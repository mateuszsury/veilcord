/**
 * Update prompt banner/modal.
 *
 * Displays when an update is available with:
 * - Version info and changelog
 * - Download & Install button
 * - Dismiss option
 */

import { useState, useEffect } from 'react';
import { api } from '@/lib/pywebview';
import type { UpdateInfo, UpdateAvailableEventPayload } from '@/lib/pywebview';

export function UpdatePrompt() {
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [downloadComplete, setDownloadComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Listen for update available event from backend
    const handleUpdateAvailable = (event: CustomEvent<UpdateAvailableEventPayload>) => {
      const { version } = event.detail;
      console.log('Update available:', version);
      // Fetch full update info
      fetchUpdateInfo();
    };

    window.addEventListener('discordopus:update_available', handleUpdateAvailable);

    // Also check on mount (in case event was missed)
    checkForUpdate();

    return () => {
      window.removeEventListener('discordopus:update_available', handleUpdateAvailable);
    };
  }, []);

  async function checkForUpdate() {
    try {
      const status = await api.call((a) => a.get_update_status());
      if (status.updateAvailable && status.availableUpdate) {
        setUpdateInfo(status.availableUpdate);
      }
    } catch (err) {
      console.error('Failed to check update status:', err);
    }
  }

  async function fetchUpdateInfo() {
    try {
      const info = await api.call((a) => a.check_for_updates());
      if (info) {
        setUpdateInfo(info);
      }
    } catch (err) {
      console.error('Failed to fetch update info:', err);
    }
  }

  async function handleDownload() {
    setDownloading(true);
    setError(null);

    try {
      const result = await api.call((a) => a.download_update());
      if (result.success) {
        setDownloadComplete(true);
      } else {
        setError(result.error || 'Download failed');
      }
    } catch (err) {
      setError('Failed to download update');
      console.error('Download error:', err);
    } finally {
      setDownloading(false);
    }
  }

  function handleDismiss() {
    setDismissed(true);
  }

  // Don't render if no update or dismissed
  if (!updateInfo || dismissed) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-purple-900/90 to-indigo-900/90 border-b border-purple-500/30 backdrop-blur-sm">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Update icon */}
          <div className="w-10 h-10 rounded-full bg-purple-600/30 flex items-center justify-center">
            <svg
              className="w-5 h-5 text-purple-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
              />
            </svg>
          </div>

          <div>
            <p className="text-white font-medium">
              Update Available: v{updateInfo.version}
            </p>
            <p className="text-sm text-purple-200/70">
              {updateInfo.changelog || 'New version available with improvements and fixes.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {error && (
            <span className="text-red-400 text-sm">{error}</span>
          )}

          {downloadComplete ? (
            <span className="text-green-400 text-sm">
              Update ready! Restart app to apply.
            </span>
          ) : (
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-800 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
            >
              {downloading ? (
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Downloading...
                </span>
              ) : (
                'Download & Install'
              )}
            </button>
          )}

          <button
            onClick={handleDismiss}
            className="p-2 text-purple-300 hover:text-white transition-colors"
            title="Dismiss"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
