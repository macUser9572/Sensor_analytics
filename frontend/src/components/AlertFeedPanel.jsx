import React from 'react';
import axios from 'axios';

export default function AlertFeedPanel({ alerts }) {
  
  const handleAcknowledge = async (id) => {
      try {
          // Placeholder for Phase 6
          // await axios.post(`http://localhost:8000/api/v1/alerts/${id}/ack`);
          console.log(`Ack requested for ${id}`);
      } catch (err) {
          console.error(err);
      }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-dashboard-border flex justify-between items-center bg-dashboard-card shrink-0">
         <h2 className="font-semibold flex items-center">
            <span className="w-2 h-2 bg-critical rounded-full mr-2 animate-pulse"></span>
            Active Alerts
         </h2>
         <span className="text-xs bg-dashboard-border px-2 py-0.5 rounded">{alerts.length}</span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {alerts.length === 0 ? (
           <div className="text-center text-dashboard-textMuted text-sm mt-10">
             System Operating Normally
           </div>
        ) : (
           alerts.map((alert, idx) => (
             <div 
                key={`${alert.id}-${idx}`} 
                className="bg-dashboard-bg border border-dashboard-border rounded p-3 text-sm flex flex-col space-y-2 animate-[slideIn_0.3s_ease-out]"
             >
                <div className="flex justify-between items-start">
                   <div className="flex items-center space-x-2">
                     <span className={`px-1.5 py-0.5 text-[10px] font-bold uppercase rounded ${alert.severity === 'critical' ? 'bg-critical/20 text-critical' : 'bg-warning/20 text-warning'}`}>
                       {alert.severity}
                     </span>
                     <span className="font-bold text-dashboard-textMain">{alert.id}</span>
                   </div>
                   <span className="text-[10px] text-dashboard-textMuted">Just now</span>
                </div>
                
                <div className="text-dashboard-textMuted text-xs leading-tight">
                  <p className="text-dashboard-textMain font-medium truncate">{alert.name}</p>
                  <p className="mt-1 font-mono">Value: <span className={alert.severity === 'critical' ? 'text-critical' : 'text-warning'}>{alert.value}</span> / {alert.threshold}</p>
                </div>

                <div className="pt-2 flex justify-end">
                   <button 
                     className="text-[10px] px-2 py-1 bg-dashboard-border hover:bg-dashboard-border/80 rounded transition text-dashboard-textMain"
                     onClick={() => handleAcknowledge(alert.id)}
                   >
                     ACKNOWLEDGE
                   </button>
                </div>
             </div>
           ))
        )}
      </div>
    </div>
  );
}
