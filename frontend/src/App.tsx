import { useState, useEffect } from "react";
import { Sidebar, type PageId } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { Dashboard } from "./pages/Dashboard";
import { LiveCamera } from "./pages/LiveCamera";
import { Analytics } from "./pages/Analytics";
import { History } from "./pages/History";
import { Settings } from "./pages/Settings";
import { About } from "./pages/About";

// A global event emitter or custom hook could sync WebSocket data,
// but for maximum performance, the LiveCamera page handles its own local worker connections,
// and Topbar displays health stats based on the active stream telemetry.
// We can share telemetry data by lifting state, or let the LiveCamera emit custom events 
// that App.tsx listens to for Topbar updates!
// Let's implement a clean custom event-listener approach or simple local state synchronization 
// via custom events "telemetry-update". This is extremely clean, high-performance, and keeps 
// components decoupled!

export function App() {
  const [currentPage, setCurrentPage] = useState<PageId>("dashboard");
  const [darkMode, setDarkMode] = useState<boolean>(true);
  const [connected, setConnected] = useState<boolean>(false);
  const [systemStats, setSystemStats] = useState<any>(null);
  const [latency, setLatency] = useState<number>(0);

  // Simple global custom event listener to update Topbar telemetry when LiveCamera stream is active
  useEffect(() => {
    const handleTelemetryUpdate = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { connected: isConn, telemetry: tel } = customEvent.detail;
      setConnected(isConn);
      if (tel) {
        setSystemStats(tel.system || null);
        setLatency(tel.performance?.total_latency_ms || 0);
      }
    };
    
    const handleStreamStop = () => {
      setConnected(false);
      setSystemStats(null);
      setLatency(0);
    };

    window.addEventListener("telemetry-active", handleTelemetryUpdate);
    window.addEventListener("telemetry-inactive", handleStreamStop);
    
    return () => {
      window.removeEventListener("telemetry-active", handleTelemetryUpdate);
      window.removeEventListener("telemetry-inactive", handleStreamStop);
    };
  }, []);

  // Sync WebSocket states from local active streams
  // We can let the LiveCamera page dispatch custom events:
  // window.dispatchEvent(new CustomEvent('telemetry-active', { detail: { connected, telemetry } }));
  // when it receives frames. This is a very clean and decoupled pub/sub pattern!

  return (
    <div className={`w-screen h-screen flex overflow-hidden font-sans ${
      darkMode ? "bg-slate-950 text-slate-100" : "bg-slate-50 text-slate-900"
    }`}>
      {/* Navigation Sidebar */}
      <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} />

      {/* Main Panel Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Header telemetry display bar */}
        <Topbar 
          connected={connected} 
          systemStats={systemStats} 
          latencyMs={latency} 
          darkMode={darkMode}
          onThemeToggle={() => setDarkMode(!darkMode)}
        />

        {/* Dynamic page render */}
        <main className="flex-1 min-h-0 flex flex-col overflow-hidden">
          {currentPage === "dashboard" && <Dashboard onNavigate={setCurrentPage} />}
          {currentPage === "camera" && <LiveCameraWrapper />}
          {currentPage === "analytics" && <Analytics />}
          {currentPage === "history" && <History />}
          {currentPage === "settings" && <Settings />}
          {currentPage === "about" && <About />}
        </main>
      </div>
    </div>
  );
}

// Wrapper for LiveCamera to publish custom events to App.tsx
function LiveCameraWrapper() {
  return (
    <div className="flex-1 flex flex-col overflow-hidden" ref={(el) => {
      if (!el) {
        // Unmounted: notify app stream is stopped
        window.dispatchEvent(new CustomEvent("telemetry-inactive"));
      }
    }}>
      <LiveCamera />
    </div>
  );
}

// Attach custom event trigger inside LiveCamera page when telemetry updates
// (In LiveCamera.tsx, we can add a useEffect to dispatch the custom event whenever telemetry changes)
// Let's modify LiveCamera.tsx slightly to publish these events!
export default App;
