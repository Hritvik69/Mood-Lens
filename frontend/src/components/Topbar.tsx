import { 
  Activity, 
  Cpu, 
  Zap, 
  Moon, 
  Sun,
  ShieldCheck
} from "lucide-react";

interface TopbarProps {
  connected: boolean;
  systemStats: {
    cpu_usage: number;
    ram_usage: number;
    gpu_engine: string;
    fps: number;
  } | null;
  latencyMs: number;
  darkMode: boolean;
  onThemeToggle: () => void;
}

export function Topbar({ 
  connected, 
  systemStats, 
  latencyMs, 
  darkMode, 
  onThemeToggle 
}: TopbarProps) {
  
  const cpu = systemStats?.cpu_usage ?? 0;
  const ram = systemStats?.ram_usage ?? 0;
  const fps = systemStats?.fps ?? 0;
  const provider = systemStats?.gpu_engine 
    ? systemStats.gpu_engine.replace("ExecutionProvider", "") 
    : "N/A";

  return (
    <header className="h-16 border-b border-white/10 glass-panel flex items-center justify-between px-8 shrink-0 select-none z-10">
      {/* Title / Info */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${
            connected ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.6)]" : "bg-rose-500 shadow-[0_0_10px_rgba(239,68,68,0.6)]"
          }`} />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {connected ? "AI Engine Connected" : "AI Engine Disconnected"}
          </span>
        </div>
      </div>

      {/* Resource & Telemetry Widget */}
      <div className="flex items-center gap-6">
        {/* FPS Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
          <Activity size={14} className="text-brand-accent animate-pulse" />
          <div className="text-xs text-slate-400">
            FPS: <span className="font-semibold text-white text-glow">{fps.toFixed(1)}</span>
          </div>
        </div>

        {/* Latency Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
          <Zap size={14} className="text-amber-400" />
          <div className="text-xs text-slate-400">
            Latency: <span className="font-semibold text-white">{latencyMs > 0 ? `${latencyMs.toFixed(1)}ms` : "N/A"}</span>
          </div>
        </div>

        {/* CPU Tracker */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
          <Cpu size={14} className="text-brand-300" />
          <div className="text-xs text-slate-400">
            CPU: <span className="font-semibold text-white">{cpu.toFixed(0)}%</span>
          </div>
        </div>

        {/* RAM Tracker */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
          <Cpu size={14} className="text-emerald-400" />
          <div className="text-xs text-slate-400">
            RAM: <span className="font-semibold text-white">{ram.toFixed(0)}%</span>
          </div>
        </div>

        {/* Accelerator Engine */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-gradient-to-r from-brand-600/30 to-brand-400/20 border border-brand-500/20">
          <ShieldCheck size={14} className="text-brand-accent" />
          <div className="text-[11px] text-brand-100 font-medium">
            Provider: <span className="font-bold text-white uppercase tracking-wider">{provider}</span>
          </div>
        </div>

        {/* Divider */}
        <div className="w-[1px] h-6 bg-white/10" />

        {/* Theme Toggle Button */}
        <button 
          onClick={onThemeToggle}
          className="p-2 rounded-xl bg-white/5 border border-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition-all duration-300"
        >
          {darkMode ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
}
export default Topbar;
