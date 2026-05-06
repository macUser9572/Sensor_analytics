import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { apiUrl, wsUrl } from '../src/config';

const sortByNewest = (alerts) =>
    [...alerts].sort((a, b) => new Date(b.fired_at || 0) - new Date(a.fired_at || 0));

export function useAlertStream() {
    const [activeAlerts, setActiveAlerts] = useState([]);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const retryCountRef = useRef(0);
    const isMountedRef = useRef(true);
    const pingIntervalRef = useRef(null);

    const scheduleReconnect = () => {
        const delay = Math.min(30000, Math.pow(2, retryCountRef.current) * 1000);
        retryCountRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(connect, delay);
    };

    const connect = () => {
        if (!isMountedRef.current) return;

        if (wsRef.current) {
            wsRef.current.close();
        }

        const ws = new WebSocket(wsUrl('/ws/alerts'));
        wsRef.current = ws;

        ws.onopen = () => {
            retryCountRef.current = 0;
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = null;
            }
        };

        ws.onmessage = (event) => {
            if (event.data === 'pong' || event.data === 'ping') return;

            try {
                const message = JSON.parse(event.data);
                if (message.type === 'active_alerts' && Array.isArray(message.data)) {
                    setActiveAlerts(sortByNewest(message.data));
                    return;
                }

                if (message.event === 'alert_fired' && message.alert) {
                    if (message.alert.alert_type === 'sensor_recovered') {
                        setActiveAlerts((prev) =>
                            prev.filter((alert) => alert.sensor_id !== message.alert.sensor_id)
                        );
                        return;
                    }

                    setActiveAlerts((prev) => {
                        const withoutDuplicate = prev.filter((alert) => alert.id !== message.alert.id);
                        return sortByNewest([message.alert, ...withoutDuplicate]);
                    });
                } else if (message.event === 'alert_resolved' && message.alert) {
                    setActiveAlerts((prev) => prev.filter((alert) => alert.id !== message.alert.id));
                }
            } catch (err) {
                console.error('Failed to parse alert stream message', err);
            }
        };

        ws.onclose = () => {
            if (!isMountedRef.current) return;
            scheduleReconnect();
        };

        ws.onerror = () => {
            ws.close();
        };
    };

    useEffect(() => {
        isMountedRef.current = true;
        connect();

        pingIntervalRef.current = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send('ping');
            }
        }, 30000);

        return () => {
            isMountedRef.current = false;
            if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    const acknowledgeAlert = async (alertId) => {
        try {
            const res = await axios.post(apiUrl(`/api/v1/alerts/${alertId}/acknowledge`));
            if (res.data.status === 'success') {
                setActiveAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
            }
        } catch (err) {
            console.error('Failed to acknowledge alert', err);
        }
    };

    return { activeAlerts, alerts: activeAlerts, acknowledgeAlert };
}
