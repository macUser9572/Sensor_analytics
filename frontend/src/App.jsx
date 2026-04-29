import React, { useState, useMemo } from 'react';
import { useWebSockets } from './context/WebSocketContext';
import Layout from './components/layout/Layout';
import SensorHeatmap from './components/charts/SensorHeatmap';
import SubsystemLineChart from './components/charts/SubsystemLineChart';
import CriticalGauges from './components/charts/CriticalGauges';
import SensorDetailModal from './components/SensorDetailModal';
import SensorListView from './components/views/SensorListView';
import CompareChartView from './components/views/CompareChartView';

const SUBSYSTEMS = [
    { id: 'turbine', label: 'Turbine' },
    { id: 'boiler', label: 'Boiler' },
    { id: 'generator', label: 'Generator' },
    { id: 'cooling', label: 'Cooling' },
    { id: 'transformer', label: 'Transformer' },
    { id: 'auxiliary', label: 'Auxiliary' },
];

const SUBSYSTEM_IDS = SUBSYSTEMS.map(s => s.id);

export default function App() {
    const { sensorReadings } = useWebSockets();
    const [activeView, setActiveView] = useState('overview');
    const [selectedSensorIds, setSelectedSensorIds] = useState([]);
    const [selectedSensor, setSelectedSensor] = useState(null);
    // View before compare — to restore when clearing
    const [preCompareView, setPreCompareView] = useState('overview');

    // Compute which subsystems are represented in selected sensors
    const subsystemCount = useMemo(() => {
        const subs = new Set();
        selectedSensorIds.forEach(id => {
            const r = sensorReadings[id];
            if (r?.subsystem) subs.add(String(r.subsystem).toLowerCase());
        });
        return subs.size;
    }, [selectedSensorIds, sensorReadings]);

    const handleSensorClick = (sensorId) => {
        const reading = sensorReadings[sensorId];
        if (reading) setSelectedSensor(reading);
    };

    const handleCompareClick = () => {
        setPreCompareView(activeView);
        setActiveView('compare');
    };

    const handleClearAll = () => {
        setSelectedSensorIds([]);
        setActiveView(preCompareView || 'sensor-list');
    };

    const handleSelectionChange = (ids) => {
        setSelectedSensorIds(ids);
    };

    // Find subsystem label from view id like 'subsystem-turbine'
    const getSubsystemMeta = (view) => {
        const id = view.replace('subsystem-', '');
        return SUBSYSTEMS.find(s => s.id === id);
    };

    const isSubsystemView = activeView.startsWith('subsystem-');
    const subsystemMeta = isSubsystemView ? getSubsystemMeta(activeView) : null;

    // Show gauges on all views except overview and compare
    const showGauges = activeView !== 'overview' && activeView !== 'compare';

    return (
        <Layout
            activeView={activeView}
            setActiveView={setActiveView}
            selectedSensorIds={selectedSensorIds}
            subsystemCount={subsystemCount}
            onCompareClick={handleCompareClick}
        >
            <div className="flex flex-col" style={{ height: '100%', minHeight: 0 }}>
                {/* Critical Gauges strip — shown on all non-overview, non-compare views */}
                {showGauges && (
                    <div className="shrink-0 bg-industrial-panel border border-industrial-border rounded-lg p-3 mb-3">
                        <CriticalGauges />
                    </div>
                )}

                {/* Main content area */}
                <div
                    className="bg-industrial-panel border border-industrial-border rounded-lg p-4 overflow-hidden flex"
                    style={{ flex: 1, minHeight: 0 }}
                >
                    {activeView === 'overview' && (
                        <SensorHeatmap
                            onSensorClick={handleSensorClick}
                        />
                    )}

                    {activeView === 'sensor-list' && (
                        <SensorListView
                            selectedSensorIds={selectedSensorIds}
                            onSelectionChange={handleSelectionChange}
                            onSensorClick={handleSensorClick}
                        />
                    )}

                    {activeView === 'compare' && (
                        <CompareChartView
                            selectedSensorIds={selectedSensorIds}
                            sensorReadings={sensorReadings}
                            onClearAll={handleClearAll}
                        />
                    )}

                    {isSubsystemView && subsystemMeta && (
                        <SubsystemLineChart
                            subsystemId={subsystemMeta.id}
                            subsystemLabel={subsystemMeta.label}
                        />
                    )}
                </div>
            </div>

            {/* Sensor Detail Modal */}
            {selectedSensor && (
                <SensorDetailModal
                    sensor={selectedSensor}
                    source="heatmap"
                    onClose={() => setSelectedSensor(null)}
                />
            )}
        </Layout>
    );
}
