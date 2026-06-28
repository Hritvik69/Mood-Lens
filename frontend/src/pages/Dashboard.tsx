import { useState, useEffect } from "react";
import { 
  BarChart, 
  Activity, 
  UserCheck, 
  Heart,
  AlertTriangle,
  ArrowUpRight,
  Sparkles
} from "lucide-react";
import type { PageId } from "../components/Sidebar";

interface SummaryData {
  total_detections: number;
  total_sessions: number;
  average_confidence: number;
  average_inference_ms: number;
  average_quality: number;
  drowsiness_alerts: number;
}

export function Dashboard({ onNavigate }: { onNavigate: (page: PageId) => void }) {
  const [metrics, setMetrics] = useState<SummaryData>({
    total_detections: 0,
    total_sessions: 0,
    average_confidence: 0,
    average_inference_ms: 0,
    average_quality: 0,
    drowsiness_alerts: 0
  });
  const [loading, setLoading] = useState(true);

  const fetchSummary = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/analytics/summary");
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      console.warn("Could not load dashboard statistics from backend:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const statCards = [
    {
      title: "Total Face Scans",
      value: metrics.total_detections,
      icon: UserCheck,
      color: "text-brand-accent",
      bg: "bg-brand-accent/10",
      description: "Aggregated frames with faces detected"
    },
    {
      title: "Average Confidence",
      value: `${metrics.average_confidence.toFixed(1)}%`,
      icon: Heart,
      color: "text-emerald-400",
      bg: "bg-emerald-400/10",
      description: "Mean expression confidence score"
    },
    {
      title: "Avg Inference Latency",
      value: `${metrics.average_inference_ms.toFixed(1)} ms`,
      icon: Activity,
      color: "text-amber-400",
      bg: "bg-amber-400/10",
      description: "Average frame processing duration"
    },
    {
      title: "Drowsiness Triggers",
      value: metrics.drowsiness_alerts,
      icon: AlertTriangle,
      color: metrics.drowsiness_alerts > 0 ? "text-rose-500 animate-pulse" : "text-slate-400",
      bg: metrics.drowsiness_alerts > 0 ? "bg-rose-500/10" : "bg-white/5",
      description: "Fatigue warnings registered"
    }
  ];

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8 select-none">
      {/* Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-brand-800 to-slate-900 border border-white/10 p-8 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2 relative z-10">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-500/20 border border-brand-500/30 text-xs text-brand-accent font-semibold">
            <Sparkles size={12} />
            Enterprise Edition
          </div>
          <h2 className="text-3xl font-bold text-white tracking-tight">
            Welcome to EmotionVision AI
          </h2>
          <p className="text-sm text-slate-400 max-w-xl">
            Real-time multi-face alignment, landmark mesh tracking, head pose solver, eye indicators, and facial expression analysis locally on your hardware.
          </p>
        </div>
        <button
          onClick={() => onNavigate("camera")}
          className="relative z-10 px-6 py-3.5 rounded-2xl bg-gradient-to-r from-brand-accent to-brand-500 text-slate-950 font-bold text-sm flex items-center gap-2 hover:opacity-90 shadow-lg shadow-brand-accent/20 transition-all duration-300 transform hover:scale-[1.02]"
        >
          Launch Live Session
          <ArrowUpRight size={16} />
        </button>
        {/* Decorative Grid */}
        <div className="absolute right-0 bottom-0 top-0 w-1/3 opacity-20 pointer-events-none bg-[radial-gradient(ellipse_at_bottom_right,_var(--tw-gradient-stops))] from-brand-accent via-transparent to-transparent" />
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="glass-panel glass-panel-hover p-6 rounded-2xl flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-400">
                  {card.title}
                </span>
                <div className={`p-2.5 rounded-xl ${card.bg} ${card.color}`}>
                  <Icon size={18} />
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-bold text-white tracking-tight">
                  {loading ? "..." : card.value}
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  {card.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Core Widgets */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* AI Capabilities Card */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-3xl space-y-6">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Activity size={18} className="text-brand-accent" />
            Core Architecture Specs
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl bg-white/5 border border-white/5 space-y-2">
              <h4 className="text-xs font-semibold text-brand-accent">Inference Engine</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                ONNX Runtime sessions optimized utilizing DirectML or CUDA Execution Providers, warming up pipeline state vectors to maintain sub-40ms end-to-end processing speeds.
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/5 space-y-2">
              <h4 className="text-xs font-semibold text-brand-accent">Web Worker Offloading</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Offscreen canvas pipelines execute image compression and binary WebSockets off the main thread, locking browser DOM rendering speeds to 60 FPS.
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/5 space-y-2">
              <h4 className="text-xs font-semibold text-brand-accent">DuckDB Analytics</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Transactional events flow directly to SQLite (Write-Ahead Log) while analytics aggregations are mapped onto a live DuckDB engine for real-time aggregation queries.
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/5 space-y-2">
              <h4 className="text-xs font-semibold text-brand-accent">Face Quality Scoring</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Laplacian variance filters motion blur, and luminance channels evaluate brightness levels, yielding immediate alignment feedback to guarantee detection accuracy.
              </p>
            </div>
          </div>
        </div>

        {/* System Health / Status */}
        <div className="glass-panel p-6 rounded-3xl flex flex-col justify-between gap-6">
          <div className="space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart size={18} className="text-brand-accent" />
              Session Summary
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Open the live camera stream to initiate tracking. The system detects pupil centering, measures eye aspect ratios (EAR) to check for drowsiness, estimates 3D head coordinates, and charts expression frequencies.
            </p>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs p-3 rounded-xl bg-white/5 border border-white/5">
              <span className="text-slate-400">SQLite Database Path:</span>
              <span className="text-slate-300 font-mono">backend/emotionvision_ai.db</span>
            </div>
            <div className="flex items-center justify-between text-xs p-3 rounded-xl bg-white/5 border border-white/5">
              <span className="text-slate-400">ONNX Model Cache:</span>
              <span className="text-slate-300 font-mono">models/emotion-ferplus-8.onnx</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
export default Dashboard;
