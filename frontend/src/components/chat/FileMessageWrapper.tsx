/**
 * File message wrapper - lazy loads file metadata and renders FileMessage.
 *
 * Used when rendering messages from chat history that have a file_id.
 * Fetches file metadata on mount and passes to FileMessage component.
 */

import { useEffect, useState } from 'react';
import { api } from '@/lib/pywebview';
import { FileMessage } from './FileMessage';

interface FileMessageWrapperProps {
  fileId: number;
  className?: string;
}

interface FileMetadata {
  id: number;
  filename: string;
  mimeType: string;
  size: number;
}

export function FileMessageWrapper({ fileId, className = '' }: FileMessageWrapperProps) {
  const [metadata, setMetadata] = useState<FileMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadMetadata = async () => {
      try {
        setLoading(true);
        const response = await api.call((a) => a.get_file(String(fileId)));

        if (!mounted) return;

        if (response.error) {
          setError(response.error);
        } else if (response.id && response.filename && response.mimeType && response.size !== undefined) {
          setMetadata({
            id: parseInt(response.id),
            filename: response.filename,
            mimeType: response.mimeType,
            size: response.size,
          });
        } else {
          setError('Invalid file metadata');
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load file metadata');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadMetadata();

    return () => {
      mounted = false;
    };
  }, [fileId]);

  if (loading) {
    return (
      <div className={`inline-flex items-center gap-2 bg-cosmic-surface rounded px-3 py-2 ${className}`}>
        <div className="w-4 h-4 border-2 border-cosmic-accent border-t-transparent rounded-full animate-spin" />
        <span className="text-sm text-cosmic-muted">Loading file...</span>
      </div>
    );
  }

  if (error || !metadata) {
    return (
      <div className={`inline-flex items-center gap-2 bg-cosmic-surface rounded px-3 py-2 ${className}`}>
        <svg className="w-5 h-5 text-cosmic-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-sm text-cosmic-muted">{error || 'File not available'}</span>
      </div>
    );
  }

  return (
    <FileMessage
      fileId={metadata.id}
      filename={metadata.filename}
      mimeType={metadata.mimeType}
      size={metadata.size}
      className={className}
    />
  );
}
