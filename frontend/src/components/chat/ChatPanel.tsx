/**
 * Main chat panel component.
 *
 * Displays:
 * - Contact header with connection status
 * - Message list
 * - Message input
 * - Connection controls
 */

import { useChat } from '@/stores/chat';
import { useMessages } from '@/stores/messages';
import { useContactsStore } from '@/stores/contacts';
import { useVoiceRecording } from '@/stores/voiceRecording';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';
import { FileUpload } from './FileUpload';
import { TransferProgress } from './TransferProgress';
import { ResumableTransfers } from './ResumableTransfers';
import { VoiceRecorder } from './VoiceRecorder';

// SVG path for icons
const ICONS = {
  message: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  wifi: 'M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.14 0M1.394 9.393c5.857-5.858 15.355-5.858 21.213 0',
  wifiOff: 'M1 1l22 22M8.111 16.404A5.5 5.5 0 0112 15c1.24 0 2.428.41 3.396 1.164M12 20h.01',
  loader: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
  mic: 'M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z M19 10v2a7 7 0 01-14 0v-2 M12 19v4 M8 23h8',
};

function Icon({ path, className = 'w-4 h-4', spin = false }: { path: string; className?: string; spin?: boolean }) {
  return (
    <svg
      className={`${className} ${spin ? 'animate-spin' : ''}`}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={path} />
    </svg>
  );
}

export function ChatPanel() {
  const { activeContactId, p2pStates, initiateConnection, typingContacts } = useChat();
  const { messagesByContact, loading, hasMore, loadMessages, sendMessage } = useMessages();
  const contacts = useContactsStore((s) => s.contacts);
  const { isRecording, startRecording, reset: resetRecording } = useVoiceRecording();

  const contact = contacts.find((c) => c.id === activeContactId);
  const messages = activeContactId ? messagesByContact[activeContactId] || [] : [];
  const isLoading = activeContactId ? loading[activeContactId] : false;
  const canLoadMore = activeContactId ? hasMore[activeContactId] : false;
  const p2pState = activeContactId ? p2pStates[activeContactId] || 'disconnected' : 'disconnected';
  const isTyping = activeContactId ? typingContacts.has(activeContactId) : false;

  // No contact selected
  if (!activeContactId || !contact) {
    return (
      <div className="flex-1 flex items-center justify-center bg-cosmic-bg/50">
        <div className="text-center text-cosmic-muted">
          <Icon path={ICONS.message} className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg">Select a contact to start chatting</p>
        </div>
      </div>
    );
  }

  const handleConnect = () => {
    if (activeContactId && p2pState === 'disconnected') {
      initiateConnection(activeContactId);
    }
  };

  const handleSend = async (body: string) => {
    if (!activeContactId) return false;
    return sendMessage(activeContactId, body);
  };

  const handleLoadMore = () => {
    if (!activeContactId || !messages.length) return;
    const oldestTimestamp = messages[0]?.timestamp;
    loadMessages(activeContactId, oldestTimestamp);
  };

  const handleStartRecording = async () => {
    await startRecording();
  };

  const handleRecordingSent = () => {
    resetRecording();
  };

  const handleRecordingCancel = () => {
    resetRecording();
  };

  return (
    <div className="flex-1 flex flex-col bg-cosmic-bg/50">
      {/* Header */}
      <div className="border-b border-cosmic-border p-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-cosmic-text">
            {contact.displayName}
          </h2>
          {isTyping && (
            <p className="text-sm text-cosmic-accent animate-pulse">typing...</p>
          )}
        </div>

        {/* Connection status */}
        <div className="flex items-center gap-2">
          {p2pState === 'connected' && (
            <div className="flex items-center gap-1 text-green-400 text-sm">
              <Icon path={ICONS.wifi} />
              <span>Connected</span>
            </div>
          )}
          {p2pState === 'connecting' && (
            <div className="flex items-center gap-1 text-yellow-400 text-sm">
              <Icon path={ICONS.loader} spin />
              <span>Connecting...</span>
            </div>
          )}
          {p2pState === 'disconnected' && (
            <button
              onClick={handleConnect}
              className="flex items-center gap-1 text-cosmic-muted hover:text-cosmic-text text-sm
                         px-3 py-1 rounded-lg bg-cosmic-surface hover:bg-cosmic-border transition-colors"
            >
              <Icon path={ICONS.wifiOff} />
              <span>Connect</span>
            </button>
          )}
          {p2pState === 'failed' && (
            <div className="flex items-center gap-2">
              <span className="text-red-400 text-sm">Connection failed</span>
              <button
                onClick={handleConnect}
                className="text-sm text-cosmic-accent hover:text-cosmic-accent/80"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Resumable transfers */}
      <ResumableTransfers contactId={activeContactId} />

      {/* Messages */}
      <MessageList
        messages={messages}
        contactId={activeContactId}
        loading={isLoading}
        hasMore={canLoadMore}
        onLoadMore={handleLoadMore}
      />

      {/* Typing indicator */}
      {isTyping && <TypingIndicator displayName={contact.displayName} />}

      {/* Transfer progress */}
      <TransferProgress contactId={activeContactId} />

      {/* Input area with file upload and voice recording */}
      <div className="border-t border-cosmic-border p-4">
        {isRecording ? (
          // Voice recording mode
          <VoiceRecorder
            contactId={activeContactId}
            onSent={handleRecordingSent}
            onCancel={handleRecordingCancel}
          />
        ) : (
          // Normal input mode
          <div className="flex items-end gap-2">
            <FileUpload
              contactId={activeContactId}
              disabled={p2pState !== 'connected'}
            />
            <button
              type="button"
              onClick={handleStartRecording}
              disabled={p2pState !== 'connected'}
              className="p-2 text-cosmic-muted hover:text-cosmic-text hover:bg-cosmic-surface rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Record voice message"
            >
              <Icon path={ICONS.mic} className="w-5 h-5" />
            </button>
            <MessageInput
              contactId={activeContactId}
              onSend={handleSend}
              disabled={p2pState !== 'connected'}
            />
          </div>
        )}
      </div>
    </div>
  );
}
