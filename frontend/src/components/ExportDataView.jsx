import React, { useState } from 'react';

export default function ExportDataView() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    if (!startDate || !endDate) {
      setErrorMsg('Please select both start and end dates.');
      return;
    }
    
    if (new Date(startDate) > new Date(endDate)) {
        setErrorMsg('Start date must be before end date.');
        return;
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      const startIso = new Date(startDate).toISOString();
      const endIso = new Date(endDate).toISOString();
      const response = await fetch(`http://localhost:8000/data/export?start_date=${encodeURIComponent(startIso)}&end_date=${encodeURIComponent(endIso)}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          setErrorMsg('Timeline is not matching');
        } else {
          setErrorMsg('Failed to export data');
        }
        setLoading(false);
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `sensor_export_${startDate}_to_${endDate}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      
      setLoading(false);
    } catch (err) {
      console.error(err);
      setErrorMsg('Network error occurred during export.');
      setLoading(false);
    }
  };

  return (
    <div className="w-full h-full flex flex-col p-6 items-center justify-center bg-dashboard-bg/50 rounded overflow-hidden">
      <div className="max-w-md w-full bg-dashboard-card border border-dashboard-border rounded-lg p-8 shadow-lg">
        <h2 className="text-xl font-bold text-dashboard-textMain mb-2 uppercase tracking-wide flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2 text-normal" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export Sensor Data
        </h2>
        <p className="text-dashboard-textMuted text-sm text-center mb-8">
            Download raw telemetry data within a specific time window for backup or local analysis.
        </p>
        
        <div className="space-y-6">
          <div>
            <label className="block text-xs font-bold text-dashboard-textMuted uppercase mb-2">Start Date & Time</label>
            <input 
              type="datetime-local" 
              className="w-full bg-dashboard-bg border border-dashboard-border rounded px-4 py-3 text-dashboard-textMain focus:outline-none focus:border-normal transition-colors"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          
          <div>
            <label className="block text-xs font-bold text-dashboard-textMuted uppercase mb-2">End Date & Time</label>
            <input 
              type="datetime-local" 
              className="w-full bg-dashboard-bg border border-dashboard-border rounded px-4 py-3 text-dashboard-textMain focus:outline-none focus:border-normal transition-colors"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          <button 
            onClick={handleExport}
            disabled={loading}
            className="w-full mt-4 bg-dashboard-border hover:bg-dashboard-textMuted text-white font-bold py-3 rounded transition-colors text-base disabled:opacity-50 flex items-center justify-center"
          >
            {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Exporting...
                </>
            ) : 'Export to CSV'}
          </button>
        </div>
      </div>

      {/* Error Popup Modal */}
      {errorMsg && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 transition-opacity">
          <div className="bg-dashboard-card border-2 border-critical rounded-lg p-6 max-w-sm w-full shadow-2xl animate-[fadeIn_0.2s_ease-out]">
             <div className="flex items-center space-x-3 text-critical mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <h3 className="text-xl font-bold">Export Failed</h3>
             </div>
             <p className="text-dashboard-textMuted mb-6 whitespace-pre-wrap">{errorMsg}</p>
             <div className="flex justify-end">
                <button 
                  onClick={() => setErrorMsg(null)}
                  className="bg-dashboard-border hover:bg-dashboard-textMuted px-5 py-2 rounded text-white font-medium transition-colors"
                >
                  Dismiss
                </button>
             </div>
          </div>
        </div>
      )}
    </div>
  );
}
