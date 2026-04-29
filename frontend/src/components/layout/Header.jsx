import React, { useState, useEffect } from 'react';
import { useWebSockets } from '../../context/WebSocketContext';
import DemoControlPanel from '../demo/DemoControlPanel';

export default function Header({ selectedSensorIds, subsystemCount, onCompareClick }) {
    const { connectionStatus, subsystemStatus } = useWebSockets();
    const [time, setTime] = useState(
        new Date().toLocaleTimeString('en-GB', { hour12: false })
    );

    useEffect(() => {
        const timer = setInterval(() =>
            setTime(new Date().toLocaleTimeString('en-GB', { hour12: false })), 1000
        );
        return () => clearInterval(timer);
    }, []);

    const aggregateStatus = {
        normal: 0, warning: 0, critical: 0, fault: 0, missing: 0
    };
    
    Object.values(subsystemStatus).forEach(sub => {
        aggregateStatus.normal += sub.normal || 0;
        aggregateStatus.warning += sub.warning || 0;
        aggregateStatus.critical += sub.critical || 0;
        aggregateStatus.fault += sub.fault || 0;
        aggregateStatus.missing += sub.missing || 0;
    });

    const totalFaults = aggregateStatus.fault + aggregateStatus.missing;

    return (
        <header className="h-14 bg-industrial-panel border-b border-industrial-border flex items-center justify-between px-4 text-sm select-none">
            {/* Left */}
            <div className="flex items-center space-x-3 text-accent-cyan font-semibold tracking-wider">
                <div className="w-6 h-6 bg-accent-cyan text-black flex items-center justify-center font-bold rounded-sm">
                    B
                </div>
                <span>BHEL Haridwar — Unit 5 — 500MW Thermal</span>
            </div>

            {/* Center */}
            <div className="font-mono text-xl tracking-widest text-gray-300">
                {time}
            </div>

            {/* Right */}
            <div className="flex items-center space-x-4">
                <DemoControlPanel />

                <div className="flex space-x-2">
                    <span className="px-2 py-0.5 bg-status-live/20 text-status-live rounded border border-status-live/50">
                        {aggregateStatus.normal} Normal
                    </span>
                    <span className="px-2 py-0.5 bg-status-warning/20 text-status-warning rounded border border-status-warning/50">
                        {aggregateStatus.warning} Warn
                    </span>
                    <span className="px-2 py-0.5 bg-status-critical/20 text-status-critical rounded border border-status-critical/50">
                        {aggregateStatus.critical} Crit
                    </span>
                    <span className="px-2 py-0.5 bg-status-fault/20 text-status-fault rounded border border-status-fault/50">
                        {totalFaults} Fault
                    </span>
                </div>

                <div className="flex items-center space-x-2 border-l border-industrial-border pl-4">
                    <span className={`w-3 h-3 rounded-full ${
                        connectionStatus === 'connected' ? 'bg-status-live' : 
                        connectionStatus === 'connecting' ? 'bg-status-warning animate-pulse' : 'bg-status-critical'
                    }`} title={`WS: ${connectionStatus}`}></span>
                </div>

                {selectedSensorIds && selectedSensorIds.length >= 2 && (
                    <button 
                        onClick={onCompareClick}
                        className="ml-2 px-3 py-1 bg-accent-cyan hover:bg-accent-hover text-black font-bold rounded transition-colors text-sm whitespace-nowrap"
                    >
                        COMPARE ({selectedSensorIds.length}){subsystemCount > 1 ? ` · ${subsystemCount} subsystems` : ''}
                    </button>
                )}
            </div>
        </header>
    );
}
