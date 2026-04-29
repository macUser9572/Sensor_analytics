import React from 'react';
import { useWebSockets } from '../../context/WebSocketContext';
import Header from './Header';
import Sidebar from './Sidebar';
import AlertFeedPanel from '../alerts/AlertFeedPanel';

function ConnectionStatusBanner() {
    const { connectionStatus } = useWebSockets();

    if (connectionStatus === 'connected') return null;

    return (
        <div className="bg-status-warning text-black font-bold text-center py-1 text-sm animate-pulse z-50">
            {connectionStatus === 'connecting' ? 'Reconnecting to live data...' : 'Disconnected from live data. Retrying...'}
        </div>
    );
}

export default function Layout({ 
    children, 
    activeView, 
    setActiveView, 
    selectedSensorIds, 
    subsystemCount,
    onCompareClick 
}) {
    return (
        <div className="flex flex-col h-screen overflow-hidden bg-industrial-bg text-gray-200">
            <ConnectionStatusBanner />
            <Header 
                selectedSensorIds={selectedSensorIds}
                subsystemCount={subsystemCount}
                onCompareClick={onCompareClick} 
            />
            
            <div className="flex flex-1 overflow-hidden">
                <Sidebar activeView={activeView} setActiveView={setActiveView} />
                
                <main className="flex-1 overflow-auto relative p-4 flex flex-col">
                    {children}
                </main>

                <AlertFeedPanel />
            </div>
        </div>
    );
}
