/**
 * Discord/Zoom-style call controls bar.
 *
 * Center bottom bar with:
 * - Mute/Unmute mic
 * - Toggle camera
 * - Share screen
 * - Effects toggle
 * - End call
 */

import { motion } from 'framer-motion';
import { Mic, MicOff, Video, VideoOff, Monitor, Sparkles, PhoneOff } from 'lucide-react';

export interface CallControlsProps {
  isMuted: boolean;
  onMuteToggle: () => void;
  isVideoOn: boolean;
  onVideoToggle: () => void;
  isScreenSharing: boolean;
  onScreenShareToggle: () => void;
  onEffectsToggle: () => void;
  onEndCall: () => void;
  showEffects?: boolean;
}

export function CallControls({
  isMuted,
  onMuteToggle,
  isVideoOn,
  onVideoToggle,
  isScreenSharing,
  onScreenShareToggle,
  onEffectsToggle,
  onEndCall,
  showEffects = false,
}: CallControlsProps) {
  return (
    <div className="flex items-center justify-center gap-2 px-4 py-3 bg-discord-bg-secondary/90 backdrop-blur rounded-full shadow-lg">
      {/* Mute/Unmute mic */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onMuteToggle}
        className={`w-11 h-11 rounded-full flex items-center justify-center transition-colors ${
          isMuted
            ? 'bg-accent-red/20 text-accent-red-text'
            : 'bg-discord-bg-tertiary text-discord-text-primary hover:bg-discord-bg-modifier-hover'
        }`}
        title={isMuted ? 'Unmute' : 'Mute'}
      >
        {isMuted ? <MicOff size={20} /> : <Mic size={20} />}
      </motion.button>

      {/* Toggle camera */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onVideoToggle}
        className={`w-11 h-11 rounded-full flex items-center justify-center transition-colors ${
          !isVideoOn
            ? 'bg-accent-red/20 text-accent-red-text'
            : 'bg-discord-bg-tertiary text-discord-text-primary hover:bg-discord-bg-modifier-hover'
        }`}
        title={isVideoOn ? 'Turn off camera' : 'Turn on camera'}
      >
        {isVideoOn ? <Video size={20} /> : <VideoOff size={20} />}
      </motion.button>

      {/* Share screen */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onScreenShareToggle}
        className={`w-11 h-11 rounded-full flex items-center justify-center transition-colors ${
          isScreenSharing
            ? 'bg-status-online text-white'
            : 'bg-discord-bg-tertiary text-discord-text-primary hover:bg-discord-bg-modifier-hover'
        }`}
        title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
      >
        <Monitor size={20} />
      </motion.button>

      {/* Effects toggle */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onEffectsToggle}
        className={`w-11 h-11 rounded-full flex items-center justify-center transition-colors ${
          showEffects
            ? 'bg-accent-red text-white'
            : 'bg-discord-bg-tertiary text-discord-text-primary hover:bg-discord-bg-modifier-hover'
        }`}
        title="Effects"
      >
        <Sparkles size={20} />
      </motion.button>

      {/* End call */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onEndCall}
        className="w-11 h-11 rounded-full bg-status-busy text-white flex items-center justify-center transition-colors hover:brightness-110"
        title="End call"
      >
        <PhoneOff size={20} />
      </motion.button>
    </div>
  );
}
