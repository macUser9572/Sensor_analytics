import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import axios from 'axios';

export default function SensorDetailModal({ sensor, onClose }) {
  const [history, setHistory] = useState(null);
  const [stats, setStats] = useState({ min: 0, max: 0, mean: 0 });

  useEffect(() => {
    let active = true;
    const fetchHistory = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/data/sensors/${sensor.id}/history?minutes=60`);
        if (!active) return;
        
        const data = res.data;
        if(data.length > 0) {
            const x = data.map(d => d.time);
            const y = data.map(d => d.value);
            setHistory({ x, y });
            
            const min = Math.min(...y);
            const max = Math.max(...y);
            const mean = y.reduce((a,b)=>a+b, 0) / y.length;
            setStats({ min: min.toFixed(2), max: max.toFixed(2), mean: mean.toFixed(2) });
        }
      } catch(err) {
         console.error("Failed to load history", err);
      }
    };
    fetchHistory();
    return () => { active = false; };
  }, [sensor.id]);

  return (
    <div className="fixed inset-0 bg-dashboard-bg/90 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-[fadeIn_0.2s_ease-out]">
       <div className="bg-dashboard-card border border-dashboard-border shadow-2xl rounded-xl w-full max-w-5xl flex flex-col overflow-hidden">
          
          <div className="flex justify-between items-center p-5 border-b border-dashboard-border bg-dashboard-border/30">
             <div>
                <h2 className="text-2xl font-bold flex items-center space-x-3 text-dashboard-textMain">
                   <span>{sensor.name}</span>
                   <span className={`px-2 py-0.5 text-xs uppercase rounded font-bold tracking-wider ${sensor.status === 'critical' ? 'bg-critical/20 text-critical' : sensor.status === 'warning' ? 'bg-warning/20 text-warning' : 'bg-normal/20 text-normal'}`}>{sensor.status}</span>
                </h2>
                <p className="text-dashboard-textMuted text-sm font-mono mt-1">{sensor.id} • {sensor.subsystem.toUpperCase()}</p>
             </div>
             <button onClick={onClose} className="text-dashboard-textMuted hover:text-white p-2 text-xl font-bold transition-colors">✕</button>
          </div>

          <div className="p-6 flex-1 flex flex-col min-h-[500px]">
             
             <div className="flex justify-between items-center mb-6 bg-dashboard-bg border border-dashboard-border rounded p-4">
                <div>
                   <div className="text-dashboard-textMuted text-xs uppercase font-bold tracking-widest mb-1">Live Value</div>
                   <div className="text-4xl font-mono font-bold text-dashboard-textMain">
                     {sensor.value.toFixed(2)} <span className="text-xl text-dashboard-textMuted ml-1">{sensor.unit}</span>
                   </div>
                </div>
                
                {history && (
                  <div className="flex space-x-8 text-sm font-mono">
                     <div className="flex flex-col items-end"><span className="text-dashboard-textMuted text-xs uppercase font-bold tracking-wider mb-1">Min (60m)</span><span className="text-xl">{stats.min}</span></div>
                     <div className="flex flex-col items-end"><span className="text-dashboard-textMuted text-xs uppercase font-bold tracking-wider mb-1">Mean (60m)</span><span className="text-xl">{stats.mean}</span></div>
                     <div className="flex flex-col items-end"><span className="text-dashboard-textMuted text-xs uppercase font-bold tracking-wider mb-1">Max (60m)</span><span className="text-xl">{stats.max}</span></div>
                  </div>
                )}
             </div>

             <div className="flex-1 min-h-[300px] border border-dashboard-border rounded bg-dashboard-bg overflow-hidden relative">
                {history ? (
                  <Plot 
                    data={[{
                       x: history.x,
                       y: history.y,
                       type: 'scatter',
                       mode: 'lines',
                       fill: 'tozeroy',
                       fillcolor: sensor.status === 'critical' ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)',
                       line: { color: sensor.status === 'critical' ? '#ef4444' : '#22c55e', width: 2 }
                    }]}
                    layout={{
                       autosize: true,
                       margin: { t: 30, l: 50, r: 30, b: 50 },
                       paper_bgcolor: 'transparent',
                       plot_bgcolor: 'transparent',
                       font: { color: '#94a3b8', family: 'monospace' },
                       xaxis: { showgrid: true, gridcolor: '#334155', title: 'Time' },
                       yaxis: { showgrid: true, gridcolor: '#334155', title: sensor.unit }
                    }}
                    useResizeHandler={true}
                    style={{ width: '100%', height: '100%' }}
                    config={{ displayModeBar: false, responsive: true }}
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-dashboard-textMuted animate-pulse space-y-4">
                      <div className="w-8 h-8 border-4 border-dashboard-border border-t-dashboard-textMuted rounded-full animate-spin"></div>
                      <div>Querying TimescaleDB History...</div>
                  </div>
                )}
             </div>
          </div>

       </div>
    </div>
  );
}
