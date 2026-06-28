import { Shield, Cpu, Activity, BrainCircuit } from "lucide-react";

export function About() {
  const sections = [
    {
      title: "Scientific Boundaries & Accuracy",
      description: "EmotionVision AI does NOT claim to read internal feelings, emotions, or cognitive thoughts. The AI is specifically trained to analyze physical muscle movements and classify 'Detected Facial Expressions' (neutral, happy, surprise, sad, angry, disgust, fear, contempt). Labeling classifications as facial expressions rather than actual internal emotions ensures scientific rigor.",
      icon: Shield,
      color: "text-brand-accent",
      bg: "bg-brand-accent/10"
    },
    {
      title: "100% Local Privacy Compliance",
      description: "Privacy is designed into the core system architecture. No webcam images, frame coordinates, or metrics are uploaded to external cloud endpoints. All calculations (MediaPipe landmarks extraction, OpenCV decoding, and ONNX Runtime inference) are processed purely in-memory on your local CPU or GPU, adhering to strict corporate security standards.",
      icon: Shield,
      color: "text-emerald-400",
      bg: "bg-emerald-400/10"
    },
    {
      title: "Advanced Multi-Threaded Engine",
      description: "The application offloads camera compression and binary WebSockets to Web Worker threads, decoupling the UI from performance-heavy background logic. In the backend, uvicorn event loops are unblocked by executing CPU-heavy MediaPipe tracking and ONNX predictions in isolated process executors.",
      icon: Cpu,
      color: "text-brand-300",
      bg: "bg-brand-300/10"
    },
    {
      title: "Face Quality & Alignment System",
      description: "To prevent false classifications, frames undergo strict validation: focus is computed using Laplacian edge variance, lighting levels are audited via standard luminance deviation, and facial angle skew is corrected using pupil-aligned affine rotations.",
      icon: Activity,
      color: "text-amber-400",
      bg: "bg-amber-400/10"
    }
  ];

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-4xl space-y-8 select-none">
      <div>
        <h2 className="text-2xl font-bold text-glow">About the Platform</h2>
        <p className="text-xs text-slate-400">Enterprise AI facial analytics and spatial pose solver documentation.</p>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sections.map((sec, idx) => {
          const Icon = sec.icon;
          return (
            <div key={idx} className="glass-panel p-6 rounded-3xl flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-xl ${sec.bg} ${sec.color}`}>
                  <Icon size={18} />
                </div>
                <h3 className="text-sm font-bold text-white">
                  {sec.title}
                </h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {sec.description}
              </p>
            </div>
          );
        })}
      </div>

      {/* Tech Stack details */}
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <BrainCircuit size={16} className="text-brand-accent" />
          Platform Specifications
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 rounded-2xl bg-white/5 border border-white/5 space-y-1">
            <span className="text-slate-500 block">Frontend</span>
            <span className="text-slate-200 font-bold block">React 19 + TypeScript</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-white/5 border border-white/5 space-y-1">
            <span className="text-slate-500 block">Styling</span>
            <span className="text-slate-200 font-bold block">Tailwind CSS + Motion</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-white/5 border border-white/5 space-y-1">
            <span className="text-slate-500 block">Backend Server</span>
            <span className="text-slate-200 font-bold block">FastAPI + Python 3</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-white/5 border border-white/5 space-y-1">
            <span className="text-slate-500 block">Inference Engine</span>
            <span className="text-slate-200 font-bold block">ONNX Runtime</span>
          </div>
        </div>
      </div>
    </div>
  );
}
export default About;
