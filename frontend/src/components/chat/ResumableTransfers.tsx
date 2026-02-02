/**
 * ResumableTransfers component - shows incomplete file transfers that can be resumed.
 *
 * Displays a list of interrupted send transfers with resume buttons.
 * Users must re-select the original file to continue the transfer.
 */

import { useEffect } from 'react';
import { useTransferStore } from '@/stores/transfers';

// SVG icons
const ICONS = {
  file: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  play: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  upload: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12',
};

function Icon({ path, className = 'w-4 h-4' }: { path: string; className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={path} />
    </svg>
  );
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

interface Props {
  contactId: number;
}

export function ResumableTransfers({ contactId }: Props) {
  const { resumableTransfers, loadResumableTransfers, resumeTransfer } = useTransferStore();

  // Load resumable transfers when contact changes
  useEffect(() => {
    loadResumableTransfers(contactId);
  }, [contactId, loadResumableTransfers]);

  // Filter transfers for this contact
  const transfers = Array.from(resumableTransfers.values()).filter(
    (t) => t.contact_id === contactId && t.direction === 'send'
  );

  if (transfers.length === 0) {
    return null;
  }

  return (
    <div className="border-b border-discord-bg-tertiary bg-discord-bg-secondary/50 px-4 py-2">
      <div className="flex items-center gap-2 mb-2">
        <Icon path={ICONS.upload} className="w-4 h-4 text-discord-text-muted" />
        <span className="text-sm text-discord-text-muted">Resumable Transfers</span>
      </div>

      <div className="space-y-2">
        {transfers.map((transfer) => {
          const progress = (transfer.bytes_transferred / transfer.size) * 100;

          return (
            <div
              key={transfer.id}
              className="flex items-center gap-3 p-2 rounded-lg bg-discord-bg-primary/50"
            >
              {/* File icon */}
              <div className="p-2 rounded-lg bg-accent-red/10 text-accent-red-text">
                <Icon path={ICONS.file} className="w-5 h-5" />
              </div>

              {/* File info */}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-discord-text-primary truncate">
                  {transfer.filename}
                </div>
                <div className="text-xs text-discord-text-muted">
                  {formatSize(transfer.bytes_transferred)} / {formatSize(transfer.size)}
                  {' - '}
                  {progress.toFixed(0)}% complete
                </div>

                {/* Progress bar */}
                <div className="mt-1 h-1 bg-discord-bg-modifier-active rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent-red transition-all"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Resume button */}
              <button
                onClick={() => resumeTransfer(contactId, transfer.id)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg
                           bg-accent-red text-white text-sm font-medium
                           hover:bg-accent-red-hover transition-colors"
                title="Resume transfer (select the same file)"
              >
                <Icon path={ICONS.play} className="w-4 h-4" />
                <span>Resume</span>
              </button>
            </div>
          );
        })}
      </div>

      <p className="mt-2 text-xs text-discord-text-muted">
        Click Resume and select the same file to continue the transfer.
      </p>
    </div>
  );
}
