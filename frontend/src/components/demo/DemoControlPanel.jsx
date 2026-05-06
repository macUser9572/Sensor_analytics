import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { apiUrl } from '../../config';

const SCENARIOS = [
    {
        name: 'Temperature Warning',
        sensorId: 'T003',
        detail: 'Ramp bearing temperature to the warning band.',
        endpoint: '/simulator/fault/T003',
        payload: { target_multiplier: 0.95 },
    },
    {
        name: 'Temperature Critical',
        sensorId: 'T003',
        detail: 'Ramp bearing temperature through warning into critical.',
        endpoint: '/simulator/fault/T003',
        payload: { target_multiplier: 1.2 },
    },
    {
        name: 'Boiler Pressure Critical',
        sensorId: 'B012',
        detail: 'Ramp drum pressure past its critical threshold.',
        endpoint: '/simulator/fault/B012',
        payload: { target_multiplier: 1.15 },
    },
    {
        name: 'Sensor Fault',
        sensorId: 'T010',
        detail: 'Stop publishing this sensor immediately.',
        endpoint: '/simulator/fault/sensor-kill/T010',
        payload: {},
    },
];

export default function DemoControlPanel() {
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [activeFaults, setActiveFaults] = useState([]);

    const refreshFaults = async () => {
        try {
            const res = await axios.get(apiUrl('/simulator/faults'));
            setActiveFaults(Array.isArray(res.data) ? res.data : []);
        } catch (err) {
            console.error('Failed to load demo faults', err);
        }
    };

    useEffect(() => {
        refreshFaults();
    }, []);

    const triggerScenario = async (scenario) => {
        setLoading(true);
        try {
            await axios.post(apiUrl(scenario.endpoint), scenario.payload);
            await refreshFaults();
            setIsOpen(false);
        } catch (err) {
            console.error('Failed to trigger demo scenario', err);
        } finally {
            setLoading(false);
        }
    };

    const resolveFaults = async () => {
        setLoading(true);
        try {
            await axios.delete(apiUrl('/simulator/fault'));
            setActiveFaults([]);
            setIsOpen(false);
        } catch (err) {
            console.error('Failed to resolve demo faults', err);
        } finally {
            setLoading(false);
        }
    };

    const activeCount = activeFaults.length;

    return (
        <div className="relative">
            <button
                type="button"
                onClick={() => setIsOpen((open) => !open)}
                className={`px-3 py-1 font-bold rounded flex items-center space-x-2 transition-colors ${
                    activeCount > 0
                        ? 'bg-status-critical text-white animate-pulse'
                        : 'bg-industrial-border text-gray-300 hover:text-white'
                }`}
            >
                <span>DEMO</span>
                {activeCount > 0 && (
                    <span className="text-xs uppercase ml-1 px-1 bg-black/30 rounded">
                        {activeCount} active
                    </span>
                )}
            </button>

            {isOpen && (
                <div className="absolute top-full right-0 mt-2 w-72 bg-industrial-panel border border-industrial-border shadow-xl z-50 rounded">
                    <div className="p-3 border-b border-industrial-border font-bold text-gray-300">
                        Demo Scenarios
                    </div>

                    <div className="p-2 flex flex-col space-y-2">
                        {SCENARIOS.map((scenario) => (
                            <button
                                key={`${scenario.name}-${scenario.sensorId}`}
                                type="button"
                                disabled={loading}
                                onClick={() => triggerScenario(scenario)}
                                className="text-left px-3 py-2 text-sm text-gray-300 hover:bg-white/5 rounded border border-transparent hover:border-industrial-border disabled:opacity-60"
                            >
                                <div className="font-bold text-status-critical">{scenario.name}</div>
                                <div className="text-xs text-gray-400 mt-1">{scenario.detail}</div>
                                <div className="text-xs text-gray-500 mt-1">Sensor: {scenario.sensorId}</div>
                            </button>
                        ))}
                    </div>

                    <div className="p-2 border-t border-industrial-border">
                        <button
                            type="button"
                            disabled={loading || activeCount === 0}
                            onClick={resolveFaults}
                            className="w-full px-3 py-2 text-sm bg-status-live/20 text-status-live hover:bg-status-live/30 rounded font-bold disabled:opacity-50 disabled:hover:bg-status-live/20"
                        >
                            Resolve Demo Faults
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
