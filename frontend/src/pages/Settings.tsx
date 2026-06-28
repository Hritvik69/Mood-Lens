import { useState } from "react";
import { Sliders, Camera, Shield, Database, Save, Sparkles } from "lucide-react";

export function Settings() {
  // Load initial settings from localStorage or defaults
  const [resolution, setResolution] = useState(() => localStorage.getItem("settings_resolution") || "720p");
  const [model, setModel] = useState(() => localStorage.getItem("settings_model") || "ferplus-8");
  const [dbLogging, setDbLogging] = useState(() => localStorage.getItem("settings_db_logging") !== "false");
  const [confidence, setConfidence] = useState(() => parseFloat(localStorage.getItem("settings_confidence") || "0.5"));
  const [smoothing, setSmoothing] = useState(() => parseFloat(localStorage.getItem("settings_smoothing") || "0.3"));
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    localStorage.setItem("settings_resolution", resolution);
    localStorage.setItem("settings_model", model);
    localStorage.setItem("settings_db_logging", String(dbLogging));
    localStorage.setItem("settings_confidence", String(confidence));
    localStorage.setItem("settings_smoothing", String(smoothing));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-3xl space-y-8 select-none">
      <div>
        <h2 className="text-2xl font-bold text-glow">System Settings</h2>
        <p className="text-xs text-slate-400">Configure real-time pipeline parameters and engine preferences.</p>
      </div>

      <div className="space-y-6">
        {/* Sliders Area */}
        <div className="glass-panel p-6 rounded-3xl space-y-6">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sliders size={16} className="text-brand-accent" />
            Detection Thresholds
          </h3>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-semibold">Min Confidence Threshold</span>
                <span className="text-brand-accent font-mono">{(confidence * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.90"
                step="0.05"
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-brand-accent"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Filters out expression classifications below this probability limit to prevent false positives.
              </span>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-semibold">Temporal Smoothing Factor (EMA)</span>
                <span className="text-brand-accent font-mono">{smoothing.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.80"
                step="0.05"
                value={smoothing}
                onChange={(e) => setSmoothing(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-brand-accent"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Exponential Moving Average coefficient. Lower values yield smoother predictions; higher values react faster to expression shifts.
              </span>
            </div>
          </div>
        </div>

        {/* Camera and Feed */}
        <div className="glass-panel p-6 rounded-3xl space-y-6">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Camera size={16} className="text-brand-accent" />
            Webcam Configurations
          </h3>
          
          <div>
            <label className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Default Startup Resolution</label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              className="glass-input w-full max-w-sm"
            >
              <option value="360p">360p (640x360)</option>
              <option value="480p">480p (854x480)</option>
              <option value="720p">720p (1280x720) - Standard</option>
              <option value="1080p">1080p (1920x1080) - HD</option>
            </select>
          </div>
        </div>

        {/* Model Configurations */}
        <div className="glass-panel p-6 rounded-3xl space-y-6">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Shield size={16} className="text-brand-accent" />
            Model Manager
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Active AI Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="glass-input w-full max-w-sm"
              >
                <option value="ferplus-8">FERPlus-8 (ONNX - Lightweight Classifier) [Default]</option>
                <option value="deepface">DeepFace Engine (TensorFlow - Highly Accurate but Slower)</option>
                <option value="landmark-heuristic">Landmark Heuristics (Rule-based - Fast)</option>
              </select>
            </div>
            
            <div className="p-3 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-xs text-brand-200 flex items-start gap-2 max-w-sm">
              <Sparkles size={14} className="shrink-0 mt-0.5" />
              <span>
                FERPlus-8 is recommended for real-time use (~10 ms). DeepFace is more accurate but slower (~200–500 ms). Landmark heuristics are instant but less robust.
              </span>
            </div>
          </div>
        </div>

        {/* Database Logging */}
        <div className="glass-panel p-6 rounded-3xl space-y-6">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Database size={16} className="text-brand-accent" />
            Local Database Storage
          </h3>
          
          <label className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition max-w-md">
            <div className="space-y-1">
              <span className="text-xs font-semibold text-slate-200 block">Write frame event logs to SQLite</span>
              <span className="text-[10px] text-slate-500 block">
                Disable this to prevent tracking telemetry from writing to disk.
              </span>
            </div>
            <input
              type="checkbox"
              checked={dbLogging}
              onChange={(e) => setDbLogging(e.target.checked)}
              className="rounded accent-brand-accent bg-slate-900 border-white/15 w-4 h-4"
            />
          </label>
        </div>

        {/* Save button */}
        <button
          onClick={handleSave}
          className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-brand-accent to-brand-500 text-slate-950 font-bold text-sm flex items-center gap-2 hover:opacity-90 shadow-lg shadow-brand-accent/20 transition-all duration-300 transform hover:scale-[1.02]"
        >
          <Save size={16} />
          {saved ? "Settings Saved Successfully!" : "Save Configurations"}
        </button>
      </div>
    </div>
  );
}
export default Settings;
