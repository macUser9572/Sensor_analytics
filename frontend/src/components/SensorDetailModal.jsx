import React, { useState, useEffect, useRef } from 'react';
import Plotly from 'plotly.js/dist/plotly';
import axios from 'axios';
import { apiUrl } from '../config';
import { useWebSockets } from '../context/WebSocketContext';

const toISTString = (dateInput) => {
  const d = new Date(dateInput);
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  });
  return formatter.format(d);
};

function getSensorState(sensor) {
  if (!sensor) return 'fault';
  const status = sensor.status?.toLowerCase();
  const quality = sensor.quality?.toLowerCase();
  if (status === 'missing') return 'missing';
  if (status === 'fault' || quality === 'bad') return 'fault';
  if (quality === 'uncertain') return 'uncertain';
  if (status === 'critical') return 'critical';
  if (status === 'warning') return 'warning';
  const now = Date.now();
  const lastSeen = sensor.last_seen ? new Date(sensor.last_seen).getTime() : 0;
  const interval = (sensor.expected_interval || 10) * 1000;
  if (lastSeen && (now - lastSeen) > 2 * interval) return 'stale';
  return 'live';
}

const STATE_STYLES = {
  live:      { badge: 'bg-status-live/20 text-status-live border-status-live/50',      label: '● LIVE' },
  warning:   { badge: 'bg-status-warning/20 text-status-warning border-status-warning/50',  label: '⚠ WARNING' },
  critical:  { badge: 'bg-status-critical/20 text-status-critical border-status-critical/50', label: '🔴 CRITICAL' },
  uncertain: { badge: 'bg-status-uncertain/20 text-status-uncertain border-status-uncertain/50', label: '~ UNCERTAIN' },
  fault:     { badge: 'bg-status-fault/20 text-status-fault border-status-fault/50',     label: '✕ FAULT' },
  missing:   { badge: 'bg-status-fault/20 text-status-fault border-status-fault/50',     label: '✕ MISSING' },
  stale:     { badge: 'bg-gray-500/20 text-gray-400 border-gray-500/50',                label: '⏱ STALE' },
};

const LINE_COLORS = {
  live: '#00e676', warning: '#ffab00', critical: '#ff1744',
  uncertain: '#ffeb3b', fault: '#9e9e9e', missing: '#616161', stale: '#4a6a5a',
};

function computeStats(values) {
  if (!values || values.length === 0) return { min: 0, max: 0, mean: 0, std_dev: 0 };
  const min = Math.min(...values);
  const max = Math.max(...values);
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / values.length;
  return {
    min: min.toFixed(2),
    max: max.toFixed(2),
    mean: mean.toFixed(2),
    std_dev: Math.sqrt(variance).toFixed(2),
  };
}

