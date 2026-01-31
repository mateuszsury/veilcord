/**
 * Screen picker dialog for selecting monitor to share.
 *
 * Shows available monitors with their resolution and position.
 * User can select a monitor to start screen sharing.
 */

import { useEffect, useState } from 'react';
import { api } from '@/lib/pywebview';
import { useCall } from '@/stores/call';
import type { Monitor } from '@/lib/pywebview';

interface ScreenPickerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (monitorIndex: number) => void;
}

export function ScreenPicker({ isOpen, onClose, onSelect }: ScreenPickerProps) {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(false);
  const { selectedMonitor, setSelectedMonitor } = useCall();

  useEffect(() => {
    if (isOpen) {
      loadMonitors();
    }
  }, [isOpen]);

  // Handle ESC key to close
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const loadMonitors = async () => {
    setLoading(true);
    try {
      const result = await api.call((a) => a.get_monitors());
      if (!result.error && result.monitors) {
        // Filter out monitor 0 (all screens combined) for simplicity
        setMonitors(result.monitors.filter((m) => m.index > 0));
      }
    } catch (error) {
      console.error('Failed to load monitors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (index: number) => {
    try {
      await api.call((a) => a.set_screen_monitor(index));
      setSelectedMonitor(index);
      onSelect(index);
      onClose();
    } catch (error) {
      console.error('Failed to set screen monitor:', error);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center"
      onClick={handleBackdropClick}
    >
      <div className="bg-cosmic-surface rounded-xl border border-cosmic-border p-6 max-w-xl w-full mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-cosmic-text flex items-center gap-2">
            {/* Monitor icon */}
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            Select Screen to Share
          </h2>

          {/* Close button */}
          <button
            onClick={onClose}
            className="text-cosmic-muted hover:text-cosmic-text transition-colors p-1"
          >
            <svg
              className="w-6 h-6"
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
        </div>

        {/* Content */}
        {loading ? (
          <div className="text-center py-8">
            <p className="text-cosmic-muted">Loading monitors...</p>
          </div>
        ) : monitors.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-cosmic-muted">No monitors detected</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {monitors.map((monitor) => (
              <button
                key={monitor.index}
                onClick={() => handleSelect(monitor.index)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedMonitor === monitor.index
                    ? 'border-cosmic-accent bg-cosmic-accent/10'
                    : 'border-cosmic-border hover:border-cosmic-accent/50 bg-cosmic-bg'
                }`}
              >
                {/* Monitor visual representation */}
                <div className="aspect-video bg-cosmic-surface rounded border border-cosmic-border mb-3 flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-cosmic-muted"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                </div>

                {/* Monitor info */}
                <div className="text-left">
                  <p className="font-medium text-cosmic-text">
                    Monitor {monitor.index}
                    {monitor.index === 1 && (
                      <span className="text-xs text-cosmic-accent ml-2">
                        Primary
                      </span>
                    )}
                  </p>
                  <p className="text-sm text-cosmic-muted">
                    {monitor.width} x {monitor.height}
                  </p>
                  {monitors.length > 1 && (
                    <p className="text-xs text-cosmic-muted mt-1">
                      Position: ({monitor.left}, {monitor.top})
                    </p>
                  )}
                </div>

                {/* Selected indicator */}
                {selectedMonitor === monitor.index && (
                  <div className="mt-2 flex items-center gap-1 text-cosmic-accent text-sm">
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Selected
                  </div>
                )}
              </button>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-cosmic-muted hover:text-cosmic-text transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
