/**
 * LocalPreview component for small camera/screen preview.
 *
 * Shows a small picture-in-picture style preview of the local
 * video stream during video calls.
 */

import { VideoPlayer } from './VideoPlayer';
import { useCall } from '@/stores/call';

interface LocalPreviewProps {
  className?: string;
}

export function LocalPreview({ className }: LocalPreviewProps) {
  const { videoEnabled, videoSource } = useCall();

  if (!videoEnabled) {
    return null;
  }

  return (
    <div
      className={`absolute bottom-4 right-4 w-48 h-36 rounded-lg overflow-hidden shadow-lg border border-gray-700 ${className || ''}`}
    >
      <VideoPlayer type="local" className="w-full h-full" />
      <div className="absolute bottom-1 left-1 px-2 py-0.5 bg-black/60 rounded text-xs text-gray-300">
        {videoSource === 'camera' ? 'Camera' : 'Screen'}
      </div>
    </div>
  );
}