export default function SensorDetailModal({ sensor, onClose }) {
  const { alerts } = useWebSockets();
  const containerRef = useRef(null);
  const initializedRef = useRef(false);
  const lastValueRef = useRef(null);

  const [history, setHistory] = useState(null);
  const [stats, setStats] = useState({ min: 0, max: 0, mean: 0, std_dev: 0 });

  const state = getSensorState(sensor);
  const style = STATE_STYLES[state] || STATE_STYLES.live;
  const lineColor = LINE_COLORS[state] || '#00e676';

  // Find any active fault alert for this sensor
  const faultAlert = (alerts || []).find(a =>
    (a.sensor_id === sensor.id || a.sensor_id === sensor.sensor_id) &&
    (a.alert_type === 'sensor_fault' || a.alert_type === 'sensor_missing')
  );

  const isFaulted = state === 'fault' || state === 'missing';

  // Fetch history
  useEffect(() => {
    let active = true;
    const fetchHistory = async () => {
      try {
        const res = await axios.get(apiUrl(`/data/sensors/${sensor.id}/history?minutes=60`));
        if (!active) return;
        const data = res.data;
        if (data && data.length > 0) {
          const x = data.map(d => d.time || d.timestamp);
          const y = data.map(d => d.value);
          setHistory({ x, y });
          setStats(computeStats(y));
        }
      } catch (err) {
        console.error('Failed to load history', err);
      }
    };
    fetchHistory();
    return () => { active = false; };
  }, [sensor.id]);

  // Append live ticks to history
  useEffect(() => {
    if (history && sensor.value !== lastValueRef.current) {
      lastValueRef.current = sensor.value;
      setHistory(prev => {
        if (!prev) return prev;
        const newX = [...prev.x, sensor.timestamp || new Date().toISOString()];
        const newY = [...prev.y, sensor.value];
        if (newX.length > 3600) { newX.shift(); newY.shift(); }
        return { x: newX, y: newY };
      });
    }
  }, [sensor.value]);

  // Update stats when history changes
  useEffect(() => {
    if (history?.y?.length > 0) setStats(computeStats(history.y));
  }, [history]);

  // Draw/update Plotly chart
  useEffect(() => {
    if (!containerRef.current || !history) return;

    const trace = {
      x: history.x.slice(-300),
      y: history.y.slice(-300),
      type: 'scatter',
      mode: 'lines',
      fill: 'tozeroy',
      fillcolor: `${lineColor}15`,
      line: { color: lineColor, width: 2 },
      hovertemplate: '%{x|%H:%M:%S}<br><b>%{y:.2f}</b><extra></extra>',
    };

    const layout = {
      paper_bgcolor: '#000000',
      plot_bgcolor: '#111111',
      margin: { t: 10, r: 20, b: 50, l: 55 },
      xaxis: {
        type: 'date',
        showgrid: true,
        gridcolor: '#222',
        zeroline: false,
        tickfont: { color: '#666', family: 'Share Tech Mono', size: 10 },
        tickformat: '%H:%M:%S',
        nticks: 6,
      },
      yaxis: {
        title: { text: sensor.unit || '', font: { color: '#9e9e9e', size: 11 } },
        showgrid: true,
        gridcolor: '#222',
        zeroline: false,
        tickfont: { color: '#9e9e9e', family: 'Share Tech Mono', size: 10 },
      },
      hoverlabel: {
        bgcolor: '#111',
        bordercolor: lineColor,
        font: { color: '#fff', family: 'Share Tech Mono', size: 12 },
      },
    };

    const config = { displayModeBar: false, responsive: true };

    if (!initializedRef.current) {
      Plotly.newPlot(containerRef.current, [trace], layout, config);
      initializedRef.current = true;
    } else {
      Plotly.react(containerRef.current, [trace], layout, config);
    }
  }, [history, lineColor, sensor.unit]);

  return (
    <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-6">
      <div
        className="bg-industrial-panel border border-industrial-border shadow-2xl rounded-xl w-full max-w-4xl flex flex-col overflow-hidden"
        style={{ maxHeight: '88vh' }}
      >
        {/* Header */}
        <div className="flex justify-between items-start p-5 border-b border-industrial-border shrink-0">
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <h2 className="text-xl font-bold text-gray-100" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                {sensor.name || sensor.id}
              </h2>
              <span className={`px-2 py-0.5 text-xs border rounded font-bold ${style.badge}`}>
                {style.label}
              </span>
            </div>
            <p className="text-xs text-gray-500 font-mono">
              {sensor.id} &nbsp;·&nbsp; {String(sensor.subsystem || '').toUpperCase()}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white text-xl font-bold leading-none transition-colors p-1"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto p-5 flex flex-col space-y-4 min-h-0">
          {/* Live value + stats row */}
          <div className="grid grid-cols-4 gap-3 shrink-0">
            <div className="bg-black border border-industrial-border rounded p-3 col-span-1">
              <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">Live Value</div>
              <div className="text-3xl font-mono font-bold" style={{ color: lineColor }}>
                {sensor.value != null ? Number(sensor.value).toFixed(2) : '—'}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">{sensor.unit || ''}</div>
            </div>
            {[
              { label: 'Min (60m)', value: stats.min },
              { label: 'Mean (60m)', value: stats.mean },
              { label: 'Max (60m)', value: stats.max },
            ].map(s => (
              <div key={s.label} className="bg-black border border-industrial-border rounded p-3">
                <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">{s.label}</div>
                <div className="text-xl font-mono text-gray-200">{s.value}</div>
              </div>
            ))}
          </div>

          {/* Std dev */}
          {history && (
            <div className="flex items-center space-x-6 text-xs text-gray-500 font-mono shrink-0">
              <span>Std Dev (60m): <span className="text-gray-300">{stats.std_dev}</span></span>
              <span>Data points: <span className="text-gray-300">{history.y.length}</span></span>
              {sensor.threshold != null && (
                <span>Threshold: <span className="text-gray-300">{sensor.threshold}</span></span>
              )}
              {sensor.last_seen && (
                <span>Last seen: <span className="text-gray-300">{toISTString(sensor.last_seen)}</span></span>
              )}
            </div>
          )}

          {/* Fault alert details */}
          {isFaulted && faultAlert && (
            <div className="border border-status-critical/40 bg-red-950/30 rounded p-3 text-sm shrink-0">
              <div className="text-status-critical font-bold mb-1 text-xs uppercase tracking-wider">
                ✕ Fault Details
              </div>
              <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs font-mono text-gray-400">
                <span>Type: <span className="text-gray-200">{faultAlert.alert_type}</span></span>
                <span>Quality: <span className="text-gray-200">{faultAlert.quality || sensor.quality || '—'}</span></span>
                <span>Fired: <span className="text-gray-200">{faultAlert.fired_at ? toISTString(faultAlert.fired_at) : '—'}</span></span>
                <span>Alert ID: <span className="text-gray-200">{faultAlert.id}</span></span>
              </div>
            </div>
          )}

          {isFaulted && !faultAlert && (
            <div className="border border-status-fault/40 bg-status-fault/5 rounded p-3 text-xs text-gray-400 shrink-0">
              <span className="text-status-fault font-bold">✕ Fault state</span> — no active alert found in feed (may have been acknowledged).
              {sensor.quality && <span className="ml-2">Quality code: <span className="font-mono text-gray-300">{sensor.quality}</span></span>}
            </div>
          )}

          {/* History chart */}
          <div className="flex-1 min-h-0" style={{ minHeight: '240px' }}>
            {history ? (
              <div ref={containerRef} style={{ width: '100%', height: '100%', minHeight: '240px' }} />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-gray-600 space-y-3" style={{ minHeight: '240px' }}>
                <div className="w-6 h-6 border-2 border-industrial-border border-t-accent-cyan rounded-full animate-spin" />
                <span className="text-xs">Loading 60-min history...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
