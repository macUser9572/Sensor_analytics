import { useEffect, useRef, useState } from 'react';
import { wsUrl } from '../src/config';

const SUBSYSTEMS = ['turbine', 'boiler', 'generator', 'cooling', 'transformer', 'auxiliary'];
const STATUS_KEYS = ['normal', 'warning', 'critical', 'fault', 'missing'];

const emptySubsystemStatus = () =>
    Object.fromEntries(
        SUBSYSTEMS.map((subsystem) => [
            subsystem,
            { normal: 0, warning: 0, critical: 0, fault: 0, missing: 0 }
        ])
    );

const sensorId = (reading) => reading.id || reading.sensor_id;

const normalizeReading = (reading) => {
    const id = sensorId(reading);
    return { ...reading, id, sensor_id: id };
};

const statusKey = (reading) => {
    if (reading.status === 'missing') return 'missing';
    if (reading.status === 'fault' || reading.quality === 'bad') return 'fault';
    if (reading.status === 'critical') return 'critical';
    if (reading.status === 'warning' || reading.quality === 'uncertain') return 'warning';
    return 'normal';
};

const buildSubsystemStatus = (readingsById) => {
    const next = emptySubsystemStatus();
    Object.values(readingsById).forEach((reading) => {
        const subsystem = String(reading.subsystem || '').toLowerCase();
        if (!next[subsystem]) return;
        const key = statusKey(reading);
        if (STATUS_KEYS.includes(key)) {
            next[subsystem][key] += 1;
        }
    });
    return next;
};

const latestFromHistory = (history) => {
    const latest = {};
    Object.entries(history || {}).forEach(([id, readings]) => {
        if (!Array.isArray(readings) || readings.length === 0) return;
        latest[id] = normalizeReading(readings[readings.length - 1]);
    });
    return latest;
};

export function useSensorStream() {
    const [sensorReadings, setSensorReadings] = useState({});
    const [subsystemStatus, setSubsystemStatus] = useState(emptySubsystemStatus);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');

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

    const applyReadings = (readings) => {
        setSensorReadings((prev) => {
            const next = { ...prev };
            readings.forEach((reading) => {
                const normalized = normalizeReading(reading);
                if (normalized.id) {
                    next[normalized.id] = normalized;
                }
            });
            setSubsystemStatus(buildSubsystemStatus(next));
            return next;
        });
    };

    const connect = () => {
        if (!isMountedRef.current) return;

        setConnectionStatus('connecting');
        if (wsRef.current) {
            wsRef.current.close();
        }

        const ws = new WebSocket(wsUrl('/ws/live'));
        wsRef.current = ws;

        ws.onopen = () => {
            setConnectionStatus('connected');
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
                if (message.type === 'history') {
                    const latest = latestFromHistory(message.data);
                    setSensorReadings(latest);
                    setSubsystemStatus(buildSubsystemStatus(latest));
                    return;
                }

                if (message.type === 'update' && Array.isArray(message.readings)) {
                    applyReadings(message.readings);
                }
            } catch (err) {
                console.error('Failed to parse sensor stream message', err);
            }
        };

        ws.onclose = () => {
            if (!isMountedRef.current) return;
            setConnectionStatus('disconnected');
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

    return { sensorReadings, subsystemStatus, connectionStatus };
}
