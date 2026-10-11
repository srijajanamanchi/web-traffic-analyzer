import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function TimeSeriesChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-lg h-[340px] flex items-center justify-center text-slate-500">
        Waiting for traffic data...
      </div>
    );
  }

  // Format timestamp for display (e.g. HH:MM)
  const formattedData = data.map((item) => ({
    ...item,
    time: item.timestamp ? item.timestamp.split(' ')[1] || item.timestamp : '',
  }));

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-white">Traffic Throughput & Error Rate</h2>
          <p className="text-xs text-slate-400">Requests per minute vs errors</p>
        </div>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 mr-1.5"></span>
            <span className="text-slate-300">Requests</span>
          </div>
          <div className="flex items-center">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 mr-1.5"></span>
            <span className="text-slate-300">Errors</span>
          </div>
        </div>
      </div>

      <div className="h-[260px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="reqGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="errGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.5rem',
                color: '#fff',
                fontSize: '12px',
              }}
            />
            <Area
              type="monotone"
              dataKey="requests"
              stroke="#6366f1"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#reqGradient)"
            />
            <Area
              type="monotone"
              dataKey="errors"
              stroke="#f43f5e"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#errGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
