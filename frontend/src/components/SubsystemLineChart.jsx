import React, { useState, useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';

const COLORS = [
  '#22c55e', '#3b82f6', '#f59e0b', '#a78bfa', '#06b6d4',
  '#f97316', '#ec4899', '#84cc16', '#14b8a6', '#e879f9',
  '#ef4444', '#fbbf24', '#60a5fa', '#34d399', '#c084fc',
];

const MAX_POINTS = 60;

const toISTString = (dateInput) => {
  const d = new Date(dateInput);
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false
  });
  const parts = formatter.formatToParts(d);
  const getPart = (type) => parts.find(p => p.type === type).value;
  return `${getPart('year')}-${getPart('month')}-${getPart('day')} ${getPart('hour')}:${getPart('minute')}:${getPart('second')}`;
};

export default function SubsystemLineChart({ subsystem, readings }) {
  const historyRef = useRef({});
  const revisionRef = useRef(0);
  const containerRef = useRef(null);

  const [plotData, setPlotData] = useState([]);
  const [revision, setRevision] = useState(0);
  const [dims, setDims] = useState({ w: 800, h: 400 });

  /* ── measure the container's real pixel size ── */
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        const { width, height } = e.contentRect;
        if (width > 10 && height > 10) setDims({ w: Math.floor(width), h: Math.floor(height) });
      }
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  /* ── reset history when subsystem tab changes ── */
  useEffect(() => {
    historyRef.current = {};
    setPlotData([]);
    revisionRef.current = 0;
    setRevision(0);
  }, [subsystem]);

  /* ── accumulate one data point per tick ── */
  useEffect(() => {
    const subReadings = Object.values(readings).filter(r => r.subsystem === subsystem);
    if (subReadings.length === 0) return;

    const timeStr = toISTString(new Date());
    let colorIdx = Object.keys(historyRef.current).length;

    subReadings.forEach(r => {
      if (!historyRef.current[r.id]) {
        historyRef.current[r.id] = {
          x: [],
          y: [],
          name: r.id,          // short label — sensor ID
          unit: r.unit,
          colorIndex: colorIdx % COLORS.length,
          lineColor: COLORS[colorIdx % COLORS.length],
        };
        colorIdx++;
      }

      const trace = historyRef.current[r.id];
      trace.x.push(timeStr);
      trace.y.push(r.value);

      if (r.status === 'critical') trace.lineColor = '#ef4444';
      else if (r.status === 'warning') trace.lineColor = '#f59e0b';
      else trace.lineColor = COLORS[trace.colorIndex];

      if (trace.x.length > MAX_POINTS) { trace.x.shift(); trace.y.shift(); }
    });

    const traces = Object.values(historyRef.current).map(t => ({
      x: [...t.x],
      y: [...t.y],
      name: t.name,
      type: 'scatter',
      mode: 'lines',
      line: { width: 1.2, color: t.lineColor },
      hovertemplate: `<b>${t.name}</b>  %{y:.2f} ${t.unit}<br>%{x|%H:%M:%S}<extra></extra>`,
    }));

    setPlotData(traces);
    revisionRef.current += 1;
    setRevision(revisionRef.current);
  }, [readings, subsystem]);

  return (
    <div className="w-full h-full flex flex-col">

      {/* header row */}
      <div className="flex justify-between items-center mb-3 shrink-0">
        <h2 className="text-lg font-bold capitalize">
          {subsystem} — Live Telemetry
        </h2>
        <span className="text-xs font-mono text-dashboard-textMuted bg-dashboard-bg px-2 py-1 rounded">
          ROLLING 60s WINDOW
        </span>
      </div>

      {/* chart fills ALL remaining space */}
      <div
        ref={containerRef}
        className="flex-1 min-h-0 w-full bg-dashboard-bg/50 rounded overflow-hidden"
      >
        {plotData.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-dashboard-textMuted text-sm">
            Waiting for live data…
          </div>
        ) : (
          <Plot
            key={subsystem}               /* remount on subsystem change */
            data={plotData}
            layout={{
              autosize: true,       /* we control size explicitly */
              width: dims.w,
              height: dims.h,
              revision: revision,
              margin: { t: 16, l: 55, r: 16, b: 44 },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#94a3b8', family: 'monospace', size: 11 },
              xaxis: {
                type: 'date',
                showgrid: true,
                gridcolor: '#1e293b',
                zeroline: false,
                tickformat: '%H:%M:%S',
                nticks: 6,
              },
              yaxis: {
                showgrid: true,
                gridcolor: '#1e293b',
                zeroline: false,
                autorange: true,
              },
              showlegend: false,           /* 100 lines → legend is noise */
              hovermode: 'closest',
            }}
            useResizeHandler={false}       /* we drive size via dims state */
            style={{ display: 'block', width: `${dims.w}px`, height: `${dims.h}px` }}
            config={{ displayModeBar: false, responsive: false }}
          />
        )}
      </div>
    </div>
  );
}
