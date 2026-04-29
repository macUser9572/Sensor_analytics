import React from 'react';
import { useWebSockets } from '../../context/WebSocketContext';
import { apiUrl } from '../../config';
import axios from 'axios';

const ALERT_META = {
    warning_threshold: { icon: '⚠', label: 'Warning', colorClass: 'text-status-warning border-status-warning/40 bg-status-warning/5' },
    critical_threshold: { icon: '🔴', label: 'Critical', colorClass: 'text-status-critical border-status-critical/40 bg-status-critical/5' },
    sensor_fault: { icon: '✕', label: 'Sensor Fault', colorClass: 'text-status-fault border-status-fault/40 bg-status-fault/5 animate-pulse-border' },
    sensor_uncertain: { icon: '~', label: 'Uncertain', colorClass: 'text-status-uncertain border-status-uncertain/40 bg-status-uncertain/5' },
    sensor_missing: { icon: '⏱', label: 'Missing', colorClass: 'text-status-fault border-status-fault/40 bg-red-950/40 animate-pulse-border' },
    sensor_recovered: { icon: '✓', label: 'Recovered', colorClass: 'text-status-live border-status-live/40 bg-status-live/5' },
};

const isFaultType = (type) => type === 'sensor_fault' || type === 'sensor_missing';

function timeAgo(dateStr) {
    if (!dateStr) return '—';
    const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
}

export default function AlertFeedPanel() {
    const { alerts, acknowledgeAlert } = useWebSockets();
    const displayAlerts = (alerts || []).slice(0, 30);
    const faultCount = displayAlerts.filter(a => isFaultType(a.alert_type || a.type)).length;

    return (
        <div className="w-[280px] shrink-0 bg-industrial-panel border-l border-industrial-border flex flex-col overflow-hidden select-none">
            {/* Header */}
            <div className="px-4 py-3 border-b border-industrial-border bg-black flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    {faultCount > 0 && (
                        <span className="w-2 h-2 rounded-full bg-status-critical animate-pulse" />
                    )}
                    <span className="font-bold text-sm tracking-wider text-gray-200 uppercase" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                        Alert Feed
                    </span>
                </div>
                <div className="flex items-center space-x-2">
                    {faultCount > 0 && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-status-critical/20 text-status-critical border border-status-critical/30 font-bold">
                            {faultCount} FAULT
                        </span>
                    )}
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-industrial-border text-gray-400">
                        {displayAlerts.length}
                    </span>
                </div>
            </div>

            {/* Feed */}
            <div className="flex-1 overflow-y-auto">
                {displayAlerts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-600 space-y-3 py-12">
                        <span className="text-3xl">✓</span>
                        <span className="text-xs text-center leading-relaxed">
                            All systems<br />operating normally
                        </span>
                    </div>
                ) : (
                    <div className="p-2 flex flex-col space-y-1.5">
                        {displayAlerts.map((alert, idx) => {
                            const alertType = alert.alert_type || alert.type || 'warning_threshold';
                            const meta = ALERT_META[alertType] || ALERT_META.warning_threshold;
                            const isFault = isFaultType(alertType);
                            const sensorName = alert.sensor_name || alert.sensor_id || 'Unknown';
                            const value = alert.value ?? alert.current_value ?? null;
                            const threshold = alert.threshold ?? null;
                            const firedAt = alert.fired_at || alert.timestamp;

                            return (
                                <div
                                    key={`${alert.id || idx}-${idx}`}
                                    className={`rounded border p-2.5 text-xs flex flex-col space-y-1.5 transition-all ${meta.colorClass} ${isFault ? 'border-l-2' : ''}`}
                                    style={isFault ? { borderLeftColor: '#ff1744' } : {}}
                                >
                                    {/* Top row */}
                                    <div className="flex items-start justify-between gap-1">
                                        <div className="flex items-center space-x-1.5 min-w-0">
                                            <span className="text-sm shrink-0">{meta.icon}</span>
                                            <span className="font-bold truncate text-gray-200" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                                                {sensorName}
                                            </span>
                                        </div>
                                        <span className="text-[10px] text-gray-500 shrink-0 whitespace-nowrap">
                                            {timeAgo(firedAt)}
                                        </span>
                                    </div>

                                    {/* Type label */}
                                    <div className="text-[10px] font-bold uppercase tracking-wider opacity-70">
                                        {meta.label}
                                    </div>

                                    {/* Value/threshold */}
                                    {value !== null && (
                                        <div className="font-mono text-[10px] text-gray-400">
                                            val: <span className="text-gray-200">{typeof value === 'number' ? value.toFixed(2) : value}</span>
                                            {threshold != null && (
                                                <span className="ml-1 opacity-60">/ thr: {typeof threshold === 'number' ? threshold.toFixed(2) : threshold}</span>
                                            )}
                                        </div>
                                    )}

                                    {/* Fault quality */}
                                    {isFault && alert.quality && (
                                        <div className="text-[10px] text-gray-500 font-mono">
                                            quality: {alert.quality}
                                        </div>
                                    )}

                                    {/* Acknowledge */}
                                    {alertType !== 'sensor_recovered' && (
                                        <div className="pt-0.5">
                                            <button
                                                onClick={() => acknowledgeAlert && acknowledgeAlert(alert.id)}
                                                className="text-[10px] px-2 py-0.5 bg-industrial-border hover:bg-industrial-border/60 rounded text-gray-300 transition-colors w-full text-center"
                                            >
                                                ACK
                                            </button>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
