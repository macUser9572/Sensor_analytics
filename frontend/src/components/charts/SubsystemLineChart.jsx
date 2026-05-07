import React, { useEffect, useRef, useMemo, useState } from 'react';
import Plotly from 'plotly.js/dist/plotly-cartesian';
import { useWebSockets } from '../../context/WebSocketContext';

const STATUS_COLORS = {
    live: '#00e676',
    warning: '#ffab00',
    critical: '#ff1744',
    uncertain: '#ffeb3b',
    fault: '#9e9e9e',
    missing: '#616161',
    stale: '#4a6a5a',
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

const MAX_POINTS = 60;

 export default function SubsystemLineChart({ subsystemId, subsystemLabel }) {
    const { sensorReadings } = useWebSockets();
    const containerRef = useRef(null);
    const initializedRef = useRef(false);
    const historyRef = useRef({}); // sensor_id -> [values...]
    const lastTimestampRef = useRef({}); // sensor_id -> latest plotted timestamp
    const [lastUpdate, setLastUpdate] = useState(null);

    // Filter readings for this subsystem
    const subsystemReadings = useMemo(() => {
        return Object.values(sensorReadings).filter(
            r => String(r.subsystem || '').toLowerCase() === subsystemId
        );
    }, [sensorReadings, subsystemId]);

    // Accumulate rolling history
    useEffect(() => {
        let appended = false;
        subsystemReadings.forEach(r => {
            const id = r.id || r.sensor_id;
            const ts = r.timestamp || r.last_seen || '';
            if (ts && lastTimestampRef.current[id] === ts) return;
            lastTimestampRef.current[id] = ts || `${Date.now()}:${r.value}`;
            if (!historyRef.current[id]) historyRef.current[id] = [];
            historyRef.current[id].push({ v: r.value, state: getSensorState(r), ts });
            if (historyRef.current[id].length > MAX_POINTS) {
                historyRef.current[id].shift();
            }
            appended = true;
        });
        if (appended) setLastUpdate(new Date().toLocaleTimeString());
    }, [subsystemReadings]);

    // Draw/update chart
    useEffect(() => {
        if (!containerRef.current) return;
        if (subsystemReadings.length === 0) return;

        const traces = subsystemReadings.map((r) => {
            const id = r.id || r.sensor_id;
            const hist = historyRef.current[id] || [];
            const state = getSensorState(r);
            const isFaulted = state === 'fault' || state === 'missing';
            const color = STATUS_COLORS[state] || '#9e9e9e';

            return {
                name: r.name || id,
                x: hist.map((_, i) => i),
                y: hist.map(p => p.v),
                type: 'scatter',
                mode: 'lines',
                line: {
                    color,
                    width: 1.5,
                    dash: isFaulted ? 'dash' : 'solid',
                },
                opacity: isFaulted ? 0.4 : 1,
                hovertemplate: `<b>${r.name || id}</b><br>Value: %{y}<extra></extra>`,
            };
        });

        const layout = {
            paper_bgcolor: '#000000',
            plot_bgcolor: '#111111',
            margin: { t: 20, r: 20, b: 40, l: 60 },
            xaxis: {
                showgrid: true,
                gridcolor: '#222',
                zeroline: false,
                tickfont: { color: '#555' },
            },
            yaxis: {
                showgrid: true,
                gridcolor: '#222',
                zeroline: false,
                tickfont: { color: '#9e9e9e', family: 'Share Tech Mono' },
            },
            legend: {
                orientation: 'h',
                y: -0.2,
                font: { color: '#9e9e9e', size: 10 },
            },
            hoverlabel: {
                bgcolor: '#111111',
                bordercolor: '#00e5ff',
                font: { color: '#fff', family: 'Share Tech Mono', size: 12 },
            },
        };

        const config = { displayModeBar: false, responsive: true };

        if (!initializedRef.current) {
            Plotly.newPlot(containerRef.current, traces, layout, config);
            initializedRef.current = true;
        } else {
            Plotly.react(containerRef.current, traces, layout, config);
        }
    }, [subsystemReadings]);

    return (
        <div className="w-full h-full flex flex-col">
            <div className="flex items-center justify-between px-2 pb-2 text-xs text-gray-400">
                <span className="font-bold text-gray-300 uppercase tracking-wider">{subsystemLabel} — Sensor Trends</span>
                {lastUpdate && <span>Last update: {lastUpdate}</span>}
            </div>
            <div className="flex-1">
                <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
            </div>
        </div>
    );
}
