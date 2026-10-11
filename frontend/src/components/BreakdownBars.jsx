
export default function BreakdownBars({ breakdown }) {
  const device = breakdown?.device || {};
  const browser = breakdown?.browser || {};
  const os = breakdown?.os || {};

  const renderSection = (title, items) => {
    const total = Object.values(items).reduce((a, b) => a + b, 0);

    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur">
        <h3 className="text-sm font-semibold text-white mb-1">{title}</h3>
        <p className="text-xs text-slate-400 mb-3">{total} total identified</p>

        {total === 0 ? (
          <div className="py-6 text-center text-slate-500 text-xs">No data yet</div>
        ) : (
          <div className="space-y-2">
            {Object.entries(items)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 4)
              .map(([key, val]) => {
                const pct = Math.round((val / total) * 100);
                return (
                  <div key={key} className="text-xs">
                    <div className="flex justify-between items-center mb-1 text-slate-300">
                      <span>{key}</span>
                      <span className="font-semibold text-white">
                        {val} <span className="text-slate-400 font-normal">({pct}%)</span>
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-1.5 rounded-full"
                        style={{ width: `${Math.max(4, pct)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      {renderSection('Device Platforms', device)}
      {renderSection('Web Browsers', browser)}
      {renderSection('Operating Systems', os)}
    </div>
  );
}
