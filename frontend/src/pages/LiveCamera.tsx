import { useEffect, useRef, useState } from "react";
import { useWebcam, RESOLUTIONS } from "../hooks/useWebcam";
import { useWebSocket } from "../hooks/useWebSocket";
import { 
  Camera, 
  CameraOff, 
  Video, 
  Settings,
  Sliders,
  ScanFace,
  Download,
  AlertTriangle
} from "lucide-react";

const MODEL_LABELS: Record<string, string> = {
  "ferplus-8": "FERPlus-8 (ONNX)",
  "deepface": "DeepFace (TensorFlow)",
  "landmark-heuristic": "Landmark Heuristics",
};

export function LiveCamera() {
  const {
    devices,
    activeDeviceId,
    stream,
    activeResolution,
    isStreaming,
    error: webcamError,
    startCamera,
    stopCamera,
    setActiveDeviceId,
    setActiveResolution,
  } = useWebcam();

  const {
    connected,
    telemetry,
    error: wsError,
    sendFrame,
    sendConfig,
    initWorker,
    closeWorker,
  } = useWebSocket();

  // Control Toggles
  const [enableBbox, setEnableBbox] = useState(true);
  const [enableMesh, setEnableMesh] = useState(true);
  const [enableConfidence, setEnableConfidence] = useState(true);
  const [enableFaceIds, setEnableFaceIds] = useState(true);
  const [mirror, setMirror] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);
  const [smoothing, setSmoothing] = useState(0.25);
  const [activeModel, setActiveModel] = useState(
    () => localStorage.getItem("settings_model") || "ferplus-8"
  );

  const videoRef = useRef<HTMLVideoElement | null>(null);
  // Overlay canvas for AI bounding boxes / landmarks (separate from live video)
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  // Continuous video-drawing loop ref
  const frameLoopRef = useRef<number | null>(null);
  // Video-capture loop ref (sends to AI backend)
  const captureLoopRef = useRef<number | null>(null);
  const [latency, setLatency] = useState<number>(0);
  const [videoDims, setVideoDims] = useState({ w: 640, h: 480 });

  // 1. Manage Active Stream and Worker Binding
  useEffect(() => {
    if (isStreaming && stream && videoRef.current) {
      const video = videoRef.current;
      video.srcObject = stream;
      
      const initWithDims = () => {
        const w = video.videoWidth;
        const h = video.videoHeight;
        const wsUrl = "ws://127.0.0.1:8000/ws";
        // Set canvas size AND video dims state before worker
        if (canvasRef.current) {
          canvasRef.current.width = w;
          canvasRef.current.height = h;
        }
        setVideoDims({ w, h });
        initWorker(wsUrl, w, h);
      };
      
      if (video.readyState >= 1) {
        initWithDims();
      } else {
        video.addEventListener("loadedmetadata", initWithDims, { once: true });
      }
    } else {
      if (videoRef.current) videoRef.current.srcObject = null;
      closeWorker();
      if (frameLoopRef.current) {
        cancelAnimationFrame(frameLoopRef.current);
        frameLoopRef.current = null;
      }
    }
  }, [isStreaming, stream, initWorker, closeWorker]);

  // 2. Dispatch Configuration Updates
  useEffect(() => {
    sendConfig({
      confidence_threshold: confidenceThreshold,
      confidence_smoothing: smoothing,
      record_history: true,
      model: activeModel,
    });
  }, [confidenceThreshold, smoothing, activeModel, sendConfig]);

  // Sync model selection when changed in Settings (same tab or other tab)
  useEffect(() => {
    const syncModel = () => {
      setActiveModel(localStorage.getItem("settings_model") || "ferplus-8");
    };
    window.addEventListener("storage", syncModel);
    return () => window.removeEventListener("storage", syncModel);
  }, []);

  // Publish telemetry events to App.tsx for Topbar stats
  useEffect(() => {
    if (isStreaming) {
      window.dispatchEvent(new CustomEvent("telemetry-active", { 
        detail: { connected, telemetry } 
      }));
    } else {
      window.dispatchEvent(new CustomEvent("telemetry-inactive"));
    }
  }, [connected, telemetry, isStreaming]);

  // 3. Safety net: sync canvas size if video dimensions ever change
  useEffect(() => {
    if (!canvasRef.current || !stream || !videoRef.current) return;
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const onMeta = () => {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      setVideoDims({ w: video.videoWidth, h: video.videoHeight });
    };
    if (video.readyState >= 1) {
      onMeta();
    } else {
      video.addEventListener("loadedmetadata", onMeta, { once: true });
    }
  }, [stream]);

  // 4a. Continuous video rendering loop — draws live video to screen at full fps.
  // This runs independently of AI inference so the video always looks smooth.
  useEffect(() => {
    if (!isStreaming) return;

    const videoDrawLoop = () => {
      // Just keep the loop alive; the <video> element renders itself automatically.
      // We only need this loop to drive the capture loop below.
      frameLoopRef.current = requestAnimationFrame(videoDrawLoop);
    };

    frameLoopRef.current = requestAnimationFrame(videoDrawLoop);

    return () => {
      if (frameLoopRef.current) {
        cancelAnimationFrame(frameLoopRef.current);
        frameLoopRef.current = null;
      }
    };
  }, [isStreaming]);

  // 4b. AI Frame Capture Loop — sends frames to backend as fast as backend can handle.
  // Uses createImageBitmap for zero-copy grab. The worker handles backpressure
  // (only one frame in-flight at a time), so this loop just keeps feeding frames.
  useEffect(() => {
    if (!isStreaming || !connected) return;

    let active = true;

    const captureLoop = async () => {
      while (active) {
        const video = videoRef.current;
        if (video && video.readyState >= 2 && !video.paused) {
          try {
            const bitmap = await createImageBitmap(video);
            sendFrame(bitmap);
          } catch (err) {
            console.error("Frame capture error:", err);
          }
        }
        // Small yield so we don't busy-loop and starve the main thread.
        // The worker's backpressure will naturally throttle actual sends.
        await new Promise<void>((r) => setTimeout(r, 16)); // ~60fps poll
      }
    };

    captureLoop();

    return () => {
      active = false;
      if (captureLoopRef.current) {
        cancelAnimationFrame(captureLoopRef.current);
        captureLoopRef.current = null;
      }
    };
  }, [isStreaming, connected, sendFrame]);

  // 4. Overlays Canvas Drawing Logic
  useEffect(() => {
    if (!canvasRef.current || !telemetry) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    
    // Use the tracked video dimensions (set once by canvas resize effect)
    const { w: videoW, h: videoH } = videoDims;
    
    // Ensure canvas matches video resolution
    if (canvas.width !== videoW || canvas.height !== videoH) {
      canvas.width = videoW;
      canvas.height = videoH;
    }
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const faces = telemetry.faces || [];
    if (telemetry.performance) {
      setLatency(telemetry.performance.total_latency_ms);
    }
    
    faces.forEach((face: any) => {
      const [bx, by, bw, bh] = face.bbox;
      
      // Bbox: mirror the x coordinate around canvas center
      const drawBX = mirror ? (canvas.width - bx - bw) : bx;
      const drawBY = by;
      
      // 1. Draw Bounding Box
      if (enableBbox) {
        ctx.strokeStyle = "rgba(0, 242, 254, 0.85)";
        ctx.lineWidth = 3;
        ctx.shadowBlur = 8;
        ctx.shadowColor = "rgba(0, 242, 254, 0.4)";
        
        // Draw rounded rectangle bounding box
        const radius = 12;
        ctx.beginPath();
        ctx.roundRect(drawBX, drawBY, bw, bh, radius);
        ctx.stroke();
        
        // Reset shadow
        ctx.shadowBlur = 0;
        
        // Draw Face Info Label Badge
        if (enableFaceIds || enableConfidence) {
          ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
          ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
          ctx.lineWidth = 1;
          
          // Emotion emoji map
          const EMOJI_MAP: Record<string, string> = {
            "Happy": "😀", "Sad": "😢", "Angry": "😠", "Surprise": "😲",
            "Fear": "😨", "Neutral": "😐", "Disgust": "🤢", "Contempt": "🙄",
          };
          const emoji = EMOJI_MAP[face.expression] ?? "";
          const label = `${enableFaceIds ? `Face #${face.face_id} ` : ""}${
            enableConfidence ? `${emoji} ${face.expression} (${(face.expression_confidence * 100).toFixed(0)}%)` : ""
          }`;
          
          ctx.font = "bold 12px Outfit, sans-serif";
          const textWidth = ctx.measureText(label).width;
          
          ctx.beginPath();
          ctx.roundRect(drawBX, drawBY - 30, textWidth + 20, 24, 6);
          ctx.fill();
          ctx.stroke();
          
          ctx.fillStyle = "#ffffff";
          ctx.fillText(label, drawBX + 10, drawBY - 14);
        }
      }
      
      // 2. Draw Landmark Mesh
      if (enableMesh && face.landmarks) {
        ctx.fillStyle = "rgba(126, 26, 255, 0.6)";
        ctx.strokeStyle = "rgba(0, 242, 254, 0.15)";
        ctx.lineWidth = 0.5;
        
        face.landmarks.forEach((lm: [number, number, number], idx: number) => {
          if (idx >= 468) return;
          
          const lx = lm[0] * canvas.width;
          const ly = lm[1] * canvas.height;
          // Mirror: flip x around canvas center
          const drawLx = mirror ? (canvas.width - lx) : lx;
          
          ctx.beginPath();
          ctx.arc(drawLx, ly, 1.0, 0, 2 * Math.PI);
          ctx.fill();
        });
        
        // Draw glowing irises (iris range: 468-477)
        if (face.landmarks.length > 473) {
          ctx.fillStyle = "rgba(0, 242, 254, 0.9)";
          [468, 473].forEach((irisIdx) => {
            const lm = face.landmarks[irisIdx];
            if (!lm) return;
            const lx = lm[0] * canvas.width;
            const ly = lm[1] * canvas.height;
            const drawLx = mirror ? (canvas.width - lx) : lx;
            ctx.beginPath();
            ctx.arc(drawLx, ly, 2.5, 0, 2 * Math.PI);
            ctx.fill();
          });
        }
      }
    });
  }, [telemetry, enableBbox, enableMesh, enableConfidence, enableFaceIds, mirror, videoDims]);

  // Take Canvas Screenshot
  const takeSnapshot = () => {
    const video = videoRef.current;
    if (!video) return;
    
    const snapCanvas = document.createElement("canvas");
    snapCanvas.width = video.videoWidth;
    snapCanvas.height = video.videoHeight;
    const snapCtx = snapCanvas.getContext("2d");
    if (!snapCtx) return;
    
    // Draw mirrored video if enabled
    if (mirror) {
      snapCtx.translate(snapCanvas.width, 0);
      snapCtx.scale(-1, 1);
    }
    snapCtx.drawImage(video, 0, 0, snapCanvas.width, snapCanvas.height);
    
    // Download snapshot
    const url = snapCanvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = url;
    a.download = `emotionvision_snapshot_${Date.now()}.png`;
    a.click();
  };

  const activeFaces = telemetry?.faces || [];

  return (
    <div className="flex-1 overflow-hidden flex flex-col lg:flex-row select-none">
      {/* Left Column: Webcam Viewer */}
      <div className="flex-1 p-8 flex flex-col justify-between overflow-y-auto">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-glow">Live AI Scan</h2>
              <p className="text-xs text-slate-400">Stream camera frames to the selected emotion detection engine.</p>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={isStreaming ? stopCamera : () => startCamera()}
                className={`px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 border transition-all duration-300 shadow-md ${
                  isStreaming
                    ? "bg-rose-500/10 text-rose-400 border-rose-500/20 hover:bg-rose-500/25"
                    : "bg-brand-accent/15 text-brand-accent border-brand-accent/30 hover:bg-brand-accent/25"
                }`}
              >
                {isStreaming ? (
                  <>
                    <CameraOff size={14} /> Stop Stream
                  </>
                ) : (
                  <>
                    <Camera size={14} /> Start Stream
                  </>
                )}
              </button>
              
              {isStreaming && (
                <button
                  onClick={takeSnapshot}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-white/5 border border-white/5 text-slate-300 hover:bg-white/10 hover:text-white transition-all"
                  title="Capture Snapshot"
                >
                  <Download size={14} />
                </button>
              )}
            </div>
          </div>
          
          {/* Main Webcam Box */}
          <div className="relative aspect-video rounded-3xl overflow-hidden glass-panel border border-white/15 shadow-2xl flex items-center justify-center bg-slate-950">
            {isStreaming && (
              <div className="animate-scan-line" />
            )}
            
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className={`absolute inset-0 w-full h-full object-cover ${mirror ? "scale-x-[-1]" : ""}`}
            />
            
            <canvas
              ref={canvasRef}
              className="absolute inset-0 w-full h-full object-cover z-20 pointer-events-none"
            />
            
            {webcamError && (
              <div className="absolute inset-0 bg-slate-950/90 z-30 flex items-center justify-center">
                <div className="text-center space-y-3 p-6">
                  <div className="w-10 h-10 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto text-rose-400">
                    <AlertTriangle size={20} />
                  </div>
                  <h4 className="text-xs font-semibold text-rose-400">Camera Access Error</h4>
                  <p className="text-[10px] text-slate-500 max-w-xs">{webcamError}</p>
                </div>
              </div>
            )}

            {!isStreaming && !webcamError && (
              <div className="text-center space-y-4 p-6 z-10">
                <div className="w-16 h-16 rounded-full bg-slate-900 border border-white/5 flex items-center justify-center mx-auto text-slate-500">
                  <Video size={28} />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-slate-300">Camera Inactive</h4>
                  <p className="text-xs text-slate-500 max-w-[280px]">
                    Click "Start Stream" above to activate your webcam and begin tracking faces.
                  </p>
                </div>
              </div>
            )}
            
            {isStreaming && (wsError || !connected) && (
              <div className="absolute inset-0 bg-slate-950/80 z-30 flex items-center justify-center">
                <div className="text-center space-y-3 p-6">
                  <div className="w-10 h-10 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto text-rose-400 animate-pulse">
                    <AlertTriangle size={20} />
                  </div>
                  <h4 className="text-xs font-semibold text-rose-400">
                    {wsError ? "AI Connection Error" : "Reconnecting AI Engine"}
                  </h4>
                  <p className="text-[10px] text-slate-500">
                    {wsError ? "FastAPI WebSocket server is unreachable." : "WebSocket connection failed. Retrying..."}
                  </p>
                </div>
              </div>
            )}
          </div>

          {isStreaming && (
            <p className="text-[10px] text-slate-500 text-center">
              Active engine:{" "}
              <span className="text-brand-accent font-semibold">
                {MODEL_LABELS[activeModel] ?? activeModel}
              </span>
            </p>
          )}
        </div>

        {/* Live Diagnostics Summary */}
        {isStreaming && (
          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Engine latency</span>
              <span className="text-sm font-bold text-white mt-1 block">{latency > 0 ? `${latency.toFixed(1)} ms` : "---"}</span>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">FPS Feed</span>
              <span className="text-sm font-bold text-white mt-1 block">{telemetry?.performance?.fps || "0.0"} Hz</span>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Faces tracked</span>
              <span className="text-sm font-bold text-white mt-1 block">{activeFaces.length}</span>
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Controls & Analytics */}
      <div className="w-full lg:w-96 border-l border-white/10 glass-panel flex flex-col overflow-y-auto shrink-0 z-10">
        {/* Toggle Controls Tab */}
        <div className="p-6 border-b border-white/5 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sliders size={16} className="text-brand-accent" />
            Visual Toggles
          </h3>
          
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition">
              <span className="text-xs font-medium text-slate-400">Bounding Box</span>
              <input
                type="checkbox"
                checked={enableBbox}
                onChange={(e) => setEnableBbox(e.target.checked)}
                className="rounded accent-brand-accent bg-slate-900 border-white/15"
              />
            </label>
            <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition">
              <span className="text-xs font-medium text-slate-400">Landmark Mesh</span>
              <input
                type="checkbox"
                checked={enableMesh}
                onChange={(e) => setEnableMesh(e.target.checked)}
                className="rounded accent-brand-accent bg-slate-900 border-white/15"
              />
            </label>
            <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition">
              <span className="text-xs font-medium text-slate-400">Confidence Label</span>
              <input
                type="checkbox"
                checked={enableConfidence}
                onChange={(e) => setEnableConfidence(e.target.checked)}
                className="rounded accent-brand-accent bg-slate-900 border-white/15"
              />
            </label>
            <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition">
              <span className="text-xs font-medium text-slate-400">Face ID</span>
              <input
                type="checkbox"
                checked={enableFaceIds}
                onChange={(e) => setEnableFaceIds(e.target.checked)}
                className="rounded accent-brand-accent bg-slate-900 border-white/15"
              />
            </label>
          </div>

          <label className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 transition">
            <span className="text-xs font-medium text-slate-400">Mirror Webcam Output</span>
            <input
              type="checkbox"
              checked={mirror}
              onChange={(e) => setMirror(e.target.checked)}
              className="rounded accent-brand-accent bg-slate-900 border-white/15"
            />
          </label>
        </div>

        {/* Video Device Configuration */}
        <div className="p-6 border-b border-white/5 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Settings size={16} className="text-brand-accent" />
            Device Settings
          </h3>
          
          <div className="space-y-3">
            <div>
              <label className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Select Camera</label>
              <select
                value={activeDeviceId || ""}
                onChange={(e) => {
                  setActiveDeviceId(e.target.value);
                  if (isStreaming) startCamera(e.target.value);
                }}
                className="w-full glass-input"
              >
                {devices.map((device) => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.label || `Camera ${device.deviceId.slice(0, 5)}`}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Inference Resolution</label>
              <select
                value={activeResolution}
                onChange={(e) => {
                  setActiveResolution(e.target.value);
                  if (isStreaming) startCamera(undefined, e.target.value);
                }}
                className="w-full glass-input"
              >
                {Object.keys(RESOLUTIONS).map((resKey) => (
                  <option key={resKey} value={resKey}>
                    {RESOLUTIONS[resKey].label}
                  </option>
                ))}
              </select>
            </div>

            {/* Threshold Slider */}
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-[10px] text-slate-500 uppercase tracking-wider block">Min Confidence</label>
                <span className="text-xs text-slate-400">{(confidenceThreshold * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-brand-accent"
              />
            </div>

            {/* Smoothing Slider */}
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-[10px] text-slate-500 uppercase tracking-wider block">
                  {smoothing > 0.5 ? "Smooth" : "Responsive"} Mode
                </label>
                <span className="text-xs text-slate-400">
                  {smoothing > 0.5 ? "Stable" : "Quick"} ({smoothing.toFixed(2)})
                </span>
              </div>
              <div className="flex justify-between text-[9px] text-slate-600 mb-1">
                <span>Quick</span>
                <span>Stable</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={smoothing}
                onChange={(e) => setSmoothing(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-brand-accent"
              />
              <p className="text-[9px] text-slate-600 mt-1">
                Higher = smoother emotion tracking, Lower = faster response
              </p>
            </div>
          </div>
        </div>

        {/* Dynamic Face Cards */}
        <div className="p-6 flex-1 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ScanFace size={16} className="text-brand-accent" />
            Detected Facial Expressions
          </h3>
          
          {activeFaces.length === 0 ? (
            <div className="p-6 rounded-2xl bg-white/5 border border-white/5 text-center text-xs text-slate-500">
              No faces currently tracked in viewport
            </div>
          ) : (
            activeFaces.map((face: any) => {
              const quality = face.quality || { score: 0 };
              const blink = face.blink_metrics || {};
              const pitch = face.pose?.pitch || 0;
              const yaw = face.pose?.yaw || 0;
              
              const EMOJI_MAP: Record<string, string> = {
                "Happy": "😀", "Sad": "😢", "Angry": "😠", "Surprise": "😲",
                "Fear": "😨", "Neutral": "😐", "Disgust": "🤢", "Contempt": "🙄",
              };
              const emoji = EMOJI_MAP[face.expression] ?? "😊";
              
              return (
                <div key={face.face_id} className="p-5 rounded-2xl bg-white/5 border border-white/10 space-y-4 relative overflow-hidden">
                  {/* Face Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-xl bg-brand-500/20 border border-brand-500/30 flex items-center justify-center text-brand-accent font-bold text-xs">
                        ID:{face.face_id}
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white">Detected Facial Expression</div>
                        <div className="text-xs text-slate-500">Face tracked successfully</div>
                      </div>
                    </div>
                    
                    <span className="text-lg font-black text-brand-accent text-glow bg-brand-500/20 px-3 py-1 rounded-xl">
                      {emoji} {face.expression}
                    </span>
                  </div>

                  {/* Confidence Bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>Expression Confidence</span>
                      <span>{(face.expression_confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-brand-accent to-brand-500 rounded-full transition-all duration-300"
                        style={{ width: `${face.expression_confidence * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Quality & Indicators Grid */}
                  <div className="grid grid-cols-2 gap-3 text-[10px]">
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-white/5 space-y-0.5">
                      <span className="text-slate-500">Quality Score</span>
                      <span className={`font-bold block ${
                        quality.score > 70 ? "text-emerald-400" : quality.score > 40 ? "text-amber-400" : "text-rose-500"
                      }`}>{quality.score}%</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-white/5 space-y-0.5">
                      <span className="text-slate-500">Smile Intensity</span>
                      <span className="text-slate-200 font-bold block">{blink.smile_intensity || 0}%</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-white/5 space-y-0.5">
                      <span className="text-slate-500">Eye Contact</span>
                      <span className={`font-bold block ${
                        blink.eye_contact ? "text-brand-accent" : "text-slate-500"
                      }`}>{blink.eye_contact ? "Direct Look" : "Averted"}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-white/5 space-y-0.5">
                      <span className="text-slate-500">Blink Rate (BPM)</span>
                      <span className="text-slate-200 font-bold block">{blink.blink_rate || 0}</span>
                    </div>
                  </div>

                  {/* Pose Details */}
                  <div className="text-[10px] text-slate-500 flex justify-between px-1">
                    <span>Pose: P:{pitch}° Y:{yaw}°</span>
                    <span>Distance: {face.distance}m</span>
                  </div>

                  {/* Recommendations Warnings */}
                  {quality.recommendations && quality.recommendations[0] !== "Face quality optimal" && (
                    <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/25 flex items-start gap-2">
                      <AlertTriangle size={12} className="text-rose-400 shrink-0 mt-0.5" />
                      <div className="text-[10px] text-rose-300 leading-normal">
                        {quality.recommendations.join(", ")}
                      </div>
                    </div>
                  )}

                  {blink.drowsiness_detected && (
                    <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/25 flex items-start gap-2 animate-pulse">
                      <AlertTriangle size={12} className="text-amber-400 shrink-0 mt-0.5" />
                      <span className="text-[10px] font-bold text-amber-300">
                        Drowsiness Warning: Eyes Closed
                      </span>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
export default LiveCamera;
