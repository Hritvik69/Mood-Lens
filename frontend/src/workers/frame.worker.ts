// Web Worker for off-thread frame compression and WebSocket communication.
// Fixed: backpressure control so we only send a new frame AFTER the server
// has responded to the previous one. This prevents queue flooding and keeps
// the FPS in sync with actual inference speed.

let ws: WebSocket | null = null;
let canvas: OffscreenCanvas | null = null;
let ctx: OffscreenCanvasRenderingContext2D | null = null;
let isConnected = false;

// Backpressure flag: true means we are waiting for a server response.
// We must NOT send a new frame until the server replies.
let awaitingResponse = false;

// Pending bitmap: if a new frame arrives while we are still waiting for a
// server response, keep only the LATEST frame (drop intermediate ones).
let pendingBitmap: ImageBitmap | null = null;

// Config state
let config = {
  confidence_threshold: 0.5,
  confidence_smoothing: 0.3,
  record_history: true
};

self.onmessage = async (e: MessageEvent) => {
  const { type, data } = e.data;

  if (type === "init") {
    const { url, width, height } = data;
    canvas = new OffscreenCanvas(width, height);
    ctx = canvas.getContext("2d");
    awaitingResponse = false;
    pendingBitmap = null;
    initWebSocket(url);
  }

  else if (type === "config") {
    config = { ...config, ...data };
    if (ws && isConnected) {
      ws.send(JSON.stringify(config));
    }
  }

  else if (type === "frame") {
    const { bitmap } = data;

    if (!isConnected || !ctx || !canvas) {
      bitmap.close();
      return;
    }

    if (awaitingResponse) {
      // Drop the OLD pending bitmap and keep only the LATEST frame.
      // This ensures we always send the most current frame once the server is ready.
      if (pendingBitmap) {
        pendingBitmap.close();
      }
      pendingBitmap = bitmap;
      return;
    }

    // Send this frame immediately
    await sendBitmap(bitmap);
  }

  else if (type === "close") {
    if (pendingBitmap) {
      pendingBitmap.close();
      pendingBitmap = null;
    }
    if (ws) {
      ws.close();
    }
    isConnected = false;
    awaitingResponse = false;
  }
};

async function sendBitmap(bitmap: ImageBitmap) {
  if (!ws || !isConnected || !ctx || !canvas) {
    bitmap.close();
    return;
  }

  awaitingResponse = true;

  // Draw the ImageBitmap to our offscreen canvas
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close(); // Clean memory immediately

  // Convert canvas to JPEG blob and send
  try {
    const blob = await canvas.convertToBlob({ type: "image/jpeg", quality: 0.82 });
    const arrayBuffer = await blob.arrayBuffer();
    if (ws && isConnected) {
      ws.send(arrayBuffer);
    } else {
      // Server went away while we were encoding — release the lock
      awaitingResponse = false;
      drainPending();
    }
  } catch (err) {
    console.error("Worker frame compression failed:", err);
    awaitingResponse = false;
    drainPending();
  }
}

/** If there is a pending frame queued up, send it now. */
function drainPending() {
  if (pendingBitmap && isConnected && !awaitingResponse) {
    const bmp = pendingBitmap;
    pendingBitmap = null;
    sendBitmap(bmp);
  }
}

function initWebSocket(url: string) {
  if (ws) {
    ws.close();
  }

  ws = new WebSocket(url);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => {
    isConnected = true;
    awaitingResponse = false;
    self.postMessage({ type: "status", data: { connected: true } });
    // Send initial configuration
    if (ws) {
      ws.send(JSON.stringify(config));
    }
  };

  ws.onmessage = (event) => {
    // Server replied — release the backpressure lock
    awaitingResponse = false;

    try {
      const payload = JSON.parse(event.data as string);
      self.postMessage({ type: "telemetry", data: payload });
    } catch (err) {
      console.error("Error parsing WebSocket JSON in worker:", err);
    }

    // Immediately drain any pending frame so the next inference starts ASAP
    drainPending();
  };

  ws.onclose = () => {
    isConnected = false;
    awaitingResponse = false;
    self.postMessage({ type: "status", data: { connected: false } });
    // Retry connection after a delay
    setTimeout(() => {
      if (!isConnected) {
        console.log("Worker reconnecting WebSocket...");
        initWebSocket(url);
      }
    }, 3000);
  };

  ws.onerror = (err) => {
    console.error("Worker WebSocket Error:", err);
    awaitingResponse = false;
    self.postMessage({ type: "status", data: { connected: false, error: true } });
  };
}
export {};
