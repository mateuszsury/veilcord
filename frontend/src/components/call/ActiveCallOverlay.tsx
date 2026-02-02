/**
 * Active call overlay.
 *
 * Shows during active/connecting calls with:
 * - Contact avatar and name
 * - Call duration timer
 * - Video display (local and remote)
 * - Discord-style CallControls bar
 * - Expandable EffectsPanel
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCall } from '@/stores/call';
import { useContactsStore } from '@/stores/contacts';
import { Avatar } from '@/components/ui/Avatar';
import { VideoPlayer } from './VideoPlayer';
import { LocalPreview } from './LocalPreview';
import { ScreenPicker } from './ScreenPicker';
import { CallControls } from './CallControls';
import { EffectsPanel } from './EffectsPanel';

export function ActiveCallOverlay() {
  const {
    state,
    callInfo,
    muted,
    toggleMute,
    endCall,
    videoEnabled,
    videoSource,
    remoteVideo,
    enableVideo,
    disableVideo,
  } = useCall();
  const { contacts } = useContactsStore();
  const [displayDuration, setDisplayDuration] = useState(0);
  const [showScreenPicker, setShowScreenPicker] = useState(false);
  const [showEffects, setShowEffects] = useState(false);

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

  // Determine if we should show the expanded video overlay
  const showVideoOverlay = remoteVideo || videoEnabled;

  // Handler for camera toggle
  const handleCameraToggle = async () => {
    if (videoEnabled && videoSource === 'camera') {
      await disableVideo();
    } else {
      await enableVideo('camera');
    }
  };

  // Handler for screen share toggle
  const handleScreenShareToggle = () => {
    if (videoEnabled && videoSource === 'screen') {
      disableVideo();
    } else {
      setShowScreenPicker(true);
    }
  };

  // Handler for screen selection from picker
  const handleScreenSelect = async () => {
    await enableVideo('screen');
  };

  const isCameraOn = videoEnabled && videoSource === 'camera';
  const isScreenSharing = videoEnabled && videoSource === 'screen';

  return (
    <>
      {/* Screen Picker Dialog */}
      <ScreenPicker
        isOpen={showScreenPicker}
        onClose={() => setShowScreenPicker(false)}
        onSelect={handleScreenSelect}
      />

      {/* Main Overlay - Corner positioned */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        className={`fixed bottom-4 right-4 bg-discord-bg-secondary rounded-lg shadow-xl z-[3000] overflow-hidden ${
          showVideoOverlay ? 'w-[480px]' : 'w-80'
        }`}
      >
        {/* Header with caller info */}
        <div className="p-4 border-b border-discord-bg-tertiary">
          <div className="flex items-center gap-3">
            <Avatar name={contactName} size="md" />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-discord-text-primary truncate">{contactName}</p>
              <p className="text-sm text-discord-text-muted">{getStatusText()}</p>
            </div>
            {/* Audio wave indicator (only when active) */}
            {state === 'active' && (
              <div className="flex items-center gap-0.5">
                <div className="w-1 h-3 bg-status-online rounded animate-pulse" />
                <div
                  className="w-1 h-5 bg-status-online rounded animate-pulse"
                  style={{ animationDelay: '75ms' }}
                />
                <div
                  className="w-1 h-4 bg-status-online rounded animate-pulse"
                  style={{ animationDelay: '150ms' }}
                />
              </div>
            )}
          </div>
        </div>

        {/* Video area (if video enabled) */}
        {showVideoOverlay && (
          <div className="relative aspect-video bg-discord-bg-primary">
            {remoteVideo ? (
              <VideoPlayer type="remote" className="w-full h-full" />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                {/* Fallback avatar display when no remote video */}
                <div className="text-center">
                  <Avatar name={contactName} size="lg" className="mx-auto mb-3" />
                  <p className="text-discord-text-muted text-sm">Camera off</p>
                </div>
              </div>
            )}

            {/* Local preview overlay */}
            <LocalPreview />
          </div>
        )}

        {/* Controls */}
        <div className="p-4 flex justify-center relative">
          <CallControls
            isMuted={muted}
            onMuteToggle={() => toggleMute()}
            isVideoOn={isCameraOn}
            onVideoToggle={handleCameraToggle}
            isScreenSharing={isScreenSharing}
            onScreenShareToggle={handleScreenShareToggle}
            onEffectsToggle={() => setShowEffects(!showEffects)}
            onEndCall={() => endCall()}
            showEffects={showEffects}
          />
          <AnimatePresence>
            {showEffects && (
              <EffectsPanel
                isOpen={showEffects}
                onClose={() => setShowEffects(false)}
                isVideoEnabled={videoEnabled}
              />
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </>
  );
}
