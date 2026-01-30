/**
 * File message component - routes to appropriate preview based on MIME type.
 *
 * - Images: ImagePreview with lightbox
 * - Videos: VideoPreview with inline playback
 * - Audio/Voice: VoiceMessagePlayer with playback controls
 * - Other files: Generic download UI
 */

import { ImagePreview } from './ImagePreview';
import { VideoPreview } from './VideoPreview';
import { VoiceMessagePlayer } from './VoiceMessagePlayer';

// Audio file extensions that should render as voice messages
const AUDIO_EXTENSIONS = ['.ogg', '.opus', '.mp3', '.wav', '.m4a', '.webm', '.aac', '.flac'];

/**
 * Check if a file should be treated as a voice/audio message.
 */
function isVoiceMessage(mimeType: string, filename: string): boolean {
  // Check MIME type
  if (mimeType.startsWith('audio/')) {
    return true;
  }
  // Check file extension as fallback
  const lowerFilename = filename.toLowerCase();
  return AUDIO_EXTENSIONS.some(ext => lowerFilename.endsWith(ext));
}

interface FileMessageProps {
  fileId: number;
  filename: string;
  mimeType: string;
  size: number;
  className?: string;
}

export function FileMessage({ fileId, filename, mimeType, size, className = '' }: FileMessageProps) {
  // Route to appropriate preview component based on MIME type
  if (mimeType.startsWith('image/')) {
    return <ImagePreview fileId={fileId} filename={filename} className={className} />;
  }

  if (mimeType.startsWith('video/')) {
    return <VideoPreview fileId={fileId} filename={filename} className={className} />;
  }

  // Voice/audio messages get the voice player
  if (isVoiceMessage(mimeType, filename)) {
    return (
      <div className={className}>
        <VoiceMessagePlayer fileId={fileId} filename={filename} />
      </div>
    );
  }

  // Generic file download UI for other types
  return (
    <div className={`bg-gray-800 rounded p-4 max-w-xs ${className}`}>
      <div className="flex items-center gap-3">
        {/* File icon */}
        <svg
          className="w-10 h-10 text-gray-400 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
        </svg>

        {/* File info */}
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-white truncate">
            {filename}
          </div>
          <div className="text-xs text-gray-400">
            {formatFileSize(size)}
          </div>
        </div>

        {/* Download button */}
        <button
          className="flex-shrink-0 text-indigo-400 hover:text-indigo-300 transition-colors"
          onClick={() => handleDownload(fileId, filename)}
        >
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
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

// Helper function to format file size
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

// Download file handler
async function handleDownload(fileId: number, filename: string) {
  try {
    const { api } = await import('../../lib/pywebview');
    const response = await api.call((api) => api.get_file(String(fileId)));

    if (response.error) {
      console.error('Failed to download file:', response.error);
      return;
    }

    if (!response.data) {
      console.error('No file data received');
      return;
    }

    // Convert base64 to blob and trigger download
    const byteCharacters = atob(response.data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: response.mimeType || 'application/octet-stream' });

    // Create download link
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Error downloading file:', err);
  }
}
