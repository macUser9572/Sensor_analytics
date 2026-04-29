import React, { useState } from 'react';
import axios from 'axios';
import { apiUrl } from '../config';

export default function DemoControlPanel() {
  const [activeFault, setActiveFault] = useState(null);

  const faults = [
    { id: 'T003', label: 'Turbine Bearing Overheat' },
    { id: 'B012', label: 'Boiler Pressure Spike' },
    { id: 'G005', label: 'Generator Frequency Drop' }
  ];

  const triggerFault = async (sensorId) => {
    try {
      await axios.post(apiUrl(`/simulator/fault/${sensorId}`), { target_multiplier: 1.2 });
      setActiveFault(sensorId);
    } catch (err) {
      console.error('Failed to trigger fault', err);
    }
  };

  const resolveFault = async () => {
    if (!activeFault) return;
    try {
      await axios.delete(apiUrl(`/simulator/fault/${activeFault}`));
      setActiveFault(null);
    } catch (err) {
      console.error('Failed to resolve fault', err);
    }
  };

  return (
    <div className="flex items-center space-x-3 bg-dashboard-bg px-3 py-1.5 rounded border border-critical/50">
      <span className="text-xs font-bold text-critical uppercase tracking-wide">Demo Controls</span>
      
      <select 
         className="bg-dashboard-card text-xs p-1 rounded border border-dashboard-border focus:outline-none"
         onChange={(e) => {
            if(e.target.value) triggerFault(e.target.value);
            e.target.value = "";
         }}
      >
        <option value="">Trigger Fault...</option>
        {faults.map(f => (
          <option key={f.id} value={f.id}>{f.label}</option>
        ))}
      </select>

      {activeFault && (
        <button 
          onClick={resolveFault}
          className="text-xs bg-normal/20 hover:bg-normal/30 text-normal px-2 py-1 rounded transition-colors"
        >
          Resolve {activeFault}
        </button>
      )}
    </div>
  );
}
