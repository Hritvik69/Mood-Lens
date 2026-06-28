import { useState, useEffect } from "react";
import { Download, Trash2, ArrowLeft, ArrowRight, Filter, RefreshCw } from "lucide-react";

export function History() {
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(15);
  
  // Filters
  const [expressionFilter, setExpressionFilter] = useState("");
  const [sessionIdFilter, setSessionIdFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let url = `http://127.0.0.1:8000/api/history?page=${page}&limit=${limit}`;
      if (expressionFilter) url += `&expression=${expressionFilter}`;
      if (sessionIdFilter) url += `&session_id=${sessionIdFilter}`;
      
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.results);
        setTotal(data.total);
      }
    } catch (err) {
      console.warn("Failed to fetch history logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, expressionFilter, sessionIdFilter]);

  const handleClear = async () => {
    if (!window.confirm("Are you sure you want to clear all history records? This cannot be undone.")) return;
    try {
      const res = await fetch("http://127.0.0.1:8000/api/history", { method: "DELETE" });
      if (res.ok) {
        setLogs([]);
        setTotal(0);
        setPage(1);
      }
    } catch (err) {
      console.error("Failed to delete history:", err);
    }
  };

  // Helper colors for expression badges
  const getBadgeClass = (expr: string) => {
    switch (expr) {
      case "Happy": return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "Surprise": return "bg-amber-400/20 text-amber-400 border-amber-400/30";
      case "Sad": return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "Angry": return "bg-rose-500/20 text-rose-400 border-rose-500/30";
      case "Fear": return "bg-purple-500/20 text-purple-400 border-purple-500/30";
      case "Disgust": return "bg-orange-500/20 text-orange-400 border-orange-500/30";
      default: return "bg-slate-500/20 text-slate-400 border-slate-500/30";
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6 flex flex-col select-none">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div>
          <h2 className="text-2xl font-bold text-glow">Historical Database Logs</h2>
          <p className="text-xs text-slate-400">View, filter, and export frame events logged in SQLite.</p>
        </div>

        <div className="flex items-center gap-3">
          <a
            href="http://127.0.0.1:8000/api/history/export/csv"
            className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-white/5 border border-white/5 text-slate-300 hover:bg-white/10 hover:text-white transition flex items-center gap-2"
          >
            <Download size={13} />
            Export CSV
          </a>
          <a
            href="http://127.0.0.1:8000/api/history/export/json"
            className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-white/5 border border-white/5 text-slate-300 hover:bg-white/10 hover:text-white transition flex items-center gap-2"
          >
            <Download size={13} />
            Export JSON
          </a>
          
          <button
            onClick={handleClear}
            disabled={total === 0}
            className="px-4 py-2.5 rounded-xl text-xs font-bold bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 transition flex items-center gap-2 disabled:opacity-40 disabled:pointer-events-none"
          >
            <Trash2 size={13} />
            Clear logs
          </button>
        </div>
      </div>

      {/* Filters Area */}
      <div className="p-4 rounded-2xl bg-white/5 border border-white/5 flex flex-wrap items-center gap-4 shrink-0">
        <div className="flex items-center gap-2 text-xs text-slate-400 font-semibold">
          <Filter size={14} className="text-brand-accent" />
          Filter Logs:
        </div>
        
        {/* Session Filter */}
        <input
          type="text"
          placeholder="Session ID (e.g. sess_171...)"
          value={sessionIdFilter}
          onChange={(e) => {
            setSessionIdFilter(e.target.value);
            setPage(1);
          }}
          className="glass-input text-xs w-48"
        />

        {/* Expression Filter */}
        <select
          value={expressionFilter}
          onChange={(e) => {
            setExpressionFilter(e.target.value);
            setPage(1);
          }}
          className="glass-input text-xs w-40"
        >
          <option value="">All Expressions</option>
          <option value="Neutral">Neutral</option>
          <option value="Happy">Happy</option>
          <option value="Surprise">Surprise</option>
          <option value="Sad">Sad</option>
          <option value="Angry">Angry</option>
          <option value="Disgust">Disgust</option>
          <option value="Fear">Fear</option>
          <option value="Contempt">Contempt</option>
        </select>
        
        <button 
          onClick={fetchLogs} 
          className="p-2.5 rounded-xl bg-white/5 border border-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition ml-auto"
          title="Refresh Data"
        >
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Grid Container */}
      <div className="flex-1 min-h-0 rounded-2xl border border-white/10 bg-slate-950/40 overflow-hidden flex flex-col justify-between">
        <div className="overflow-x-auto overflow-y-auto flex-1">
          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-brand-accent border-t-transparent rounded-full animate-spin" />
            </div>
          ) : logs.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-xs text-slate-500">
              No historical data match the active filters
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 bg-white/5 text-slate-400 font-semibold select-none">
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">Session ID</th>
                  <th className="p-4 text-center">Face ID</th>
                  <th className="p-4">Expression</th>
                  <th className="p-4">Confidence</th>
                  <th className="p-4 text-center">Eye Contact</th>
                  <th className="p-4 text-center">Smile Int.</th>
                  <th className="p-4 text-center">Quality</th>
                  <th className="p-4 text-right">Inference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300 font-medium">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-white/5 transition duration-150">
                    <td className="p-4 font-mono text-slate-400">
                      {new Date(log.timestamp + "Z").toLocaleTimeString()}
                    </td>
                    <td className="p-4 font-mono text-[10px] text-slate-500 max-w-[120px] truncate" title={log.session_id}>
                      {log.session_id}
                    </td>
                    <td className="p-4 text-center font-mono">{log.face_id}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded-lg border text-[10px] font-bold ${getBadgeClass(log.expression)}`}>
                        {log.expression}
                      </span>
                    </td>
                    <td className="p-4 font-mono">{(log.confidence * 100).toFixed(1)}%</td>
                    <td className="p-4 text-center">
                      <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-semibold ${
                        log.eye_contact ? "bg-brand-500/10 text-brand-accent" : "bg-white/5 text-slate-500"
                      }`}>
                        {log.eye_contact ? "Direct" : "Averted"}
                      </span>
                    </td>
                    <td className="p-4 text-center font-mono">{log.smile_intensity.toFixed(0)}%</td>
                    <td className="p-4 text-center font-mono">{log.quality.score.toFixed(0)}%</td>
                    <td className="p-4 text-right font-mono text-slate-400">{log.inference_time_ms.toFixed(1)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-white/10 bg-white/5 flex items-center justify-between shrink-0 select-none">
            <span className="text-[10px] text-slate-500">
              Showing page {page} of {totalPages} ({total} entries total)
            </span>
            
            <div className="flex gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="px-3.5 py-2 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 text-slate-300 disabled:opacity-40 disabled:pointer-events-none transition flex items-center gap-1.5 text-xs font-semibold"
              >
                <ArrowLeft size={13} />
                Previous
              </button>
              <button
                disabled={page === totalPages}
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                className="px-3.5 py-2 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 text-slate-300 disabled:opacity-40 disabled:pointer-events-none transition flex items-center gap-1.5 text-xs font-semibold"
              >
                Next
                <ArrowRight size={13} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
export default History;
