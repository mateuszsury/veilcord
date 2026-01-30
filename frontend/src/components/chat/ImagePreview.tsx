/**
 * Image preview component with lightbox modal.
 *
 * Loads thumbnail on mount and displays with click-to-expand functionality.
 */

import { useEffect, useState } from 'react';
import { api } from '../../lib/pywebview';

interface ImagePreviewProps {
  fileId: number;
  filename: string;
  className?: string;
}

export function ImagePreview({ fileId, filename, className = '' }: ImagePreviewProps) {
  const [thumbnail, setThumbnail] = useState<string | null>(null);
  const [fullImage, setFullImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  // Load thumbnail on mount
  useEffect(() => {
    let mounted = true;

    const loadThumbnail = async () => {
      try {
        setLoading(true);
        const response = await api.call((api) => api.get_file_preview(fileId));

        if (!mounted) return;

        if (response.error) {
          setError(response.error);
        } else if (response.preview) {
          setThumbnail(`data:${response.mimeType || 'image/jpeg'};base64,${response.preview}`);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load preview');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadThumbnail();

    return () => {
      mounted = false;
    };
  }, [fileId]);

  // Load full image when modal opens
  const handleImageClick = async () => {
    if (!thumbnail) return;

    setShowModal(true);

    // Load full image if not already loaded
    if (!fullImage) {
      try {
        const response = await api.call((api) => api.get_file(String(fileId)));
        if (response.data) {
          setFullImage(`data:${response.mimeType || 'image/jpeg'};base64,${response.data}`);
        }
      } catch (err) {
        console.error('Failed to load full image:', err);
      }
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
  };

  if (loading) {
    return (
      <div className={`inline-flex items-center justify-center w-64 h-48 bg-gray-800 rounded ${className}`}>
        <div className="text-gray-400 text-sm">Loading preview...</div>
      </div>
    );
  }

  if (error || !thumbnail) {
    return (
      <div className={`inline-flex items-center justify-center w-64 h-48 bg-gray-800 rounded ${className}`}>
        <div className="text-gray-400 text-sm">
          {error || 'Preview not available'}
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Thumbnail */}
      <div className={className}>
        <img
          src={thumbnail}
          alt={filename}
          className="max-w-xs max-h-64 rounded cursor-pointer hover:opacity-90 transition-opacity"
          onClick={handleImageClick}
        />
      </div>

      {/* Lightbox Modal */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50"
          onClick={handleCloseModal}
        >
          <div className="relative max-w-[90vw] max-h-[90vh]">
            {/* Close button */}
            <button
              className="absolute top-4 right-4 text-white hover:text-gray-300 transition-colors"
              onClick={handleCloseModal}
            >
              <svg
                className="w-8 h-8"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>

            {/* Full image */}
            <img
              src={fullImage || thumbnail}
              alt={filename}
              className="max-w-full max-h-[90vh] object-contain"
              onClick={(e) => e.stopPropagation()}
            />

            {/* Filename caption */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-75 text-white px-4 py-2 rounded text-sm">
              {filename}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
