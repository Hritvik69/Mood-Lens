import { useState, useEffect, useCallback, useRef } from "react";

export interface Resolution {
  label: string;
  width: number;
  height: number;
}

export const RESOLUTIONS: Record<string, Resolution> = {
  "360p": { label: "360p (640x360)", width: 640, height: 360 },
  "480p": { label: "480p (854x480)", width: 854, height: 480 },
  "720p": { label: "720p (1280x720)", width: 1280, height: 720 },
  "1080p": { label: "1080p (1920x1080)", width: 1920, height: 1080 },
};

export function useWebcam() {
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [activeDeviceId, setActiveDeviceId] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [activeResolution, setActiveResolution] = useState<string>("720p");
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // 1. Enumerate Video Input Devices
  const getDevices = useCallback(async () => {
    try {
      // Trigger temporary permission check to get labeled devices
      await navigator.mediaDevices.getUserMedia({ video: true }).then((tempStream) => {
        tempStream.getTracks().forEach((track) => track.stop());
      });

      const allDevices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = allDevices.filter((device) => device.kind === "videoinput");
      setDevices(videoDevices);
      
      if (videoDevices.length > 0 && !activeDeviceId) {
        setActiveDeviceId(videoDevices[0].deviceId);
      }
    } catch (err: any) {
      console.error("Failed to enumerate webcam devices:", err);
      setError("Webcam access denied or unavailable.");
    }
  }, [activeDeviceId]);

  useEffect(() => {
    getDevices();
  }, [getDevices]);

  // 2. Start Camera with Constraints
  const startCamera = useCallback(
    async (deviceId?: string, resolution?: string) => {
      // Stop active stream first
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      const targetDeviceId = deviceId || activeDeviceId;
      const targetResKey = resolution || activeResolution;
      const targetRes = RESOLUTIONS[targetResKey];

      const constraints: MediaStreamConstraints = {
        video: {
          deviceId: targetDeviceId ? { exact: targetDeviceId } : undefined,
          width: { ideal: targetRes.width },
          height: { ideal: targetRes.height },
          frameRate: { ideal: 30 },
        },
        audio: false, // AI only requires video
      };

      try {
        setError(null);
        const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
        setStream(mediaStream);
        streamRef.current = mediaStream;
        setIsStreaming(true);
        if (targetDeviceId) setActiveDeviceId(targetDeviceId);
        setActiveResolution(targetResKey);
        return mediaStream;
      } catch (err: any) {
        console.error("Error starting camera stream:", err);
        setError(`Failed to open camera: ${err.message || err}`);
        setIsStreaming(false);
        setStream(null);
        streamRef.current = null;
        throw err;
      }
    },
    [activeDeviceId, activeResolution]
  );

  // 3. Stop Camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      setStream(null);
      streamRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  return {
    devices,
    activeDeviceId,
    stream,
    activeResolution,
    isStreaming,
    error,
    startCamera,
    stopCamera,
    setActiveDeviceId,
    setActiveResolution,
  };
}
