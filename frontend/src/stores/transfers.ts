/**
 * Transfer store - manages file transfer state and API interactions.
 *
 * Handles:
 * - Active file transfers (sending and receiving)
 * - Transfer progress tracking
 * - Received files history
 * - Initiating file transfers
 * - Canceling transfers
 */

import { create } from 'zustand';
import { api } from '@/lib/pywebview';
import type {
  FileTransferProgress,
  FileMetadata,
  TransferDirection,
} from '@/lib/pywebview';

export interface ActiveTransfer extends FileTransferProgress {
  contactId: number;
  direction: TransferDirection;
  filename: string;
  mimeType?: string;
}

export interface ReceivedFile extends FileMetadata {
  contactId: number;
  receivedAt: number;
}

interface TransfersState {
  // Active transfers by transfer ID
  transfers: Map<string, ActiveTransfer>;

  // Received files by file ID
  receivedFiles: Map<string, ReceivedFile>;

  // Actions
  sendFile: (contactId: number) => Promise<void>;
  cancelTransfer: (transferId: string, direction?: TransferDirection) => Promise<void>;
  addTransfer: (transfer: ActiveTransfer) => void;
  updateProgress: (transferId: string, progress: Partial<FileTransferProgress>) => void;
  removeTransfer: (transferId: string) => void;
  addReceivedFile: (file: ReceivedFile) => void;
}

export const useTransferStore = create<TransfersState>((set, get) => ({
  transfers: new Map(),
  receivedFiles: new Map(),

  sendFile: async (contactId: number) => {
    try {
      // Open file dialog
      const fileResult = await api.call((a) => a.open_file_dialog());

      if (fileResult.cancelled || !fileResult.path) {
        return;
      }

      if (fileResult.error) {
        console.error('File dialog error:', fileResult.error);
        return;
      }

      // Start file transfer
      const result = await api.call((a) => a.send_file(contactId, fileResult.path!));

      if (result.error) {
        console.error('Send file error:', result.error);
        return;
      }

      // Transfer started - progress will be updated via events
    } catch (error) {
      console.error('Failed to send file:', error);
    }
  },

  cancelTransfer: async (transferId: string, direction?: TransferDirection) => {
    const transfer = get().transfers.get(transferId);
    if (!transfer) {
      console.warn('Transfer not found:', transferId);
      return;
    }

    try {
      const result = await api.call((a) =>
        a.cancel_transfer(transfer.contactId, transferId, direction)
      );

      if (result.error) {
        console.error('Cancel transfer error:', result.error);
        return;
      }

      // Remove from active transfers
      get().removeTransfer(transferId);
    } catch (error) {
      console.error('Failed to cancel transfer:', error);
    }
  },

  addTransfer: (transfer: ActiveTransfer) => {
    set((state) => {
      const transfers = new Map(state.transfers);
      transfers.set(transfer.transferId, transfer);
      return { transfers };
    });
  },

  updateProgress: (transferId: string, progress: Partial<FileTransferProgress>) => {
    set((state) => {
      const transfers = new Map(state.transfers);
      const existing = transfers.get(transferId);

      if (existing) {
        transfers.set(transferId, {
          ...existing,
          ...progress,
        });
      }

      return { transfers };
    });
  },

  removeTransfer: (transferId: string) => {
    set((state) => {
      const transfers = new Map(state.transfers);
      transfers.delete(transferId);
      return { transfers };
    });
  },

  addReceivedFile: (file: ReceivedFile) => {
    set((state) => {
      const receivedFiles = new Map(state.receivedFiles);
      receivedFiles.set(file.id, file);
      return { receivedFiles };
    });
  },
}));

// Listen for file transfer events
if (typeof window !== 'undefined') {
  // File progress updates
  window.addEventListener('discordopus:file_progress', ((event: CustomEvent) => {
    const { contactId, progress } = event.detail;

    if (!contactId || !progress) return;

    const store = useTransferStore.getState();
    const existing = store.transfers.get(progress.transferId);

    if (existing) {
      // Update existing transfer
      store.updateProgress(progress.transferId, {
        bytesTransferred: progress.bytesTransferred,
        totalBytes: progress.totalBytes,
        state: progress.state,
        speedBps: progress.speedBps,
        etaSeconds: progress.etaSeconds,
      });
    } else {
      // New transfer - infer direction based on state
      // (Receiving transfers start with 'pending' state)
      const direction: TransferDirection =
        progress.state === 'pending' ? 'receive' : 'send';

      store.addTransfer({
        ...progress,
        contactId,
        direction,
        filename: progress.transferId, // Will be updated when metadata arrives
      });
    }
  }) as EventListener);

  // File received (metadata)
  window.addEventListener('discordopus:file_received', ((event: CustomEvent) => {
    const { contactId, file } = event.detail;

    if (!contactId || !file) return;

    const store = useTransferStore.getState();

    // Update transfer with filename if it exists
    if (file.transferId) {
      const existing = store.transfers.get(file.transferId);
      if (existing) {
        // Update the transfer with complete metadata
        const transfers = new Map(store.transfers);
        transfers.set(file.transferId, {
          ...existing,
          filename: file.filename,
          mimeType: file.mimeType,
          totalBytes: file.size,
        });

        useTransferStore.setState({ transfers });
      }
    }

    // Add to received files
    store.addReceivedFile({
      ...file,
      contactId,
      receivedAt: Date.now(),
    });
  }) as EventListener);

  // Transfer complete
  window.addEventListener('discordopus:transfer_complete', ((event: CustomEvent) => {
    const { transferId } = event.detail;

    if (!transferId) return;

    // Remove from active transfers after a short delay (let user see 100%)
    setTimeout(() => {
      useTransferStore.getState().removeTransfer(transferId);
    }, 2000);
  }) as EventListener);

  // Transfer error
  window.addEventListener('discordopus:transfer_error', ((event: CustomEvent) => {
    const { transferId, error } = event.detail;

    if (!transferId) return;

    console.error('Transfer error:', transferId, error);

    // Update state to failed
    useTransferStore.getState().updateProgress(transferId, {
      state: 'failed',
    });

    // Remove after delay
    setTimeout(() => {
      useTransferStore.getState().removeTransfer(transferId);
    }, 5000);
  }) as EventListener);
}
