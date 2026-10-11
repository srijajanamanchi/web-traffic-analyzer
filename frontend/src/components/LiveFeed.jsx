import { Activity } from 'lucide-react';

export default function LiveFeed({ events = [] }) {
  const getStatusBadge = (code) => {
    if (code >= 500) {
      return <span className="text-rose-400 font-bold bg-rose-500/10 px-1.5 py-0.5 rounded text-[11px]">{code}</span>;
    }
    if (code >= 400) {
      return <span className="text-amber-400 font-bold bg-amber-500/10 px-1.5 py-0.5 rounded text-[11px]">{code}</span>;
    }
    if (code >= 300) {
      return <span className="text-sky-400 font-bold bg-sky-500/10 px-1.5 py-0.5 rounded text-[11px]">{code}</span>;
    }
    return <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded text-[11px]">{code}</span>;
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-semibold text-white">Live Activity Stream</h2>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
          <span className="text-xs text-slate-400">Streaming</span>
        </div>
      </div>

      <div className="overflow-x-auto max-h-[300px] overflow-y-auto pr-1">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 pb-2">
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2 font-medium">Type</th>
              <th className="pb-2 font-medium">Endpoint</th>
              <th className="pb-2 font-medium">IP</th>
              <th className="pb-2 font-medium">Device</th>
              <th className="pb-2 font-medium text-right">Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {events.length === 0 ? (
              <tr>
                <td colSpan="6" className="py-8 text-center text-slate-500">
                  Waiting for incoming telemetry packets...
                </td>
              </tr>
            ) : (
              events.slice(0, 15).map((ev, i) => (
                <tr key={ev.id || i} className="hover:bg-slate-800/30 transition font-mono">
                  <td className="py-2">{getStatusBadge(ev.status_code || 200)}</td>
                  <td className="py-2 text-slate-400 font-sans uppercase text-[10px] tracking-wider">
                    {ev.event_type}
                  </td>
                  <td className="py-2 text-indigo-300 font-medium truncate max-w-[150px]">
                    {ev.path}
                  </td>
                  <td className="py-2 text-slate-400 text-[11px]">{ev.ip || '127.0.0.1'}</td>
                  <td className="py-2 text-slate-300 font-sans text-[11px]">{ev.device || 'Desktop'}</td>
                  <td className="py-2 text-right text-slate-400 text-[11px]">
                    {ev.response_time_ms > 0 ? `${ev.response_time_ms}ms` : '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
