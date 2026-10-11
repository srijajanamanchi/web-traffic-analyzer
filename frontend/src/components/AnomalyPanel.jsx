import React from 'react';
import { AlertTriangle, ShieldAlert, TrendingUp, AlertCircle } from 'lucide-react';

export default function AnomalyPanel({ anomalies = [] }) {
  const getIcon = (type) => {
    switch (type) {
      case 'traffic_spike':
        return <TrendingUp className="w-4 h-4 text-amber-400" />;
      case 'error_surge':
        return <AlertTriangle className="w-4 h-4 text-rose-400" />;
      case 'suspicious_ip':
        return <ShieldAlert className="w-4 h-4 text-purple-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-indigo-400" />;
    }
  };

  const getSeverityBadge = (sev) => {
    if (sev === 'critical') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-500/20 text-rose-400 border border-rose-500/40">
          Critical
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/20 text-amber-400 border border-amber-500/40">
        Warning
      </span>
    );
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <h2 className="text-base font-semibold text-white">Automated Anomaly Detections</h2>
        </div>
        <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full border border-slate-700">
          Rolling Z-Score Engine
        </span>
      </div>

      <p className="text-xs text-slate-400 mb-4">
        Real-time statistical detection of traffic bursts, error spikes, and malicious scanners.
      </p>

      <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
        {anomalies.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-xs bg-slate-950/40 rounded-lg border border-slate-800/60">
            ✓ System nominal. No active anomalies or threshold deviations detected.
          </div>
        ) : (
          anomalies.map((alert, idx) => (
            <div
              key={alert.id || idx}
              className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg flex items-start space-x-3 hover:border-slate-700 transition"
            >
              <div className="mt-0.5 p-1.5 rounded bg-slate-900 border border-slate-800">
                {getIcon(alert.anomaly_type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-white uppercase tracking-wider">
                    {alert.anomaly_type?.replace('_', ' ')}
                  </span>
                  <div className="flex items-center space-x-2">
                    {alert.z_score ? (
                      <span className="text-[10px] text-slate-400 font-mono">
                        z={alert.z_score}
                      </span>
                    ) : null}
                    {getSeverityBadge(alert.severity)}
                  </div>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{alert.description}</p>
                <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                  {alert.ip && <span className="font-mono text-purple-300">Target IP: {alert.ip}</span>}
                  <span>
                    {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : 'Just now'}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
