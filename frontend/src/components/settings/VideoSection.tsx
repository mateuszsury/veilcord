/**
 * Video device settings section.
 *
 * Allows user to select:
 * - Camera (video input device)
 */

import { useState, useEffect } from 'react';
import { api } from '@/lib/pywebview';
import { useCall } from '@/stores/call';
import { Video } from 'lucide-react';
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
      <section className="space-y-6">
        <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
          <Video size={20} />
          Video
        </h3>
        <div className="h-px bg-discord-bg-tertiary" />
        <p className="text-sm text-discord-text-muted">Loading cameras...</p>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
        <Video size={20} />
        Video
      </h3>

      <div className="h-px bg-discord-bg-tertiary" />

      <div className="space-y-4">
        {/* Camera selection */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary">
              Camera
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Select your camera for video calls
            </p>
          </div>
          <select
            value={selectedCamera ?? ''}
            onChange={(e) => handleCameraChange(Number(e.target.value))}
            className="
              w-64 bg-discord-bg-tertiary border border-discord-bg-modifier-active
              rounded-md px-3 py-2 text-discord-text-primary
              focus:ring-2 focus:ring-accent-red focus:border-transparent
              focus:outline-none
              disabled:opacity-50 disabled:cursor-not-allowed
            "
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
        </div>

        {cameras.length === 0 && (
          <p className="text-xs text-discord-text-muted">
            Connect a camera to use video calling features.
          </p>
        )}
      </div>
    </section>
  );
}
