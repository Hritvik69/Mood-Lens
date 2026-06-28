import { useEffect, useRef, useState, useCallback } from "react";

export function useWebSocket() {
  const [connected, setConnected] = useState<boolean>(false);
  const [telemetry, setTelemetry] = useState<any>(null);
  const [error, setError] = useState<boolean>(false);
  const workerRef = useRef<Worker | null>(null);

  // 1. Initialize Worker Thread
  const initWorker = useCallback((wsUrl: string, width: number, height: number) => {
    if (workerRef.current) {
      workerRef.current.terminate();
    }

    try {
      // Vite standard URL loader for Web Workers
      const worker = new Worker(
        new URL("../workers/frame.worker.ts", import.meta.url),
        { type: "module" }
      );

      worker.onmessage = (e: MessageEvent) => {
        const { type, data } = e.data;
        if (type === "status") {
          setConnected(data.connected);
          setError(!!data.error);
        } else if (type === "telemetry") {
          setTelemetry(data);
        }
      };

      worker.postMessage({
        type: "init",
        data: { url: wsUrl, width, height },
      });

      workerRef.current = worker;
      setError(false);
    } catch (err) {
      console.error("Failed to initialize Web Worker:", err);
      setError(true);
    }
  }, []);

  // 2. Stream ImageBitmap to Worker (using Transferable zero-copy boundary)
  const sendFrame = useCallback((bitmap: ImageBitmap) => {
    if (workerRef.current && connected) {
      // The second argument [bitmap] transfers ownership of the memory block,
      // preventing copy overhead and keeping main thread memory clean.
      workerRef.current.postMessage(
        {
          type: "frame",
          data: { bitmap },
        },
        [bitmap]
      );
    } else {
      // Close bitmap immediately if connection is down to prevent memory leaks
      bitmap.close();
    }
  }, [connected]);

  // 3. Dispatch Configuration updates
  const sendConfig = useCallback((config: any) => {
    if (workerRef.current) {
      workerRef.current.postMessage({
        type: "config",
        data: config,
      });
    }
  }, []);

  // 4. Terminate Worker
  const closeWorker = useCallback(() => {
    if (workerRef.current) {
      workerRef.current.postMessage({ type: "close" });
      workerRef.current.terminate();
      workerRef.current = null;
    }
    setConnected(false);
  }, []);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
      }
    };
  }, []);

  return {
    connected,
    telemetry,
    error,
    sendFrame,
    sendConfig,
    initWorker,
    closeWorker,
  };
}
