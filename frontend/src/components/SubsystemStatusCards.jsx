import React from 'react';

export default function SubsystemStatusCards({ subsystem, stats }) {
    if (!stats) return null;

    let bgColor = 'bg-dashboard-bg';
    let borderColor = 'border-dashboard-border';

    if (stats.critical > 0) {
        bgColor = 'bg-critical/10';
        borderColor = 'border-critical/30';
    } else if (stats.warning > 0) {
        bgColor = 'bg-warning/10';
        borderColor = 'border-warning/30';
    } else if (stats.normal > 0) {
        bgColor = 'bg-normal/10';
        borderColor = 'border-normal/30';
    }

    const total = stats.normal + stats.warning + stats.critical;

    return (
        <div className={`mt-2 p-2 rounded text-xs border ${bgColor} ${borderColor} shadow-inner`}>
            <div className="flex justify-between items-center text-dashboard-textMuted mb-2">
                <span>Total Sensors</span>
                <span className="font-mono font-bold text-dashboard-textMain">{total}</span>
            </div>
            <div className="grid grid-cols-3 gap-1 text-center font-mono font-bold">
                <div className="bg-normal/20 text-normal rounded py-1">{stats.normal}</div>
                <div className="bg-warning/20 text-warning rounded py-1">{stats.warning}</div>
                <div className="bg-critical/20 text-critical rounded py-1">{stats.critical}</div>
            </div>
        </div>
    );
}
