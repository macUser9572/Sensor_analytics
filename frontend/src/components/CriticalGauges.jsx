import React from 'react';
import Plot from 'react-plotly.js';

export default function CriticalGauges({ subsystem, readings }) {
  const gauges = [
    { id: 'T041', title: 'Main Shaft RPM', max: 3200, target: 3000 },
    { id: 'G041', title: 'Frequency (Hz)', max: 55, target: 50 },
    { id: 'B001', title: 'Steam Pressure (bar)', max: 200, target: 150 }
  ];

  return (
    <div className="flex w-full justify-around items-center h-[160px]">
        {gauges.map((g, i) => {
            const r = readings[g.id] || { value: 0, status: 'normal' };
            const c = r.status === 'critical' ? '#ef4444' : r.status === 'warning' ? '#f59e0b' : '#22c55e';
            return (
              <div key={i} className="w-1/3 h-full">
                <Plot 
                  data={[{
                    type: "indicator",
                    mode: "gauge+number",
                    value: r.value,
                    title: { text: g.title, font: { size: 12, color: '#f1f5f9' } },
                    number: { font: { color: c, size: 28, family: 'monospace' } },
                    gauge: {
                      axis: { range: [null, g.max], tickwidth: 1, tickcolor: "#334155" },
                      bar: { color: c, thickness: 0.3 },
                      bgcolor: "transparent",
                      borderwidth: 2,
                      bordercolor: "#334155",
                      threshold: {
                        line: { color: "#ef4444", width: 4 },
                        thickness: 0.75,
                        value: g.target
                      }
                    }
                  }]}
                  layout={{
                    autosize: true,
                    margin: { t: 40, r: 25, l: 25, b: 15 },
                    paper_bgcolor: 'transparent',
                    font: { color: '#f1f5f9' }
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '100%' }}
                  config={{ displayModeBar: false, responsive: true }}
                />
              </div>
            )
        })}
    </div>
  );
}
