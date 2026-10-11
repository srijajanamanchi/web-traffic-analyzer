import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

export default function StatusCodeDonut({ statusData }) {
  const data = [
    { name: '2xx Success', value: statusData['2xx'] || 0, color: '#10b981' },
    { name: '3xx Redirect', value: statusData['3xx'] || 0, color: '#38bdf8' },
    { name: '4xx Client Err', value: statusData['4xx'] || 0, color: '#f59e0b' },
    { name: '5xx Server Err', value: statusData['5xx'] || 0, color: '#ef4444' },
  ].filter((item) => item.value > 0);

  const total = data.reduce((acc, curr) => acc + curr.value, 0);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur">
      <h2 className="text-base font-semibold text-white mb-1">Status Code Breakdown</h2>
      <p className="text-xs text-slate-400 mb-4">HTTP Response Distribution</p>

      {total === 0 ? (
        <div className="h-[200px] flex items-center justify-center text-slate-500 text-sm">
          No responses recorded yet
        </div>
      ) : (
        <div className="flex flex-col sm:flex-row items-center justify-between">
          <div className="h-[180px] w-[180px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '0.375rem',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="flex-1 w-full mt-3 sm:mt-0 sm:ml-4 space-y-2">
            {data.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center">
                  <span className="w-2.5 h-2.5 rounded-full mr-2" style={{ backgroundColor: item.color }} />
                  <span className="text-slate-300">{item.name}</span>
                </div>
                <div className="font-semibold text-white">
                  {item.value} <span className="text-slate-400 font-normal">({Math.round((item.value / total) * 100)}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
