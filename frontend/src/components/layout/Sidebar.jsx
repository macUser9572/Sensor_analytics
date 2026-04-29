import React from 'react';
import { useWebSockets } from '../../context/WebSocketContext';

const SUBSYSTEMS = [
    { id: 'turbine', label: 'Turbine' },
    { id: 'boiler', label: 'Boiler' },
    { id: 'generator', label: 'Generator' },
    { id: 'cooling', label: 'Cooling' },
    { id: 'transformer', label: 'Transformer' },
    { id: 'auxiliary', label: 'Auxiliary' },
];

export default function Sidebar({ activeView, setActiveView }) {
    const { subsystemStatus } = useWebSockets();

    const getWorstStateColor = (subsystemId) => {
        const status = subsystemStatus[subsystemId];
        if (!status) return 'bg-status-fault'; // missing/unknown
        
        if (status.fault > 0 || status.missing > 0) return 'bg-status-fault';
        if (status.critical > 0) return 'bg-status-critical';
        if (status.warning > 0) return 'bg-status-warning';
        return 'bg-status-live';
    };

    return (
        <aside className="w-[220px] bg-industrial-panel border-r border-industrial-border flex flex-col shrink-0 select-none">
            <nav className="flex-1 py-4 flex flex-col space-y-1">
                <div className="px-4 mb-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Main Views
                </div>
                
                <button 
                    onClick={() => setActiveView('overview')}
                    className={`px-6 py-2 text-left font-medium transition-colors ${
                        activeView === 'overview' 
                        ? 'bg-white/10 text-white border-l-2 border-accent-cyan' 
                        : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border-l-2 border-transparent'
                    }`}
                >
                    Overview Heatmap
                </button>
                
                <button 
                    onClick={() => setActiveView('sensor-list')}
                    className={`px-6 py-2 text-left font-medium transition-colors ${
                        activeView === 'sensor-list' 
                        ? 'bg-white/10 text-white border-l-2 border-accent-cyan' 
                        : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border-l-2 border-transparent'
                    }`}
                >
                    Sensor List
                </button>

                <div className="px-4 mt-6 mb-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Subsystems
                </div>

                {SUBSYSTEMS.map(sub => (
                    <button 
                        key={sub.id}
                        onClick={() => setActiveView(`subsystem-${sub.id}`)}
                        className={`px-6 py-2 flex items-center justify-between font-medium transition-colors ${
                            activeView === `subsystem-${sub.id}` 
                            ? 'bg-white/10 text-white border-l-2 border-accent-cyan' 
                            : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border-l-2 border-transparent'
                        }`}
                    >
                        <span>{sub.label}</span>
                        <span className={`w-2 h-2 rounded-full ${getWorstStateColor(sub.id)}`}></span>
                    </button>
                ))}
            </nav>
        </aside>
    );
}
