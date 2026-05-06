import React, { useEffect, useRef, useMemo } from 'react';
import Plotly from 'plotly.js/dist/plotly';
import { useWebSockets } from '../../context/WebSocketContext';

const SUBSYSTEMS = ['turbine', 'boiler', 'generator', 'cooling', 'transformer', 'auxiliary'];
const SUBSYSTEM_LABELS = ['Turbine', 'Boiler', 'Generator', 'Cooling', 'Transformer', 'Auxiliary'];

function getSensorState(reading) {
    if (!reading) return 'fault';
    const status = reading.status?.toLowerCase();
    const quality = reading.quality?.toLowerCase();
    if (status === 'missing') return 'missing';
    if (status === 'fault' || quality === 'bad') return 'fault';
    if (quality === 'uncertain') return 'uncertain';
    if (status === 'critical') return 'critical';
    if (status === 'warning') return 'warning';
    // stale check
    const now = Date.now();
    const lastSeen = reading.last_seen ? new Date(reading.last_seen).getTime() : 0;
    const interval = (reading.expected_interval || 10) * 1000; // ms
    if (lastSeen && (now - lastSeen) > 2 * interval) return 'stale';
    return 'live';
}

function getPctOfThreshold(reading) {
    if (!reading || reading.value == null) return 0;

    const status = reading.status?.toLowerCase();
    const max = Number(reading.max_threshold ?? reading.threshold);
    const baseline = Number(reading.baseline_value ?? 0);
    const value = Number(reading.value);

    if (!Number.isFinite(max) || max === baseline) return 0;

    const pct = Math.round(((value - baseline) / (max - baseline)) * 100);
    if (status === 'critical') return Math.max(100, pct);
    if (status === 'warning') return Math.max(80, pct);
    return Math.min(79, Math.max(0, pct));
}

export default function SensorHeatmap({ onSensorClick }) {
    const { sensorReadings } = useWebSockets();
    const containerRef = useRef(null);
    const initializedRef = useRef(false);

    const { zData, textData, hoverData, sensorIds, numCols } = useMemo(() => {
        // Group sensors by subsystem
        const bySub = {};
        SUBSYSTEMS.forEach(s => { bySub[s] = []; });

        Object.values(sensorReadings).forEach(r => {
            const sub = String(r.subsystem || '').toLowerCase();
            if (bySub[sub]) bySub[sub].push(r);
        });

        const maxCols = Math.max(...SUBSYSTEMS.map(s => bySub[s].length), 1);

        const zData = [];
        const textData = [];
        const hoverData = [];
        const sensorIds = [];

        SUBSYSTEMS.forEach((sub) => {
            const sensors = bySub[sub];
            const zRow = [];
            const textRow = [];
            const hoverRow = [];
            const idRow = [];

            for (let i = 0; i < maxCols; i++) {
                const reading = sensors[i];
                if (!reading) {
                    zRow.push(null);
                    textRow.push('');
                    hoverRow.push('');
                    idRow.push(null);
                    continue;
                }

                const state = getSensorState(reading);
                const pct = getPctOfThreshold(reading);
                zRow.push(pct);

                let label = '';
                if (state === 'fault' || state === 'missing') label = '✕';
                else if (state === 'uncertain') label = '~';
                else if (state === 'stale') label = '⏱';
                textRow.push(label);

                const lastSeen = reading.last_seen 
                    ? new Date(reading.last_seen).toLocaleTimeString() 
                    : 'unknown';
                hoverRow.push(
                    `<b>${reading.name || reading.sensor_id}</b><br>` +
                    `Value: ${reading.value} ${reading.unit || ''}<br>` +
                    `Status: ${state.toUpperCase()}<br>` +
                    `Threshold: ${pct}%<br>` +
                    `Last seen: ${lastSeen}`
                );
                idRow.push(reading.id || reading.sensor_id);
            }

            zData.push(zRow);
            textData.push(textRow);
            hoverData.push(hoverRow);
            sensorIds.push(idRow);
        });

        return { zData, textData, hoverData, sensorIds, numCols: maxCols };
    }, [sensorReadings]);

    useEffect(() => {
        if (!containerRef.current) return;

        const trace = {
            type: 'heatmap',
            z: zData,
            text: textData,
            hovertext: hoverData,
            hovertemplate: '%{hovertext}<extra></extra>',
            x: Array.from({ length: numCols }, (_, i) => i),
            y: SUBSYSTEM_LABELS,
            colorscale: [
                [0, '#1b5e20'],
                [0.79, '#1b5e20'],
                [0.80, '#e65100'],
                [0.99, '#e65100'],
                [1.0, '#b71c1c'],
            ],
            zmin: 0,
            zmax: 150,
            showscale: false,
            texttemplate: '%{text}',
            textfont: { color: '#ffffff', size: 11 },
            xgap: 1,
            ygap: 2,
        };

        const layout = {
            paper_bgcolor: '#000000',
            plot_bgcolor: '#111111',
            margin: { t: 10, r: 10, b: 40, l: 100 },
            xaxis: {
                showgrid: false,
                showticklabels: false,
                zeroline: false,
            },
            yaxis: {
                showgrid: false,
                tickfont: { color: '#9e9e9e', family: 'Rajdhani', size: 13 },
                automargin: true,
            },
            hoverlabel: {
                bgcolor: '#111111',
                bordercolor: '#00e5ff',
                font: { color: '#ffffff', family: 'Share Tech Mono', size: 12 },
            },
        };

        const config = {
            displayModeBar: false,
            responsive: true,
        };

        if (!initializedRef.current) {
            Plotly.newPlot(containerRef.current, [trace], layout, config).then(() => {
                initializedRef.current = true;
                if (containerRef.current) {
                    containerRef.current.on('plotly_click', (data) => {
                        const pt = data.points[0];
                        const rowIdx = SUBSYSTEM_LABELS.indexOf(pt.y);
                        if (rowIdx === -1) return;
                        const colIdx = pt.x;
                        const sensorId = sensorIds[rowIdx]?.[colIdx];
                        if (sensorId) onSensorClick(sensorId);
                    });
                }
            });
        } else {
            Plotly.react(containerRef.current, [trace], layout, config);
        }
    }, [zData, textData, hoverData, sensorIds, numCols, onSensorClick]);

    return (
        <div className="w-full h-full">
            <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
        </div>
    );
}
