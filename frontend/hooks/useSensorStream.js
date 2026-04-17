import { useState, useEffect, useRef } from 'react';

export function useSensorStream() {
    const [sensorReadings, setSensorReadings] = useState({});
    const [subsystemStatus, setSubsystemStatus] = useState({
        turbine: { normal: 0, warning: 0, critical: 0 },
        boiler: { normal: 0, warning: 0, critical: 0 },
        generator: { normal: 0, warning: 0, critical: 0 },
        cooling: { normal: 0, warning: 0, critical: 0 },
        transformer: { normal: 0, warning: 0, critical: 0 },
        auxiliary: { normal: 0, warning: 0, critical: 0 }
    });
    const [connectionStatus, setConnectionStatus] = useState("disconnected");
    
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const retryCountRef = useRef(0);
    const isComponentMounted = useRef(true);

    const connect = () => {
        if (!isComponentMounted.current) return;
        
        setConnectionStatus("connecting");
        
        if (wsRef.current) {
            wsRef.current.close();
        }

        const ws = new WebSocket("ws://localhost:8000/ws/live");
        wsRef.current = ws;

        ws.onopen = () => {
            setConnectionStatus("connected");
            retryCountRef.current = 0; // Reset retry count
            
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = null;
            }
            
            // HTTP fallback to quickly rehydrate the UI
            fetch("http://localhost:8000/data/sensors/current")
                .then(res => res.json())
                .then(data => {
                    const newReadings = {};
                    if(Array.isArray(data)) {
                        data.forEach(reading => {
                            newReadings[reading.id] = reading;
                        });
                    }
                    setSensorReadings(prev => ({ ...prev, ...newReadings }));
                })
                .catch(console.error);
        };

        ws.onmessage = (event) => {
            try {
                if (event.data === "pong") return;
                
                const data = JSON.parse(event.data);
                if (data.subsystem && data.readings) {
                    setSensorReadings(prev => {
                        const next = { ...prev };
                        data.readings.forEach(r => {
                            next[r.id] = r;
                        });
                        return next;
                    });
                    
                    setSubsystemStatus(prev => {
                        const next = { ...prev };
                        let normal = 0;
                        let warning = 0;
                        let critical = 0;
                        
                        data.readings.forEach(r => {
                            if (r.status === "normal") normal++;
                            else if (r.status === "warning") warning++;
                            else if (r.status === "critical") critical++;
                        });
                        
                        next[data.subsystem] = { normal, warning, critical };
                        return next;
                    });
                }
            } catch (err) {
                console.error("Failed to parse message", err);
            }
        };

        ws.onclose = () => {
            if (!isComponentMounted.current) return;
            
            setConnectionStatus("disconnected");
            
            // Exponential backoff reconnect
            const maxBackoff = 30000;
            // 1s, 2s, 4s, 8s -> Math.pow(2, c)*1000
            let delay = Math.pow(2, retryCountRef.current) * 1000;
            if (delay > maxBackoff) delay = maxBackoff;
            
            retryCountRef.current += 1;
            reconnectTimeoutRef.current = setTimeout(connect, delay);
        };
        
        ws.onerror = (err) => {
           // Closed event handles the retry logic.
        };
    };

    useEffect(() => {
        isComponentMounted.current = true;
        connect();
        
        // ping interval every 30 seconds
        const pingInterval = setInterval(() => {
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send("ping");
            }
        }, 30000);

        // Visibility change to protect background tabs that throttle WS
        const handleVisibilityChange = () => {
            if (document.visibilityState === "visible" && connectionStatus === "disconnected") {
                if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
                retryCountRef.current = 0;
                connect();
            }
        };
        
        document.addEventListener("visibilitychange", handleVisibilityChange);

        return () => {
            isComponentMounted.current = false;
            clearInterval(pingInterval);
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            document.removeEventListener("visibilitychange", handleVisibilityChange);
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    return { sensorReadings, subsystemStatus, connectionStatus };
}
