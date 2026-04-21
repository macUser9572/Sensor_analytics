import React from 'react';
import DemoControlPanel from './DemoControlPanel';
import AlertFeedPanel from './AlertFeedPanel';
import SubsystemStatusCards from './SubsystemStatusCards';

export default function Layout({ 
  children, 
  connectionStatus, 
  subsystemStatus, 
  sensorReadings,
  selectedSubsystem,
  onSubsystemSelect,
  alerts,
  onAcknowledge
}) {


  const [time, setTime] = React.useState(new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' }));
  React.useEffect(() => {
    const timer = setInterval(() => {
       setTime(new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const getSubsystemIndicator = (sub) => {
    if (sub === 'Overview') return null;
    const stats = subsystemStatus[sub] || { normal: 0, warning: 0, critical: 0 };
    if (stats.critical > 0) return 'bg-critical';
    if (stats.warning > 0) return 'bg-warning';
    return 'bg-normal';
  };

  const totalSensors = Object.keys(sensorReadings).length;
  let totalCrit = 0, totalWarn = 0, totalNorm = 0;
  Object.values(subsystemStatus).forEach(s => {
    totalCrit += s.critical;
    totalWarn += s.warning;
    totalNorm += s.normal;
  });

  return (
    <div className="h-full w-full flex flex-col pt-[64px] pl-[220px] pr-[300px]">
      
      {/* Top Header Bar */}
      <header className="fixed top-0 left-0 w-full h-[64px] bg-dashboard-card border-b border-dashboard-border flex items-center justify-between px-6 z-50">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 bg-dashboard-border rounded flex items-center justify-center font-bold text-lg">B</div>
          <h1 className="text-xl font-semibold">BHEL Haridwar — Unit 5 — 500MW Thermal</h1>
        </div>
        
        <div className="flex items-center space-x-6">
          <DemoControlPanel />
          
          <div className="flex items-center space-x-2 text-sm font-mono">
            <span>{time}</span>
          </div>

          <div className="flex items-center space-x-4 border-l border-dashboard-border pl-4">
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${connectionStatus === 'connected' ? 'bg-normal' : 'bg-critical animate-pulse'}`}></span>
              <span className="text-sm capitalize">{connectionStatus}</span>
            </div>
            
            <div className="flex space-x-2 text-xs font-bold font-mono">
              <span className="bg-normal/20 text-normal px-2 py-1 rounded">{totalNorm}</span>
              <span className="bg-warning/20 text-warning px-2 py-1 rounded">{totalWarn}</span>
              <span className="bg-critical/20 text-critical px-2 py-1 rounded">{totalCrit}</span>
              <span className="bg-dashboard-border text-dashboard-textMain px-2 py-1 rounded">{totalSensors} TOTAL</span>
            </div>
          </div>
        </div>
      </header>

      {connectionStatus === 'disconnected' && (
        <div className="fixed top-[64px] left-0 w-full bg-warning/90 text-dashboard-bg text-center py-2 z-40 font-semibold shadow-md">
           Reconnecting to live data... 
        </div>
      )}

      {/* Left Sidebar Layout */}
      <aside className="fixed top-[64px] left-0 w-[220px] h-[calc(100vh-64px)] bg-dashboard-card/50 border-r border-dashboard-border flex flex-col p-4">
         <nav className="flex-1 space-y-1 overflow-y-auto pr-1">
            <div className="text-[10px] font-bold text-dashboard-textMuted uppercase pt-1 pb-1 tracking-wider">Dashboard Views</div>
            {['Overview', 'real data', 'Export Data'].map(view => (
              <button 
                key={view}
                className={`w-full flex items-center justify-between px-3 py-2 rounded transition-colors ${selectedSubsystem === view ? 'bg-dashboard-border text-white' : 'hover:bg-dashboard-border/50 text-dashboard-textMuted'}`}
                onClick={() => onSubsystemSelect(view)}
              >
                <span className="capitalize font-medium text-sm">{view === 'real data' ? 'Real Data View' : view}</span>
              </button>
            ))}

            <div className="text-[10px] font-bold text-dashboard-textMuted uppercase mt-5 pb-1 tracking-wider">Subsystems</div>
            {['turbine', 'boiler', 'generator', 'cooling', 'transformer', 'auxiliary'].map(sub => (
              <div key={sub}>
                <button 
                  className={`w-full flex items-center justify-between px-3 py-2 rounded transition-colors ${selectedSubsystem === sub ? 'bg-dashboard-border text-white' : 'hover:bg-dashboard-border/50 text-dashboard-textMuted'}`}
                  onClick={() => onSubsystemSelect(sub)}
                >
                  <span className="capitalize font-medium text-sm">{sub}</span>
                  <span className={`w-2 h-2 rounded-full ${getSubsystemIndicator(sub)}`}></span>
                </button>
                {selectedSubsystem === sub && (
                   <SubsystemStatusCards subsystem={sub} stats={subsystemStatus[sub]} />
                )}
              </div>
            ))}
         </nav>
      </aside>

      {/* Main Flexible Content Area */}
      <main className="p-6" style={{ height: 'calc(100vh - 64px)', overflow: 'hidden', boxSizing: 'border-box', display: 'flex', flexDirection: 'column' }}>
          {children}
      </main>

      {/* Right Alert Feed Layout */}
      <aside className="fixed top-[64px] right-0 w-[300px] h-[calc(100vh-64px)] bg-dashboard-card/50 border-l border-dashboard-border">
         <AlertFeedPanel alerts={alerts} onAcknowledge={onAcknowledge} />
      </aside>

    </div>
  );
}
