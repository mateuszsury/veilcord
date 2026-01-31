/**
 * VideoPlayer component for displaying video frames.
 *
 * Polls for video frames from the backend at ~30 FPS
 * and renders them to a canvas element.
 */

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/pywebview';

interface VideoPlayerProps {
  type: 'local' | 'remote';
  className?: string;
  onError?: (error: string) => void;
}

export function VideoPlayer({ type, className, onError }: VideoPlayerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isActive, setIsActive] = useState(false);
  const frameIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    startFramePolling();
    return () => stopFramePolling();
  }, [type]);

  const startFramePolling = () => {
    // Poll for frames at 30 FPS (33ms interval)
    frameIntervalRef.current = setInterval(async () => {
      try {
        const result =
          type === 'local'
            ? await api.call((a) => a.get_local_video_frame())
            : await api.call((a) => a.get_remote_video_frame());

        if ('frame' in result && result.frame) {
          drawFrame(result.frame);
          if (!isActive) setIsActive(true);
        } else if (isActive) {
          // No frame available, mark as inactive
          setIsActive(false);
        }
      } catch (e) {
        onError?.(`Video error: ${e}`);
      }
    }, 33);
  };

  const stopFramePolling = () => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
  };

  const drawFrame = (base64: string) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      // Resize canvas to match image
      if (canvas.width !== img.width || canvas.height !== img.height) {
        canvas.width = img.width;
        canvas.height = img.height;
      }
      ctx.drawImage(img, 0, 0);
    };
    img.src = `data:image/jpeg;base64,${base64}`;
  };

  return (
    <div className={`relative ${className || ''}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full object-contain bg-black rounded-lg"
      />
      {!isActive && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 rounded-lg">
          <span className="text-gray-400">No video</span>
        </div>
      )}
    </div>
  );
}
