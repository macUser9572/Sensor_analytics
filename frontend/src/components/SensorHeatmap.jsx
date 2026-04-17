import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

export default function SensorHeatmap({ readings, onSensorClick }) {
  const subsystems = ['turbine', 'boiler', 'generator', 'cooling', 'transformer', 'auxiliary'];
  
  const { z, text, customdata } = useMemo(() => {
     const zGrid = [];
     const textGrid = [];
     const customdataGrid = [];
     
     subsystems.forEach(sub => {
       const subReadings = Object.values(readings)
           .filter(r => r.subsystem === sub)
           .sort((a,b) => a.id.localeCompare(b.id));

       const zRow = [];
       const textRow = [];
       const cdRow = [];
       
       for(let i=0; i<120; i++) {
         const r = subReadings[i];
         if (r) {
           const ratio = Math.min((r.value / (r.max_threshold || 1)), 1.2); 
           const statusStr = r.status ? r.status.toUpperCase() : 'UNKNOWN';
           zRow.push(ratio);
           textRow.push(`<b>${r.name}</b><br>ID: ${r.id}<br>Value: ${r.value.toFixed(2)} ${r.unit}<br>Threshold: ${r.max_threshold}<br>Status: ${statusStr}`);
           cdRow.push(r.id);
         } else {
           zRow.push(null);
           textRow.push('');
           cdRow.push(null);
         }
       }
       zGrid.push(zRow);
       textGrid.push(textRow);
       customdataGrid.push(cdRow);
     });
     
     return { z: zGrid, text: textGrid, customdata: customdataGrid };
  }, [readings]);

  const colorscale = [
    [0.0, '#22c55e'], [0.79, '#22c55e'],
    [0.79, '#f59e0b'], [0.99, '#f59e0b'],
    [0.99, '#ef4444'], [1.0, '#ef4444']
  ];

  return (
    <div className="w-full h-full flex flex-col">
       <h2 className="text-lg font-bold mb-4 shrink-0">Plant Overview — All Sensors</h2>
       <div className="flex-1 min-h-0 bg-dashboard-bg/50 rounded flex flex-col justify-center items-center overflow-hidden">
          <div className="w-full" style={{ maxHeight: '250px', height: '100%' }}>
             <Plot 
               data={[
                 {
                   z: z,
                   text: text,
                   customdata: customdata,
                   type: 'heatmap',
                   colorscale: colorscale,
                   zmin: 0,
                   zmax: 1.0,
                   hoverinfo: 'text',
                   showscale: false,
                   xgap: 2,
                   ygap: 2,
                 hoverlabel: { font: { family: 'monospace' } }
              }
            ]}
            layout={{
              autosize: true,
              margin: { t: 10, l: 100, r: 10, b: 10 },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              yaxis: {
                tickvals: [0,1,2,3,4,5],
                ticktext: subsystems.map(s => s.toUpperCase()),
                tickfont: { color: '#94a3b8', size: 10, family: 'monospace' },
                autorange: 'reversed',
                fixedrange: true,
                showgrid: false,
                zeroline: false
              },
              xaxis: {
                showticklabels: false,
                showgrid: false,
                zeroline: false,
                 fixedrange: true
              }
            }}
            useResizeHandler={true}
            style={{ width: '100%', height: '100%', display: 'block' }}
            config={{ displayModeBar: false, responsive: true }}
            onClick={(e) => {
              if (e.points && e.points[0] && e.points[0].customdata) {
                 onSensorClick(e.points[0].customdata);
              }
            }}
          />
          </div>
       </div>
    </div>
  );
}
