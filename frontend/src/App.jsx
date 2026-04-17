import React, { useState, useEffect } from 'react';
import { useSensorStream } from '../hooks/useSensorStream';
import Layout from './components/Layout';
import SensorHeatmap from './components/SensorHeatmap';
import SubsystemLineChart from './components/SubsystemLineChart';
import CriticalGauges from './components/CriticalGauges';
import SensorDetailModal from './components/SensorDetailModal';

export default function App() {
  const { sensorReadings, subsystemStatus, connectionStatus } = useSensorStream();
  const [selectedSubsystem, setSelectedSubsystem] = useState('Overview');
  const [selectedSensor, setSelectedSensor] = useState(null);

  // Derive alert feed conceptually by scanning for active warnings/critical
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    // Generate alerts dynamically from current payloads for the feed
    // In Phase 6 this uses /ws/alerts.
    const activeAlerts = Object.values(sensorReadings)
      .filter(r => r.status === 'warning' || r.status === 'critical')
      .map(r => ({
        id: r.id,
        severity: r.status,
        name: r.name,
        subsystem: r.subsystem,
        value: r.value,
        threshold: r.max_threshold,
        time: new Date().toISOString() // naive for demo
      }))
      .slice(0, 20); // Keep max 20
      
    // Merging logic would go here if we tracked history of alerts,
    // For now we just replace to avoid complexity, since the feed checks get/post
    setAlerts(activeAlerts);
  }, [sensorReadings]);

  const handleSubsystemSelect = (sub) => {
    setSelectedSubsystem(sub);
  };

  const handleSensorClick = (sensorId) => {
    const sensor = sensorReadings[sensorId];
    if (sensor) setSelectedSensor(sensor);
  };

  return (
    <Layout 
      connectionStatus={connectionStatus}
      subsystemStatus={subsystemStatus}
      sensorReadings={sensorReadings}
      selectedSubsystem={selectedSubsystem}
      onSubsystemSelect={handleSubsystemSelect}
      alerts={alerts}
    >
      <div className="flex flex-col h-full w-full space-y-4">
        {selectedSubsystem !== 'Overview' && (
          <div className="shrink-0 bg-dashboard-card border border-dashboard-border rounded-lg p-4">
             <CriticalGauges 
               subsystem={selectedSubsystem} 
               readings={sensorReadings} 
             />
          </div>
        )}
        
        <div className="flex-1 bg-dashboard-card border border-dashboard-border rounded-lg p-4 overflow-hidden relative">
          {selectedSubsystem === 'Overview' ? (
            <SensorHeatmap 
               readings={sensorReadings} 
               onSensorClick={handleSensorClick} 
            />
          ) : (
            <SubsystemLineChart 
               subsystem={selectedSubsystem} 
               readings={sensorReadings} 
            />
          )}
        </div>
      </div>

      {selectedSensor && (
        <SensorDetailModal 
          sensor={selectedSensor} 
          onClose={() => setSelectedSensor(null)} 
        />
      )}
    </Layout>
  );
}
