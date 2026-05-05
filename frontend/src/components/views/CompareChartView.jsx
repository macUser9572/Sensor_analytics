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

function buildLayout(dualAxis, primaryUnit, secondaryUnit) {
    return {
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
}

export default function CompareChartView({ selectedSensorIds, sensorReadings, onClearAll }) {
    const containerRef  = useRef(null);
    const initializedRef = useRef(false);
    // last value we appended per sensor — prevents duplicate points
    const lastValuesRef  = useRef({});
    // live points accumulated since last full fetch: { id: { x: string[], y: number[] } }
    const livePointsRef  = useRef({});

    const [minutes,   setMinutes]   = useState(60);
    const [loading,   setLoading]   = useState(false);
    const [error,     setError]     = useState(null);
    const [traceData, setTraceData] = useState({});

    // Build full trace array from historical DB data merged with accumulated live points
    const buildTraces = useCallback((data, livePts, readings, ids, mins) => {
        const units = {};
        ids.forEach(id => {
            const r = readings?.[id];
            if (r?.unit) units[id] = r.unit;
        });
        const uniqueUnits = [...new Set(Object.values(units))];
        const dualAxis      = uniqueUnits.length >= 2;
        const primaryUnit   = uniqueUnits[0] || '';
        const secondaryUnit = uniqueUnits[1] || '';

        const cutoff = Date.now() - mins * 60 * 1000;

        const traces = ids.map((id, i) => {
            const historical = (data[id] || []).filter(d =>
                new Date(d.time || d.timestamp).getTime() >= cutoff
            );
            const live = livePts[id] || { x: [], y: [] };

            const x = [...historical.map(d => d.time || d.timestamp), ...live.x];
            const y = [...historical.map(d => d.value),               ...live.y];

            const sensorUnit = units[id] || '';
            const onSecondary = dualAxis && sensorUnit && sensorUnit !== primaryUnit;
            const reading     = readings?.[id];
            const name        = reading?.name || id;
            const currentVal  = reading?.value;

            return {
                name: `${name}${currentVal != null ? ` (${Number(currentVal).toFixed(2)} ${sensorUnit})` : ''}`,
                x,
                y,
                type: 'scatter',
                mode: 'lines+markers',
                marker: { size: 3 },
                line: { color: COLORS[i % COLORS.length], width: 1.5 },
                yaxis: onSecondary ? 'y2' : 'y',
                hovertemplate: `<b>${name}</b><br>%{x|%H:%M:%S}<br>%{y:.2f} ${sensorUnit}<extra></extra>`,
            };
        });

        return { traces, dualAxis, primaryUnit, secondaryUnit };
    }, []);

    // ── Fetch historical data ────────────────────────────────────────────────
    const fetchData = useCallback(async () => {
        if (!selectedSensorIds || selectedSensorIds.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const ids = selectedSensorIds.join(',');
            const res = await axios.get(apiUrl(`/data/sensors/compare?ids=${ids}&minutes=${minutes}`));
            // Reset live buffers on every fresh fetch so we don't double-count
            livePointsRef.current  = {};
            lastValuesRef.current  = {};
            initializedRef.current = false;
            setTraceData(res.data);
        } catch (err) {
            console.error('CompareChartView fetch error', err);
            setError('Failed to fetch comparison data.');
        } finally {
            setLoading(false);
        }
    }, [selectedSensorIds, minutes]);

    useEffect(() => { fetchData(); }, [fetchData]);

    // ── Full chart redraw whenever historical data changes (fetch / refetch) ──
    useEffect(() => {
        if (!containerRef.current || loading) return;

        const { traces, dualAxis, primaryUnit, secondaryUnit } = buildTraces(
            traceData, livePointsRef.current, sensorReadings, selectedSensorIds, minutes
        );
        const layout = buildLayout(dualAxis, primaryUnit, secondaryUnit);
        const config = { displayModeBar: false, responsive: true };

        if (!initializedRef.current) {
            Plotly.newPlot(containerRef.current, traces, layout, config);
            initializedRef.current = true;
        } else {
            Plotly.react(containerRef.current, traces, layout, config);
        }
    }, [traceData, loading, selectedSensorIds, minutes]);

    // ── Stream live ticks via Plotly.extendTraces (no full re-render) ────────
    useEffect(() => {
        if (!containerRef.current || !initializedRef.current) return;
        if (!sensorReadings || selectedSensorIds.length === 0) return;

        const cutoff   = Date.now() - minutes * 60 * 1000;
        // maxPoints caps how many points Plotly keeps per trace (rolling window)
        const maxPoints = Math.ceil(minutes * 60);

        const traceIndices = [];
        const xUpdates     = [];
        const yUpdates     = [];

        selectedSensorIds.forEach((id, i) => {
            const reading = sensorReadings[id];
            if (!reading || reading.value == null) return;
            if (reading.value === lastValuesRef.current[id]) return;  // no change

            lastValuesRef.current[id] = reading.value;
            const ts = reading.timestamp || new Date().toISOString();

            // Accumulate in livePointsRef for use in the next full redraw
            if (!livePointsRef.current[id]) livePointsRef.current[id] = { x: [], y: [] };
            const buf = livePointsRef.current[id];
            buf.x.push(ts);
            buf.y.push(reading.value);
            // Trim buffer to window
            while (buf.x.length > 0 && new Date(buf.x[0]).getTime() < cutoff) {
                buf.x.shift();
                buf.y.shift();
            }

            traceIndices.push(i);
            xUpdates.push([ts]);
            yUpdates.push([reading.value]);
        });

        if (traceIndices.length === 0) return;

        try {
            Plotly.extendTraces(
                containerRef.current,
                { x: xUpdates, y: yUpdates },
                traceIndices,
                maxPoints,
            );
        } catch (_) {
            // chart may not be ready yet on the very first tick; safe to ignore
        }
    }, [sensorReadings]);

    const subsystems = getSubsystemsFromIds(selectedSensorIds, sensorReadings);
    const subCount   = subsystems.size;

    return (
        <div className="w-full h-full flex flex-col">
            {/* Toolbar */}
            <div className="flex items-center justify-between mb-3 shrink-0">
                <div className="flex items-center space-x-3">
                    <span className="text-accent-cyan font-bold text-sm uppercase tracking-wider"
                          style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                        Comparing {selectedSensorIds.length} sensors
                        {subCount > 1 && (
                            <span className="ml-2 text-xs text-gray-400">· {subCount} subsystems</span>
                        )}
                    </span>
                </div>

                <div className="flex items-center space-x-2">
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
