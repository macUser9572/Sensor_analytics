import React, { createContext, useContext } from 'react';
import { useSensorStream } from '../../hooks/useSensorStream';
import { useAlertStream } from '../../hooks/useAlertStream';

const WebSocketContext = createContext(null);

export function WebSocketProvider({ children }) {
    const { sensorReadings, subsystemStatus, connectionStatus } = useSensorStream();
    const { alerts, activeAlerts, acknowledgeAlert } = useAlertStream();

    return (
        <WebSocketContext.Provider value={{
            sensorReadings,
            subsystemStatus,
            connectionStatus,
            alerts: alerts || activeAlerts, // fallback since hook returns both names
            acknowledgeAlert
        }}>
            {children}
        </WebSocketContext.Provider>
    );
}

export function useWebSockets() {
    return useContext(WebSocketContext);
}
