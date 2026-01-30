/**
 * Active call overlay.
 *
 * Shows during active/connecting calls with:
 * - Contact name
 * - Call duration timer
 * - Mute button
 * - End call button
 */

import { useEffect, useState } from 'react';
import { useCall } from '@/stores/call';
import { useContactsStore } from '@/stores/contacts';

export function ActiveCallOverlay() {
  const { state, callInfo, muted, toggleMute, endCall } = useCall();
  const { contacts } = useContactsStore();
  const [displayDuration, setDisplayDuration] = useState(0);

  // Update duration every second when active
  useEffect(() => {
    if (state !== 'active') {
      setDisplayDuration(0);
      return;
    }

    const interval = setInterval(() => {
      setDisplayDuration((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [state]);

  // Only show for connecting, active, reconnecting, or outgoing ring states
  const showOverlay =
    state === 'connecting' ||
    state === 'active' ||
    state === 'reconnecting' ||
    state === 'ringing_outgoing';

  if (!showOverlay || !callInfo) {
    return null;
  }

  // Find contact name
  const contact = contacts.find((c) => c.id === callInfo.contactId);
  const contactName = callInfo.contactName || contact?.displayName || 'Unknown';

  // Format duration as MM:SS
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Get status text based on call state
  const getStatusText = () => {
    switch (state) {
      case 'ringing_outgoing':
        return 'Ringing...';
      case 'connecting':
        return 'Connecting...';
      case 'reconnecting':
        return 'Reconnecting...';
      case 'active':
        return formatDuration(displayDuration);
      default:
        return '';
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-40">
      <div className="bg-slate-800/95 backdrop-blur rounded-2xl p-4 shadow-2xl border border-slate-700 min-w-[280px]">
        {/* Header with avatar and info */}
        <div className="flex items-center gap-3 mb-4">
          {/* Avatar placeholder with initial */}
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
            <span className="text-white font-semibold text-lg">
              {contactName.charAt(0).toUpperCase()}
            </span>
          </div>

          <div className="flex-1">
            <p className="text-white font-medium">{contactName}</p>
            <p className="text-slate-400 text-sm">{getStatusText()}</p>
          </div>

          {/* Audio wave indicator (only when active) */}
          {state === 'active' && (
            <div className="flex items-center gap-0.5">
              <div className="w-1 h-3 bg-green-400 rounded animate-pulse" />
              <div
                className="w-1 h-5 bg-green-400 rounded animate-pulse"
                style={{ animationDelay: '75ms' }}
              />
              <div
                className="w-1 h-4 bg-green-400 rounded animate-pulse"
                style={{ animationDelay: '150ms' }}
              />
            </div>
          )}
        </div>

        {/* Call controls */}
        <div className="flex justify-center gap-4">
          {/* Mute button */}
          <button
            onClick={() => toggleMute()}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
              muted
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
            title={muted ? 'Unmute' : 'Mute'}
          >
            {muted ? (
              // Muted icon (speaker with X)
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
                />
              </svg>
            ) : (
              // Microphone icon
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </svg>
            )}
          </button>

          {/* End call button */}
          <button
            onClick={() => endCall()}
            className="w-12 h-12 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center transition-colors"
            title="End call"
          >
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
