import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Users,
  Clock,
  AlertOctagon,
  Eye,
  Radio,
  ExternalLink,
  Filter,
  RefreshCw,
} from 'lucide-react';
import MetricCard from './components/MetricCard.jsx';
import TimeSeriesChart from './components/TimeSeriesChart.jsx';
import StatusCodeDonut from './components/StatusCodeDonut.jsx';
import TopTable from './components/TopTable.jsx';
import BreakdownBars from './components/BreakdownBars.jsx';
import AnomalyPanel from './components/AnomalyPanel.jsx';
import LiveFeed from './components/LiveFeed.jsx';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = API_BASE.replace(/^http/, 'ws') + '/ws/traffic';

export default function App() {
  const [timeRange, setTimeRange] = useState('1h');
  const [pathFilter, setPathFilter] = useState('');
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  const wsRef = useRef(null);

  // Fetch initial analytics summary
  const fetchStats = async () => {
    try {
      const url = new URL(`${API_BASE}/api/stats`);
      url.searchParams.set('time_range', timeRange);
      if (pathFilter) url.searchParams.set('path', pathFilter);

      const res = await fetch(url.toString());
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentEvents = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/events?limit=25`);
      if (res.ok) {
        const data = await res.json();
        setEvents(data);
      }
    } catch (err) {
      console.error('Failed to fetch events:', err);
    }
  };

  const fetchAnomalies = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/anomalies?limit=15`);
      if (res.ok) {
        const data = await res.json();
        setAnomalies(data);
      }
    } catch (err) {
      console.error('Failed to fetch anomalies:', err);
    }
  };

  // Re-fetch on filter change
  useEffect(() => {
    fetchStats();
  }, [timeRange, pathFilter]);

  // Initial load
  useEffect(() => {
    fetchStats();
    fetchRecentEvents();
    fetchAnomalies();
  }, []);

  // WebSocket lifecycle management
  useEffect(() => {
    let reconnectTimer;

    function connectWs() {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'kpi_tick') {
              setStats((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  active_users_now: msg.data.active_users_now,
                };
              });
            } else if (msg.type === 'new_event') {
              setEvents((prev) => [msg.event, ...prev.slice(0, 30)]);
              // Soft refresh stats in background
              fetchStats();
            } else if (msg.type === 'anomaly_alert') {
              setAnomalies((prev) => [msg.alert, ...prev]);
            }
          } catch (e) {
            console.error('Failed to parse WS packet:', e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimer = setTimeout(connectWs, 3000);
        };

        ws.onerror = () => {
          setWsConnected(false);
          ws.close();
        };
      } catch (e) {
        setWsConnected(false);
        reconnectTimer = setTimeout(connectWs, 3000);
      }
    }

    connectWs();

    return () => {
      clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600 p-2 rounded-lg shadow-md shadow-indigo-600/30">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                Real-Time Web Traffic Analyzer
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  DevOps Pipeline Edition
                </span>
              </h1>
              <p className="text-xs text-slate-400">Continuous Telemetry, Anomaly Detection & Prometheus Metrics</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Live WebSocket Status */}
            <div className="flex items-center space-x-2 text-xs px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  wsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                }`}
              />
              <span className={wsConnected ? 'text-emerald-400 font-medium' : 'text-rose-400'}>
                {wsConnected ? 'Live Stream Active' : 'Connecting to API...'}
              </span>
            </div>

            {/* Link to Demo Site */}
            <a
              href="http://localhost:8080"
              target="_blank"
              rel="noreferrer"
              className="hidden sm:flex items-center space-x-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium px-3 py-1.5 rounded-lg border border-indigo-500/30 hover:bg-indigo-500/10 transition"
            >
              <span>Open Demo Site</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Controls Bar: Filters & Refresh */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" /> Filter Range:
            </span>
            <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
              {['5m', '15m', '1h', '24h', 'all'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-3 py-1 rounded text-xs font-medium transition ${
                    timeRange === range
                      ? 'bg-indigo-600 text-white shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {range.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Path Filter */}
            <input
              type="text"
              placeholder="Filter path (e.g. /products)..."
              value={pathFilter}
              onChange={(e) => setPathFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs px-3 py-1.5 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-48 font-mono"
            />
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                fetchStats();
                fetchRecentEvents();
                fetchAnomalies();
              }}
              className="flex items-center space-x-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 rounded-lg transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Top KPI Cards Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <MetricCard
            title="Total Requests"
            value={stats ? stats.total_requests.toLocaleString() : '—'}
            subtitle={`Window: Last ${timeRange}`}
            icon={Eye}
            color="indigo"
          />
          <MetricCard
            title="Active Visitors Now"
            value={stats ? stats.active_users_now : '—'}
            subtitle="Active within last 5m"
            icon={Users}
            color="emerald"
          />
          <MetricCard
            title="Unique Visitors"
            value={stats ? stats.unique_visitors : '—'}
            subtitle="Distinct Sessions"
            icon={Radio}
            color="cyan"
          />
          <MetricCard
            title="Error Rate"
            value={stats ? `${stats.error_rate}%` : '—'}
            subtitle="4xx & 5xx HTTP Responses"
            icon={AlertOctagon}
            color={stats && stats.error_rate > 10 ? 'rose' : 'amber'}
          />
          <MetricCard
            title="P95 Latency"
            value={stats ? `${stats.latency.p95}ms` : '—'}
            subtitle={`Avg: ${stats ? stats.latency.avg : 0}ms`}
            icon={Clock}
            color="emerald"
          />
        </div>

        {/* Charts & Status Donut Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TimeSeriesChart data={stats?.time_series || []} />
          </div>
          <div>
            <StatusCodeDonut statusData={stats?.status_codes || {}} />
          </div>
        </div>

        {/* Top Pages & Referrers Row */}
        <TopTable pages={stats?.top_pages || []} referrers={stats?.top_referrers || []} />

        {/* Device, Browser & OS Breakdowns */}
        <BreakdownBars breakdown={stats?.breakdown || {}} />

        {/* Anomalies Panel & Live Feed Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AnomalyPanel anomalies={anomalies} />
          <LiveFeed events={events} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-4 text-center text-xs text-slate-500">
        <p>
          Real-Time Web Traffic Analyzer &bull; Complete End-to-End DevOps Pipeline &bull; Automated Telemetry &bull; Prometheus + Grafana Observability
        </p>
      </footer>
    </div>
  );
}
