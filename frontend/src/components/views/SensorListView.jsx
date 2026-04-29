import React, { useState, useMemo } from 'react';
import { useWebSockets } from '../../context/WebSocketContext';

const SUBSYSTEMS = ['turbine', 'boiler', 'generator', 'cooling', 'transformer', 'auxiliary'];
const SUBSYSTEM_LABELS = {
    turbine: 'Turbine', boiler: 'Boiler', generator: 'Generator',
    cooling: 'Cooling', transformer: 'Transformer', auxiliary: 'Auxiliary',
};

const STATUS_STYLES = {
    live: 'text-status-live bg-status-live/10 border-status-live/30',
    warning: 'text-status-warning bg-status-warning/10 border-status-warning/30',
    critical: 'text-status-critical bg-status-critical/10 border-status-critical/30',
    uncertain: 'text-status-uncertain bg-status-uncertain/10 border-status-uncertain/30',
    fault: 'text-status-fault bg-status-fault/10 border-status-fault/30',
    missing: 'text-status-fault bg-status-fault/10 border-status-fault/30',
    stale: 'text-gray-500 bg-gray-500/10 border-gray-500/30',
};

function getSensorState(reading) {
    if (!reading) return 'fault';
    const status = reading.status?.toLowerCase();
    const quality = reading.quality?.toLowerCase();
    if (status === 'missing') return 'missing';
    if (status === 'fault' || quality === 'bad') return 'fault';
    if (quality === 'uncertain') return 'uncertain';
    if (status === 'critical') return 'critical';
    if (status === 'warning') return 'warning';
    const now = Date.now();
    const lastSeen = reading.last_seen ? new Date(reading.last_seen).getTime() : 0;
    const interval = (reading.expected_interval || 10) * 1000;
    if (lastSeen && (now - lastSeen) > 2 * interval) return 'stale';
    return 'live';
}

function StatusBadge({ state }) {
    const icons = { live: '●', warning: '⚠', critical: '🔴', uncertain: '~', fault: '✕', missing: '✕', stale: '⏱' };
    return (
        <span className={`text-xs px-1.5 py-0.5 rounded border font-bold ${STATUS_STYLES[state] || ''}`}>
            {icons[state]} {state.toUpperCase()}
        </span>
    );
}

export default function SensorListView({ selectedSensorIds, onSelectionChange, onSensorClick }) {
    const { sensorReadings } = useWebSockets();
    const [search, setSearch] = useState('');
    const [collapsed, setCollapsed] = useState({});

    const grouped = useMemo(() => {
        const groups = {};
        SUBSYSTEMS.forEach(s => { groups[s] = []; });

        Object.values(sensorReadings).forEach(r => {
            const sub = String(r.subsystem || '').toLowerCase();
            if (groups[sub]) groups[sub].push(r);
        });

        return groups;
    }, [sensorReadings]);

    const filteredGrouped = useMemo(() => {
        if (!search.trim()) return grouped;
        const q = search.toLowerCase();
        const result = {};
        SUBSYSTEMS.forEach(s => {
            result[s] = grouped[s].filter(r =>
                String(r.name || '').toLowerCase().includes(q) ||
                String(r.sensor_id || r.id || '').toLowerCase().includes(q) ||
                s.includes(q)
            );
        });
        return result;
    }, [grouped, search]);

    const toggleGroup = (sub) => setCollapsed(prev => ({ ...prev, [sub]: !prev[sub] }));

    const handleCheck = (id, e) => {
        e.stopPropagation();
        const set = new Set(selectedSensorIds);
        if (set.has(id)) set.delete(id);
        else set.add(id);
        onSelectionChange(Array.from(set));
    };

    const selectAll = (sensors, e) => {
        e.stopPropagation();
        const ids = sensors.map(r => r.id || r.sensor_id);
        const set = new Set(selectedSensorIds);
        const allSelected = ids.every(id => set.has(id));
        if (allSelected) ids.forEach(id => set.delete(id));
        else ids.forEach(id => set.add(id));
        onSelectionChange(Array.from(set));
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center space-x-3 mb-3">
                <input
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder="Search sensors or subsystems..."
                    className="flex-1 bg-industrial-panel border border-industrial-border rounded px-3 py-1.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent-cyan"
                />
                {selectedSensorIds.length > 0 && (
                    <button 
                        onClick={() => onSelectionChange([])}
                        className="text-xs text-gray-400 hover:text-gray-200 px-2 py-1 border border-industrial-border rounded"
                    >
                        Clear ({selectedSensorIds.length})
                    </button>
                )}
            </div>

            <div className="flex-1 overflow-auto">
                {SUBSYSTEMS.map(sub => {
                    const sensors = filteredGrouped[sub] || [];
                    const isCollapsed = collapsed[sub];

                    return (
                        <div key={sub} className="mb-2 border border-industrial-border rounded overflow-hidden">
                            <button
                                onClick={() => toggleGroup(sub)}
                                className="w-full flex items-center justify-between px-4 py-2 bg-industrial-panel text-left hover:bg-white/5"
                            >
                                <div className="flex items-center space-x-3">
                                    <span className="font-bold text-gray-200">{SUBSYSTEM_LABELS[sub]}</span>
                                    <span className="text-xs text-gray-500">{sensors.length} sensors</span>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <button
                                        onClick={(e) => selectAll(sensors, e)}
                                        className="text-xs text-accent-cyan hover:underline"
                                    >
                                        Select all
                                    </button>
                                    <span className="text-gray-500">{isCollapsed ? '▼' : '▲'}</span>
                                </div>
                            </button>

                            {!isCollapsed && (
                                <div className="overflow-auto max-h-64">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="text-left text-xs text-gray-500 bg-black border-b border-industrial-border">
                                                <th className="w-8 p-2"></th>
                                                <th className="p-2">ID</th>
                                                <th className="p-2">Name</th>
                                                <th className="p-2 font-mono text-right">Value</th>
                                                <th className="p-2">Unit</th>
                                                <th className="p-2">Status</th>
                                                <th className="p-2">Last Seen</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {sensors.map(r => {
                                                const id = r.id || r.sensor_id;
                                                const state = getSensorState(r);
                                                const isSelected = selectedSensorIds.includes(id);
                                                const lastSeen = r.last_seen
                                                    ? new Date(r.last_seen).toLocaleTimeString()
                                                    : '—';

                                                return (
                                                    <tr 
                                                        key={id}
                                                        onClick={() => onSensorClick(id)}
                                                        className={`border-b border-industrial-border/50 cursor-pointer hover:bg-white/5 transition-colors ${isSelected ? 'bg-accent-cyan/10' : ''}`}
                                                    >
                                                        <td className="p-2 text-center" onClick={e => e.stopPropagation()}>
                                                            <input
                                                                type="checkbox"
                                                                checked={isSelected}
                                                                onChange={() => {}}
                                                                onClick={(e) => handleCheck(id, e)}
                                                                className="accent-cyan-400 cursor-pointer"
                                                            />
                                                        </td>
                                                        <td className="p-2 font-mono text-xs text-gray-400">{id}</td>
                                                        <td className="p-2 text-gray-200">{r.name || id}</td>
                                                        <td className="p-2 font-mono text-right text-accent-cyan">
                                                            {r.value != null ? Number(r.value).toFixed(2) : '—'}
                                                        </td>
                                                        <td className="p-2 text-xs text-gray-400">{r.unit || '—'}</td>
                                                        <td className="p-2"><StatusBadge state={state} /></td>
                                                        <td className="p-2 text-xs text-gray-500">{lastSeen}</td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
