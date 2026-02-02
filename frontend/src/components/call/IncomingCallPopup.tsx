/**
 * Incoming call notification popup.
 *
 * Shows when state is 'ringing_incoming' with caller info
 * and accept/reject buttons in Discord style.
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Phone, PhoneOff } from 'lucide-react';
import { useCall } from '@/stores/call';
import { useContactsStore } from '@/stores/contacts';

export function IncomingCallPopup() {
  const { state, callInfo, acceptCall, rejectCall } = useCall();
  const { contacts } = useContactsStore();

  // Only show for incoming calls
  if (state !== 'ringing_incoming' || !callInfo) {
    return null;
  }

  // Find contact name
  const contact = contacts.find((c) => c.id === callInfo.contactId);
  const callerName = callInfo.contactName || contact?.displayName || 'Unknown';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[3000] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          className="w-80 bg-discord-bg-secondary rounded-lg shadow-xl border border-discord-bg-tertiary overflow-hidden"
        >
          {/* Content */}
          <div className="p-8 flex flex-col items-center">
            {/* Caller avatar with pulse ring */}
            <div className="relative mb-6">
              {/* Pulse rings */}
              <div className="absolute inset-0 -m-3">
                <div className="w-[calc(100%+24px)] h-[calc(100%+24px)] rounded-full border-2 border-status-online/30 animate-ping" />
              </div>
              <div className="absolute inset-0 -m-1.5">
                <div
                  className="w-[calc(100%+12px)] h-[calc(100%+12px)] rounded-full border-2 border-status-online/50 animate-ping"
                  style={{ animationDelay: '150ms' }}
                />
              </div>
              {/* Avatar */}
              <div className="relative w-20 h-20 rounded-full bg-accent-red/50 flex items-center justify-center text-3xl font-medium text-white">
                {callerName.charAt(0).toUpperCase()}
              </div>
            </div>

            {/* Caller info */}
            <div className="text-center mb-8">
              <p className="text-lg font-medium text-discord-text-primary mb-1">{callerName}</p>
              <p className="text-discord-text-muted flex items-center justify-center gap-2">
                <span className="inline-block w-2 h-2 bg-status-online rounded-full animate-pulse" />
                Incoming call...
              </p>
            </div>

            {/* Action buttons */}
            <div className="flex justify-center gap-8">
              {/* Reject button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => rejectCall()}
                className="w-14 h-14 rounded-full bg-status-busy hover:brightness-110 flex items-center justify-center transition-colors shadow-lg"
                title="Reject call"
              >
                <PhoneOff size={24} className="text-white" />
              </motion.button>

              {/* Accept button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => acceptCall()}
                className="w-14 h-14 rounded-full bg-status-online hover:brightness-110 flex items-center justify-center transition-colors shadow-lg"
                title="Accept call"
              >
                <Phone size={24} className="text-white" />
              </motion.button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
