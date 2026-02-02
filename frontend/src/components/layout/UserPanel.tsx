import { useState, useEffect } from 'react';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { Avatar } from '@/components/ui/Avatar';
import { useNetworkStore } from '@/stores/network';
import { api, type IdentityResponse } from '@/lib/pywebview';
import type { StatusType } from '@/components/ui/Badge';

// Map UserStatus to StatusType for Avatar component
function mapStatus(status: string): StatusType {
  switch (status) {
    case 'online':
      return 'online';
    case 'away':
      return 'away';
    case 'busy':
      return 'busy';
    case 'invisible':
    case 'offline':
    case 'unknown':
    default:
      return 'offline';
  }
}

export function UserPanel() {
  const [identity, setIdentity] = useState<IdentityResponse | null>(null);
  const [isMicMuted, setIsMicMuted] = useState(false);
  const [isSpeakerMuted, setIsSpeakerMuted] = useState(false);

  const userStatus = useNetworkStore((s) => s.userStatus);

  // Load identity on mount
  useEffect(() => {
    api.call((a) => a.get_identity()).then((id) => {
      if (id) {
        setIdentity(id);
      }
    });
  }, []);

  const displayName = identity?.displayName ?? 'User';
  const status = mapStatus(userStatus);

  return (
    <div className="w-full p-2 bg-discord-bg-secondary rounded-t-lg flex flex-col items-center gap-2">
      {/* User Avatar */}
      <Avatar
        name={displayName}
        size="md"
        status={status}
      />

      {/* Display Name (truncated) */}
      <span className="text-xs text-discord-text-primary truncate max-w-[72px] text-center">
        {displayName}
      </span>

      {/* Audio Controls Row */}
      <div className="flex items-center gap-1">
        {/* Mic Toggle */}
        <button
          onClick={() => setIsMicMuted(!isMicMuted)}
          className={`
            w-8 h-8
            flex items-center justify-center
            rounded-lg
            transition-colors
            hover:bg-discord-bg-tertiary
            focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-red
            ${isMicMuted ? 'text-accent-red' : 'text-discord-text-secondary'}
          `.trim().replace(/\s+/g, ' ')}
          aria-label={isMicMuted ? 'Unmute microphone' : 'Mute microphone'}
        >
          {isMicMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>

        {/* Speaker Toggle */}
        <button
          onClick={() => setIsSpeakerMuted(!isSpeakerMuted)}
          className={`
            w-8 h-8
            flex items-center justify-center
            rounded-lg
            transition-colors
            hover:bg-discord-bg-tertiary
            focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-red
            ${isSpeakerMuted ? 'text-accent-red' : 'text-discord-text-secondary'}
          `.trim().replace(/\s+/g, ' ')}
          aria-label={isSpeakerMuted ? 'Unmute speaker' : 'Mute speaker'}
        >
          {isSpeakerMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
}
