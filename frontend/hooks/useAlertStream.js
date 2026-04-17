import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

export function useAlertStream() {
    const [alerts, setAlerts] = useState([]);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const retryCountRef = useRef(0);
    const isComponentMounted = useRef(true);

    const fetchActiveAlerts = async () => {
        try {
            const res = await axios.get("http://localhost:8000/api/v1/alerts/active");
            setAlerts(res.data);
        } catch (err) {
            console.error("Failed to fetch initial active alerts", err);
        }
    };

    const connect = () => {
        if (!isComponentMounted.current) return;
        
        if (wsRef.current) {
            wsRef.current.close();
        }

        const ws = new WebSocket("ws://localhost:8000/ws/alerts");
        wsRef.current = ws;

        ws.onopen = () => {
            retryCountRef.current = 0;
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = null;
            }
            fetchActiveAlerts();
        };

        ws.onmessage = (event) => {
            try {
                if (event.data === "pong") return;
                
                const data = JSON.parse(event.data);
                
                if (data.event === "alert_fired" && data.alert) {
                    setAlerts(prev => {
                        const next = [...prev];
                        const idx = next.findIndex(a => a.id === data.alert.id);
                        if (idx >= 0) {
                            next[idx] = data.alert;
                        } else {
                            next.unshift(data.alert);
                        }
                        return next;
                    });
                } else if (data.event === "alert_resolved" && data.alert) {
                    const alertId = data.alert.id;
                    setAlerts(prev => prev.filter(a => a.id !== alertId));
                }
            } catch (err) {
                console.error("Failed to parse alert message", err);
            }
        };

        ws.onclose = () => {
            if (!isComponentMounted.current) return;
            
            const maxBackoff = 30000;
            let delay = Math.pow(2, retryCountRef.current) * 1000;
            if (delay > maxBackoff) delay = maxBackoff;
            
            retryCountRef.current += 1;
            reconnectTimeoutRef.current = setTimeout(connect, delay);
        };
    };

    useEffect(() => {
        isComponentMounted.current = true;
        connect();
        
        // Polling fallback to clear any discrepancies (like the mobile app)
        const pollInterval = setInterval(fetchActiveAlerts, 10000);

        return () => {
            isComponentMounted.current = false;
            clearInterval(pollInterval);
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    const acknowledgeAlert = async (alertId) => {
        try {
            const res = await axios.post(`http://localhost:8000/api/v1/alerts/${alertId}/acknowledge`);
            if (res.data.status === 'success') {
                setAlerts(prev => prev.filter(a => a.id !== alertId));
            }
        } catch (err) {
            console.error("Failed to acknowledge alert", err);
        }
    };

    return { alerts, acknowledgeAlert };
}
