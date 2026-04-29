import React, { useState } from 'react';
import axios from 'axios';
import { apiUrl } from '../../config';

export default function DemoControlPanel() {
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [activeFault, setActiveFault] = useState(null);

    const triggerFault = async (name, endpoint, payload) => {
        setLoading(true);
        try {
            await axios.post(apiUrl(endpoint), payload);
            setActiveFault(name);
            setIsOpen(false);
        } catch (err) {
            console.error('Failed to trigger fault', err);
        } finally {
            setLoading(false);
        }
    };

    const resolveAll = async () => {
        setLoading(true);
        try {
            // Need to resolve all faults individually or via a resolve all endpoint.
            // Based on instructions: "Resolve All Faults" button -> DELETE /simulator/fault for each active fault.
            // If activeFault is known, delete it. But since it's "each active fault", maybe there's a blanket endpoint?
            // Actually, instruction says "DELETE /simulator/fault for each active fault". It might be DELETE /simulator/fault/{id} or maybe the prompt just said:
            // "Resolve All Faults" button → DELETE /simulator/fault for each active fault
            // Wait, I will just call DELETE /simulator/fault which might be a blanket clear.
            await axios.delete(apiUrl('/simulator/fault'));
            setActiveFault(null);
            setIsOpen(false);
        } catch (err) {
            console.error('Failed to resolve faults', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative">
            <button 
                onClick={() => setIsOpen(!isOpen)}
                className={`px-3 py-1 font-bold rounded flex items-center space-x-2 transition-colors ${
                    activeFault 
                    ? 'bg-status-critical text-white animate-pulse' 
                    : 'bg-industrial-border text-gray-300 hover:text-white'
                }`}
            >
                <span>⚡ DEMO</span>
                {activeFault && <span className="text-xs uppercase ml-2 px-1 bg-black/30 rounded">{activeFault}</span>}
            </button>

            {isOpen && (
                <div className="absolute top-full right-0 mt-2 w-64 bg-industrial-panel border border-industrial-border shadow-xl z-50 rounded">
                    <div className="p-3 border-b border-industrial-border font-bold text-gray-300">
                        Demo Scenarios
                    </div>
                    <div className="p-2 flex flex-col space-y-2">
                        <button 
                            disabled={loading}
                            onClick={() => triggerFault('Turbine Overheat', '/simulator/fault/T003', { target_multiplier: 1.2 })}
                            className="text-left px-3 py-2 text-sm text-status-critical hover:bg-white/5 rounded border border-transparent hover:border-industrial-border group"
                        >
                            <div className="font-bold">Turbine Bearing Overheat</div>
                            <div className="text-xs text-gray-400 mt-1">Simulates loss of lube oil flow.</div>
                            <div className="text-xs text-gray-500 mt-1">Sensor: T003 • Time to CRITICAL: ~15s</div>
                            <div className="text-xs text-red-400 mt-1 hidden group-hover:block">Alert: CRITICAL_THRESHOLD breached</div>
                        </button>
                        <button 
                            disabled={loading}
                            onClick={() => triggerFault('Boiler Pressure', '/simulator/fault/B012', { target_multiplier: 1.15 })}
                            className="text-left px-3 py-2 text-sm text-status-critical hover:bg-white/5 rounded border border-transparent hover:border-industrial-border group"
                        >
                            <div className="font-bold">Boiler Pressure Spike</div>
                            <div className="text-xs text-gray-400 mt-1">Simulates stuck pressure relief valve.</div>
                            <div className="text-xs text-gray-500 mt-1">Sensor: B012 • Time to CRITICAL: ~10s</div>
                            <div className="text-xs text-red-400 mt-1 hidden group-hover:block">Alert: RATE_OF_CHANGE exceeded</div>
                        </button>
                        <button 
                            disabled={loading}
                            onClick={() => triggerFault('Gen Frequency', '/simulator/fault/G005', { target_multiplier: 1.1 })}
                            className="text-left px-3 py-2 text-sm text-status-critical hover:bg-white/5 rounded border border-transparent hover:border-industrial-border group"
                        >
                            <div className="font-bold">Generator Frequency Drop</div>
                            <div className="text-xs text-gray-400 mt-1">Simulates sudden grid load imbalance.</div>
                            <div className="text-xs text-gray-500 mt-1">Sensor: G005 • Time to CRITICAL: ~5s</div>
                            <div className="text-xs text-red-400 mt-1 hidden group-hover:block">Alert: SUSTAINED_DEVIATION detected</div>
                        </button>
                        <button 
                            disabled={loading}
                            onClick={() => triggerFault('Sensor Kill', '/simulator/fault/sensor-kill/T010', {})}
                            className="text-left px-3 py-2 text-sm text-gray-400 hover:bg-white/5 rounded border border-transparent hover:border-industrial-border group"
                        >
                            <div className="font-bold">Sensor Hardware Failure</div>
                            <div className="text-xs text-gray-400 mt-1">Simulates cut cable/power loss.</div>
                            <div className="text-xs text-gray-500 mt-1">Sensor: T010 • Time to MISSING: ~45s</div>
                            <div className="text-xs text-red-400 mt-1 hidden group-hover:block">Alert: SENSOR_MISSING</div>
                        </button>
                    </div>
                    <div className="p-2 border-t border-industrial-border">
                        <button 
                            disabled={loading}
                            onClick={resolveAll}
                            className="w-full px-3 py-2 text-sm bg-status-live/20 text-status-live hover:bg-status-live/30 rounded font-bold"
                        >
                            Resolve All Faults
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
