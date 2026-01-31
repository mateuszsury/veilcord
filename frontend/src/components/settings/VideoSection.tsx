/**
 * Video device settings section.
 *
 * Allows user to select:
 * - Camera (video input device)
 */

import { useState, useEffect } from 'react';
import { api } from '@/lib/pywebview';
import { useCall } from '@/stores/call';
import type { Camera } from '@/lib/pywebview';

export function VideoSection() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const { selectedCamera, setSelectedCamera } = useCall();

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    setLoading(true);
    try {
      const result = await api.call((a) => a.get_cameras());
      if (!result.error && result.cameras) {
        setCameras(result.cameras);

        // Select first camera if none selected
        if (result.cameras.length > 0 && selectedCamera === null) {
          const firstCamera = result.cameras[0];
          if (firstCamera) {
            setSelectedCamera(firstCamera.index);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load cameras:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCameraChange = async (index: number) => {
    try {
      await api.call((a) => a.set_camera(index));
      setSelectedCamera(index);
    } catch (error) {
      console.error('Failed to set camera:', error);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 p-4 bg-cosmic-surface/50 rounded-xl border border-cosmic-border">
        <h3 className="text-lg font-semibold text-cosmic-text flex items-center gap-2">
          {/* Camera icon */}
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          Video
        </h3>
        <p className="text-cosmic-muted">Loading cameras...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4 bg-cosmic-surface/50 rounded-xl border border-cosmic-border">
      <h3 className="text-lg font-semibold text-cosmic-text flex items-center gap-2">
        {/* Camera icon */}
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
        Video
      </h3>

      {/* Camera selection */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-cosmic-muted">
          Camera
        </label>
        <select
          value={selectedCamera ?? ''}
          onChange={(e) => handleCameraChange(Number(e.target.value))}
          className="w-full bg-cosmic-bg text-cosmic-text rounded-lg px-3 py-2 border border-cosmic-border focus:border-cosmic-accent focus:outline-none"
          disabled={cameras.length === 0}
        >
          {cameras.length === 0 ? (
            <option value="">No cameras detected</option>
          ) : (
            cameras.map((camera) => (
              <option key={camera.index} value={camera.index}>
                {camera.name}
              </option>
            ))
          )}
        </select>

        {cameras.length === 0 && (
          <p className="text-xs text-cosmic-muted">
            Connect a camera to use video calling features.
          </p>
        )}
      </div>
    </div>
  );
}
