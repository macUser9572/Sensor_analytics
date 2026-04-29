import React, { useEffect, useRef, useState, useCallback } from 'react';
import Plotly from 'plotly.js/dist/plotly';
import axios from 'axios';
import { apiUrl } from '../../config';

const COLORS = [
    '#00e5ff', '#00e676', '#ffab00', '#ff1744', '#b388ff',
    '#ff6d00', '#40c4ff', '#69f0ae', '#ffd740', '#ff4081',
    '#64ffda', '#ff6e40', '#ccff90', '#ea80fc', '#80d8ff',
];

const TIME_OPTIONS = [
    { label: '15 min', minutes: 15 },
    { label: '1 h',   minutes: 60 },
    { label: '6 h',   minutes: 360 },
];

function getSubsystemsFromIds(ids, sensorReadings) {
    const subs = new Set();
    ids.forEach(id => {
        const r = sensorReadings?.[id];
        if (r?.subsystem) subs.add(String(r.subsystem).toLowerCase());
    });
    return subs;
}

export default function CompareChartView({ selectedSensorIds, sensorReadings, onClearAll }) {
    const containerRef = useRef(null);
    const initializedRef = useRef(false);
    const [minutes, setMinutes] = useState(60);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [traceData, setTraceData] = useState([]);

    const fetchData = useCallback(async () => {
        if (!selectedSensorIds || selectedSensorIds.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const ids = selectedSensorIds.join(',');
            const res = await axios.get(apiUrl(`/data/sensors/compare?ids=${ids}&minutes=${minutes}`));
            const data = res.data; // Expected: { sensor_id: [{time, value}, ...], ... }
            setTraceData(data);
        } catch (err) {
            console.error('CompareChartView fetch error', err);
            setError('Failed to fetch comparison data.');
        } finally {
            setLoading(false);
        }
    }, [selectedSensorIds, minutes]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Build and render chart whenever traceData or minutes changes
    useEffect(() => {
        if (!containerRef.current) return;
        if (loading) return;

        // Determine units for dual-axis
        const units = {};
        selectedSensorIds.forEach(id => {
            const r = sensorReadings?.[id];
            if (r?.unit) units[id] = r.unit;
        });
        const uniqueUnits = [...new Set(Object.values(units))];
        const dualAxis = uniqueUnits.length >= 2;
        const primaryUnit = uniqueUnits[0] || '';
        const secondaryUnit = uniqueUnits[1] || '';

        const traces = selectedSensorIds.map((id, i) => {
            const raw = traceData[id] || [];
            const sensorUnit = units[id] || '';
            const onSecondary = dualAxis && sensorUnit && sensorUnit !== primaryUnit;
            const reading = sensorReadings?.[id];
            const name = reading?.name || id;
            const currentVal = reading?.value;

            return {
                name: `${name}${currentVal != null ? ` (${Number(currentVal).toFixed(2)} ${sensorUnit})` : ''}`,
                x: raw.map(d => d.time || d.timestamp),
                y: raw.map(d => d.value),
                type: 'scatter',
                mode: 'lines',
                line: { color: COLORS[i % COLORS.length], width: 2 },
                yaxis: onSecondary ? 'y2' : 'y',
                hovertemplate: `<b>${name}</b><br>%{x|%H:%M:%S}<br>%{y:.2f} ${sensorUnit}<extra></extra>`,
            };
        });

        const layout = {
            paper_bgcolor: '#000000',
            plot_bgcolor: '#111111',
            margin: { t: 20, r: dualAxis ? 70 : 20, b: 80, l: 70 },
            xaxis: {
                type: 'date',
                showgrid: true,
                gridcolor: '#222',
                zeroline: false,
                tickfont: { color: '#9e9e9e', family: 'Share Tech Mono', size: 10 },
                tickformat: '%H:%M:%S',
            },
            yaxis: {
                title: { text: primaryUnit, font: { color: '#9e9e9e', size: 11 } },
                showgrid: true,
                gridcolor: '#222',
                zeroline: false,
                tickfont: { color: '#9e9e9e', family: 'Share Tech Mono', size: 10 },
            },
            ...(dualAxis && {
                yaxis2: {
                    title: { text: secondaryUnit, font: { color: '#9e9e9e', size: 11 } },
                    overlaying: 'y',
                    side: 'right',
                    showgrid: false,
                    zeroline: false,
                    tickfont: { color: '#9e9e9e', family: 'Share Tech Mono', size: 10 },
                },
            }),
            legend: {
                orientation: 'h',
                y: -0.25,
                x: 0,
                font: { color: '#ccc', family: 'Rajdhani', size: 12 },
                bgcolor: 'transparent',
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
    }, [traceData, loading, selectedSensorIds, sensorReadings, minutes]);

    const subsystems = getSubsystemsFromIds(selectedSensorIds, sensorReadings);
    const subCount = subsystems.size;

    return (
        <div className="w-full h-full flex flex-col">
            {/* Toolbar */}
            <div className="flex items-center justify-between mb-3 shrink-0">
                <div className="flex items-center space-x-3">
                    <span className="text-accent-cyan font-bold text-sm uppercase tracking-wider" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                        Comparing {selectedSensorIds.length} sensors
                        {subCount > 1 && (
                            <span className="ml-2 text-xs text-gray-400">· {subCount} subsystems</span>
                        )}
                    </span>
                </div>

                <div className="flex items-center space-x-2">
                    {/* Time range */}
                    <div className="flex border border-industrial-border rounded overflow-hidden text-xs">
                        {TIME_OPTIONS.map(opt => (
                            <button
                                key={opt.minutes}
                                onClick={() => setMinutes(opt.minutes)}
                                className={`px-3 py-1 transition-colors ${minutes === opt.minutes
                                    ? 'bg-accent-cyan text-black font-bold'
                                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                                }`}
                            >
                                {opt.label}
                            </button>
                        ))}
                    </div>

                    <button
                        onClick={fetchData}
                        disabled={loading}
                        className="px-3 py-1 text-xs border border-industrial-border text-gray-400 hover:text-gray-200 hover:border-accent-cyan rounded transition-colors"
                    >
                        {loading ? '...' : '↻ Refresh'}
                    </button>

                    <button
                        onClick={onClearAll}
                        className="px-3 py-1 text-xs bg-industrial-border text-gray-300 hover:text-white rounded transition-colors"
                    >
                        ✕ Clear All
                    </button>
                </div>
            </div>

            {/* Chart area */}
            <div className="flex-1 relative min-h-0">
                {loading && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center z-10 bg-black/60">
                        <div className="w-8 h-8 border-2 border-industrial-border border-t-accent-cyan rounded-full animate-spin mb-3" />
                        <span className="text-xs text-gray-400" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                            Fetching comparison data...
                        </span>
                    </div>
                )}
                {error && !loading && (
                    <div className="absolute inset-0 flex items-center justify-center text-status-critical text-sm">
                        {error}
                    </div>
                )}
                <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
            </div>
        </div>
    );
}
