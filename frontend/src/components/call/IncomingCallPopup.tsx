/**
 * Incoming call notification popup.
 *
 * Shows when state is 'ringing_incoming' with caller info
 * and accept/reject buttons.
 */

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-slate-800 rounded-2xl p-8 shadow-2xl border border-slate-700 max-w-sm w-full mx-4">
        {/* Phone icon with pulse animation */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center animate-pulse">
            <svg
              className="w-10 h-10 text-green-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
              />
            </svg>
          </div>
        </div>

        {/* Caller info */}
        <div className="text-center mb-8">
          <h2 className="text-xl font-semibold text-white mb-1">Incoming Call</h2>
          <p className="text-slate-300 text-lg">{callerName}</p>
        </div>

        {/* Action buttons */}
        <div className="flex justify-center gap-6">
          {/* Reject button */}
          <button
            onClick={() => rejectCall()}
            className="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center transition-colors shadow-lg"
            title="Reject call"
          >
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>

          {/* Accept button */}
          <button
            onClick={() => acceptCall()}
            className="w-16 h-16 rounded-full bg-green-500 hover:bg-green-600 flex items-center justify-center transition-colors shadow-lg"
            title="Accept call"
          >
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
