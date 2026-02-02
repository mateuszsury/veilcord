/**
 * Transfer progress display component.
 *
 * Features:
 * - Shows active file transfers with progress bars
 * - Displays bytes transferred, speed, and ETA
 * - Cancel button for each transfer
 */

import { useTransferStore } from '@/stores/transfers';
import type { ActiveTransfer } from '@/stores/transfers';

interface TransferProgressProps {
  contactId: number;
}

export function TransferProgress({ contactId }: TransferProgressProps) {
  const transfers = useTransferStore((state) => state.transfers);
  const cancelTransfer = useTransferStore((state) => state.cancelTransfer);

  // Filter transfers for this contact
  const contactTransfers = Array.from(transfers.values()).filter(
    (t) => t.contactId === contactId
  );

  if (contactTransfers.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-discord-bg-tertiary p-4 space-y-3">
      {contactTransfers.map((transfer) => (
        <TransferItem
          key={transfer.transferId}
          transfer={transfer}
          onCancel={() => cancelTransfer(transfer.transferId, transfer.direction)}
        />
      ))}
    </div>
  );
}

interface TransferItemProps {
  transfer: ActiveTransfer;
  onCancel: () => void;
}

function TransferItem({ transfer, onCancel }: TransferItemProps) {
  const progress =
    transfer.totalBytes > 0
      ? (transfer.bytesTransferred / transfer.totalBytes) * 100
      : 0;

  const isActive = transfer.state === 'active' || transfer.state === 'pending';

  return (
    <div className="bg-discord-bg-secondary rounded-lg p-3">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {/* File icon */}
            <svg
              className="w-4 h-4 text-accent-red-text flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>

            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-discord-text-primary truncate">
                {transfer.filename}
              </p>
              <p className="text-xs text-discord-text-muted">
                {formatTransferInfo(transfer)}
              </p>
            </div>
          </div>
        </div>

        {/* Cancel button */}
        {isActive && (
          <button
            onClick={onCancel}
            className="text-discord-text-muted hover:text-status-busy transition-colors"
            title="Cancel transfer"
          >
            <svg
              className="w-4 h-4"
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
        )}
      </div>

      {/* Progress bar */}
      <div className="w-full bg-discord-bg-primary rounded-full h-1.5">
        <div
          className="bg-accent-red h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>

      {/* Status */}
      {transfer.state === 'failed' && (
        <p className="text-xs text-status-busy mt-1">Transfer failed</p>
      )}
      {transfer.state === 'cancelled' && (
        <p className="text-xs text-discord-text-muted mt-1">Cancelled</p>
      )}
      {transfer.state === 'complete' && (
        <p className="text-xs text-status-online mt-1">Complete</p>
      )}
    </div>
  );
}

function formatTransferInfo(transfer: ActiveTransfer): string {
  const { bytesTransferred, totalBytes, speedBps, etaSeconds, state, direction } = transfer;

  if (state === 'pending') {
    return `${direction === 'send' ? 'Sending' : 'Receiving'}... (pending)`;
  }

  if (state === 'complete') {
    return `${formatBytes(totalBytes)} - Complete`;
  }

  if (state === 'failed' || state === 'cancelled') {
    return formatBytes(bytesTransferred);
  }

  const parts: string[] = [];

  // Bytes transferred / total
  if (totalBytes > 0) {
    parts.push(`${formatBytes(bytesTransferred)} / ${formatBytes(totalBytes)}`);
  } else {
    parts.push(formatBytes(bytesTransferred));
  }

  // Speed
  if (speedBps > 0) {
    parts.push(`${formatBytes(speedBps)}/s`);
  }

  // ETA
  if (etaSeconds > 0 && etaSeconds < Infinity) {
    parts.push(`ETA ${formatTime(etaSeconds)}`);
  }

  return parts.join(' • ');
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(i === 0 ? 0 : 1)} ${sizes[i]}`;
}

function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);

  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  return `${hours}h ${remainingMinutes}m`;
}
