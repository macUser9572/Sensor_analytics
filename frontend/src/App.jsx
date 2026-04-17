import React, { useState, useEffect } from 'react';
import { useSensorStream } from '../hooks/useSensorStream';
import { useAlertStream } from '../hooks/useAlertStream';
import Layout from './components/Layout';
import SensorHeatmap from './components/SensorHeatmap';
import SubsystemLineChart from './components/SubsystemLineChart';
import RealDataView from './components/RealDataView';
import CriticalGauges from './components/CriticalGauges';
import SensorDetailModal from './components/SensorDetailModal';

export default function App() {
  const { sensorReadings, subsystemStatus, connectionStatus } = useSensorStream();
  const { alerts, acknowledgeAlert } = useAlertStream();
  const [selectedSubsystem, setSelectedSubsystem] = useState('Overview');
  const [selectedSensor, setSelectedSensor] = useState(null);

  const handleSubsystemSelect = (sub) => {
    setSelectedSubsystem(sub);
  };

  const handleSensorClick = (sensorId, source = 'default') => {
    setSelectedSensor({ id: sensorId, source });
  };

  return (
    <Layout 
      connectionStatus={connectionStatus}
      subsystemStatus={subsystemStatus}
      sensorReadings={sensorReadings}
      selectedSubsystem={selectedSubsystem}
      onSubsystemSelect={handleSubsystemSelect}
      alerts={alerts}
      onAcknowledge={acknowledgeAlert}
    >
      <div className="flex flex-col" style={{ height: '100%', minHeight: 0 }}>
        {selectedSubsystem !== 'Overview' && selectedSubsystem !== 'real data' && (
          <div className="shrink-0 bg-dashboard-card border border-dashboard-border rounded-lg p-4 mb-4">
             <CriticalGauges 
               subsystem={selectedSubsystem} 
               readings={sensorReadings} 
             />
          </div>
        )}
        
        <div className="bg-dashboard-card border border-dashboard-border rounded-lg p-4 overflow-hidden" style={{ flex: 1, minHeight: 0 }}>
          {selectedSubsystem === 'Overview' ? (
            <SensorHeatmap 
               readings={sensorReadings} 
               onSensorClick={(id) => handleSensorClick(id, 'heatmap')} 
            />
          ) : selectedSubsystem === 'real data' ? (
             <RealDataView 
               readings={sensorReadings} 
               onSensorClick={(id) => handleSensorClick(id, 'realdata')} 
             />
          ) : (
            <SubsystemLineChart 
               subsystem={selectedSubsystem} 
               readings={sensorReadings} 
            />
          )}
        </div>
      </div>

      {selectedSensor && sensorReadings[selectedSensor.id] && (
        <SensorDetailModal 
          sensor={sensorReadings[selectedSensor.id]} 
          source={selectedSensor.source}
          onClose={() => setSelectedSensor(null)} 
        />
      )}
    </Layout>
  );
}
