/**
 * Group call controls component.
 *
 * Displays:
 * - Start call button (when not in call)
 * - Leave call and mute buttons (when in call)
 * - Member count and bandwidth warning
 */

import { useState } from 'react';
import { useGroupStore } from '@/stores/groups';

interface Props {
  groupId: string;
}

export function GroupCallControls({ groupId }: Props) {
  const [loading, setLoading] = useState(false);
  const [muted, setMuted] = useState(false);

  const members = useGroupStore((s) => s.members.get(groupId) || []);
  const activeGroupCall = useGroupStore((s) => s.activeGroupCall);
  const startGroupCall = useGroupStore((s) => s.startGroupCall);
  const leaveGroupCall = useGroupStore((s) => s.leaveGroupCall);
  const setGroupCallMuted = useGroupStore((s) => s.setGroupCallMuted);

  const isInCall = activeGroupCall === groupId;
  const participantCount = members.length;

  const handleStartCall = async () => {
    if (participantCount > 8) {
      alert('Maximum 8 participants allowed for group calls');
      return;
    }

    if (participantCount > 4) {
      const proceed = confirm(
        `Group calls with ${participantCount} participants may experience quality degradation. Continue?`
      );
      if (!proceed) return;
    }

    setLoading(true);
    try {
      const callId = crypto.randomUUID();
      await startGroupCall(groupId, callId);
    } catch (err) {
      alert(`Failed to start call: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveCall = async () => {
    try {
      await leaveGroupCall(groupId);
    } catch (err) {
      console.error('Failed to leave call:', err);
    }
  };

  const handleToggleMute = async () => {
    const newMuted = !muted;
    setMuted(newMuted);
    try {
      await setGroupCallMuted(groupId, newMuted);
    } catch (err) {
      setMuted(!newMuted);  // Revert on error
    }
  };

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-discord-bg-secondary/50 border-b border-discord-bg-tertiary">
      <div className="text-sm text-discord-text-muted">
        {isInCall ? (
          <span className="text-green-400">In group call</span>
        ) : (
          <span>{participantCount} members</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {isInCall ? (
          <>
            <button
              onClick={handleToggleMute}
              className={`p-2 rounded-full transition-colors ${
                muted
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-discord-bg-secondary hover:bg-discord-bg-modifier-hover text-discord-text-primary'
              }`}
              title={muted ? 'Unmute' : 'Mute'}
            >
              {muted ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>

            <button
              onClick={handleLeaveCall}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded transition-colors text-sm"
            >
              Leave Call
            </button>
          </>
        ) : (
          <button
            onClick={handleStartCall}
            disabled={loading || participantCount < 2}
            className="flex items-center gap-2 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            {loading ? 'Starting...' : 'Start Call'}
          </button>
        )}
      </div>
    </div>
  );
}
