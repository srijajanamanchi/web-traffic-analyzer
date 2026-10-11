
export default function TopTable({ pages = [], referrers = [] }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {/* Top Pages */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur">
        <h2 className="text-base font-semibold text-white mb-1">Top Endpoints / Pages</h2>
        <p className="text-xs text-slate-400 mb-4">Most requested paths and average latencies</p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 pb-2">
                <th className="pb-2 font-medium">Path</th>
                <th className="pb-2 font-medium text-right">Hits</th>
                <th className="pb-2 font-medium text-right">Errors</th>
                <th className="pb-2 font-medium text-right">Avg Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {pages.length === 0 ? (
                <tr>
                  <td colSpan="4" className="py-4 text-center text-slate-500">
                    No endpoint visits recorded
                  </td>
                </tr>
              ) : (
                pages.slice(0, 6).map((item) => (
                  <tr key={item.path} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 font-mono text-indigo-300 font-medium truncate max-w-[180px]">
                      {item.path}
                    </td>
                    <td className="py-2.5 text-right font-semibold text-white">{item.hits}</td>
                    <td className="py-2.5 text-right">
                      {item.errors > 0 ? (
                        <span className="text-rose-400 font-semibold">{item.errors}</span>
                      ) : (
                        <span className="text-slate-500">0</span>
                      )}
                    </td>
                    <td className="py-2.5 text-right text-slate-300">
                      {item.avg_latency ? `${item.avg_latency}ms` : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Referrers */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur">
        <h2 className="text-base font-semibold text-white mb-1">Top Traffic Referrers</h2>
        <p className="text-xs text-slate-400 mb-4">Acquisition channels and inbound sources</p>
        <div className="space-y-3">
          {referrers.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-xs">No referrer data available</div>
          ) : (
            referrers.slice(0, 5).map((ref) => (
              <div key={ref.referrer} className="text-xs">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-mono text-slate-300 truncate max-w-[240px]">
                    {ref.referrer || 'Direct / Internal'}
                  </span>
                  <span className="text-slate-400 font-semibold">
                    {ref.hits} hits ({ref.percentage}%)
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-indigo-500 h-1.5 rounded-full"
                    style={{ width: `${Math.min(100, Math.max(5, ref.percentage))}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
