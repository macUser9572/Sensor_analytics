import React, { useState, useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';

export default function SubsystemLineChart({ subsystem, readings }) {
  const [plotData, setPlotData] = useState([]);
  const historyRef = useRef({});

  useEffect(() => {
    historyRef.current = {};
    setPlotData([]);
  }, [subsystem]);

  useEffect(() => {
    const subReadings = Object.values(readings).filter(r => r.subsystem === subsystem);
    if(subReadings.length === 0) return;

    const timeStr = new Date().toISOString();

    subReadings.forEach(r => {
       if (!historyRef.current[r.id]) {
           historyRef.current[r.id] = {
              x: [],
              y: [],
              name: r.name,
              type: 'scatter',
              mode: 'lines',
              line: { width: 1.5, color: '#22c55e' },
              hoverinfo: 'name+y'
           };
       }
       
       const trace = historyRef.current[r.id];
       trace.x.push(timeStr);
       trace.y.push(r.value);
       
       if (r.status === 'critical') trace.line.color = '#ef4444';
       else if (r.status === 'warning') trace.line.color = '#f59e0b';
       else trace.line.color = '#22c55e';

       if (trace.x.length > 60) {
           trace.x.shift();
           trace.y.shift();
       }
    });

    setPlotData(Object.values(historyRef.current).map(t => ({...t})));
  }, [readings, subsystem]);

  return (
    <div className="w-full h-full flex flex-col">
       <div className="flex justify-between items-end mb-4">
          <h2 className="text-lg font-bold capitalize">{subsystem} — Live telemetry</h2>
          <span className="text-xs font-mono text-dashboard-textMuted bg-dashboard-bg px-2 py-1 rounded">ROLLING 60s WINDOW</span>
       </div>
       <div className="flex-1 min-h-0 bg-dashboard-bg/50 rounded overflow-hidden">
          <Plot 
            data={plotData}
            layout={{
              autosize: true,
              margin: { t: 20, l: 50, r: 20, b: 40 },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: '#94a3b8', family: 'monospace' },
              xaxis: { showgrid: true, gridcolor: '#334155', zeroline: false },
              yaxis: { showgrid: true, gridcolor: '#334155', zeroline: false },
              showlegend: false,
              hovermode: 'closest'
            }}
            useResizeHandler={true}
            style={{ width: '100%', height: '100%' }}
            config={{ displayModeBar: false, responsive: true }}
          />
       </div>
    </div>
  );
}
