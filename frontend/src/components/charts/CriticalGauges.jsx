import React, { useEffect, useRef, useState } from 'react';
import { useWebSockets } from '../../context/WebSocketContext';

const GAUGES = [
    {
        id: 'turbine_rpm',
        label: 'Main Shaft RPM',
        subsystem: 'turbine',
        unit: 'RPM',
        min: 0,
        max: 3200,
        target: 3000,
        thresholds: { warn: 2700, crit: 3100 },
        fallback: 0,
        // Which sensor to look for by name keywords
        keywords: ['rpm', 'shaft', 'rotor'],
    },
    {
        id: 'generator_freq',
        label: 'Frequency',
        subsystem: 'generator',
        unit: 'Hz',
        min: 48,
        max: 52,
        target: 50,
        thresholds: { warn: 49.5, crit: 51.5 },
        fallback: 50,
        keywords: ['freq', 'hertz'],
    },
    {
        id: 'boiler_pressure',
        label: 'Main Steam Pressure',
        subsystem: 'boiler',
        unit: 'bar',
        min: 0,
        max: 200,
        target: 150,
        thresholds: { warn: 160, crit: 180 },
        fallback: 0,
        keywords: ['pressure', 'steam'],
    },
];

function findGaugeValue(sensorReadings, gauge) {
    const readings = Object.values(sensorReadings).filter(r => 
        String(r.subsystem || '').toLowerCase() === gauge.subsystem
    );
    for (const reading of readings) {
        const name = String(reading.name || reading.sensor_id || '').toLowerCase();
        if (gauge.keywords.some(kw => name.includes(kw))) {
            return reading.value ?? gauge.fallback;
        }
    }
    // fallback: first reading of subsystem
    if (readings.length > 0 && readings[0].value != null) return readings[0].value;
    return gauge.fallback;
}

function buildGaugeTrace(gauge, value) {
    const pct = (value - gauge.min) / (gauge.max - gauge.min);
    const warnPct = (gauge.thresholds.warn - gauge.min) / (gauge.max - gauge.min);
    const critPct = (gauge.thresholds.crit - gauge.min) / (gauge.max - gauge.min);

    const barColor = value >= gauge.thresholds.crit ? '#ff1744'
        : value >= gauge.thresholds.warn ? '#ffab00'
        : '#00e676';

    return {
        type: 'indicator',
        mode: 'gauge+number',
        value,
        number: {
            font: { color: barColor, family: 'Share Tech Mono', size: 22 },
            suffix: gauge.unit,
        },
        gauge: {
            axis: {
                range: [gauge.min, gauge.max],
                tickfont: { color: '#555', size: 9 },
                nticks: 5,
            },
            bar: { color: barColor, thickness: 0.6 },
            bgcolor: '#111111',
            bordercolor: '#333',
            borderwidth: 1,
            steps: [
                { range: [gauge.min, gauge.thresholds.warn], color: '#0a2a12' },
                { range: [gauge.thresholds.warn, gauge.thresholds.crit], color: '#2a1a00' },
                { range: [gauge.thresholds.crit, gauge.max], color: '#2a0009' },
            ],
            threshold: {
                line: { color: '#00e5ff', width: 2 },
                thickness: 0.75,
                value: gauge.target,
            },
        },
        domain: { x: [0, 1], y: [0, 1] },
        title: {
            text: gauge.label,
            font: { color: '#9e9e9e', family: 'Rajdhani', size: 13 },
        },
    };
}

export default function CriticalGauges() {
    const { sensorReadings } = useWebSockets();
    const [plotly, setPlotly] = useState(null);
    const refs = [useRef(null), useRef(null), useRef(null)];
    const initialized = [useRef(false), useRef(false), useRef(false)];

    const layout = {
        paper_bgcolor: '#000000',
        plot_bgcolor: '#000000',
        margin: { t: 40, r: 10, b: 5, l: 10 },
        font: { color: '#ccc' },
    };

    const config = { displayModeBar: false, responsive: true };

    useEffect(() => {
        let mounted = true;
        import('plotly.js/dist/plotly').then((module) => {
            if (mounted) setPlotly(module.default || module);
        });
        return () => {
            mounted = false;
        };
    }, []);

    useEffect(() => {
        if (!plotly) return;

        GAUGES.forEach((gauge, i) => {
            const el = refs[i].current;
            if (!el) return;
            const value = findGaugeValue(sensorReadings, gauge);
            const trace = buildGaugeTrace(gauge, value);

            if (!initialized[i].current) {
                plotly.newPlot(el, [trace], layout, config);
                initialized[i].current = true;
            } else {
                plotly.react(el, [trace], layout, config);
            }
        });
    }, [sensorReadings, plotly]);

    return (
        <div className="flex space-x-2 w-full" style={{ height: '180px' }}>
            {GAUGES.map((gauge, i) => (
                <div key={gauge.id} className="flex-1 bg-industrial-panel border border-industrial-border rounded overflow-hidden">
                    <div ref={refs[i]} style={{ width: '100%', height: '100%' }} />
                </div>
            ))}
        </div>
    );
}
