import React, { useState } from 'react';

export default function RealDataView({ readings, onSensorClick }) {
  const categories = ['turbine', 'boiler', 'generator', 'cooling', 'transformer', 'auxiliary'];
  const [selectedCategory, setSelectedCategory] = useState(categories[0]);
  const [search, setSearch] = useState('');

  // Filter sensors based on the selected category & search string
  const sensors = Object.values(readings).filter(r => {
    if (r.subsystem !== selectedCategory) return false;
    if (search && !r.name.toLowerCase().includes(search.toLowerCase()) && !r.id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  // Sort sensors by status (critical -> warning -> normal), then ID
  sensors.sort((a, b) => {
     const valA = a.status === 'critical' ? 3 : a.status === 'warning' ? 2 : 1;
     const valB = b.status === 'critical' ? 3 : b.status === 'warning' ? 2 : 1;
     if (valA !== valB) return valB - valA;
     return a.id.localeCompare(b.id);
  });

  return (
    <div className="flex h-full w-full bg-dashboard-card border border-dashboard-border rounded-lg overflow-hidden font-mono">
      {/* Category Sidebar */}
      <div className="w-[200px] bg-dashboard-border/20 border-r border-dashboard-border flex flex-col">
        <div className="p-4 border-b border-dashboard-border text-sm font-bold uppercase tracking-wider text-dashboard-textMuted">
          Categories
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => { setSelectedCategory(cat); setSearch(''); }}
              className={`w-full text-left px-3 py-2 rounded capitalize text-sm transition-colors ${
                selectedCategory === cat 
                  ? 'bg-dashboard-border text-white border-l-2 border-green-500' 
                  : 'hover:bg-dashboard-border/50 text-dashboard-textMuted'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Sensor List Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="p-4 border-b border-dashboard-border flex items-center justify-between">
            <h2 className="text-lg font-bold capitalize text-white">{selectedCategory} Sensors</h2>
            <div className="w-[250px]">
               <input 
                 type="text" 
                 placeholder="Search sensors..." 
                 value={search}
                 onChange={(e) => setSearch(e.target.value)}
                 className="w-full bg-dashboard-bg border border-dashboard-border rounded px-3 py-1.5 text-sm outline-none focus:border-green-500 text-dashboard-textMain"
               />
            </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {sensors.length === 0 ? (
               <div className="col-span-full text-center py-10 text-dashboard-textMuted">No sensors found.</div>
            ) : sensors.map(sensor => (
              <div 
                key={sensor.id}
                onClick={() => onSensorClick(sensor.id)}
                className="bg-dashboard-bg border border-dashboard-border rounded p-3 cursor-pointer hover:bg-dashboard-border transition-colors flex flex-col justify-between"
              >
                 <div className="flex justify-between items-start mb-2">
                    <span className="font-bold text-dashboard-textMain">{sensor.id}</span>
                    <span className={`px-1.5 py-0.5 text-[10px] uppercase font-bold rounded ${
                        sensor.status === 'critical' ? 'bg-critical/20 text-critical' : 
                        sensor.status === 'warning' ? 'bg-warning/20 text-warning' : 
                        'bg-normal/20 text-normal'
                    }`}>
                      {sensor.status}
                    </span>
                 </div>
                 <div className="text-xs text-dashboard-textMuted truncate mb-3" title={sensor.name}>
                    {sensor.name}
                 </div>
                 <div className="flex justify-between items-end">
                    <span className="text-xl font-bold bg-dashboard-card px-2 py-1 rounded inline-block text-white">
                      {sensor.value.toFixed(2)}
                    </span>
                    <span className="text-dashboard-textMuted text-xs">{sensor.unit}</span>
                 </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
