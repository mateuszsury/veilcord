/**
 * Main chat panel component with Discord-style layout.
 *
 * Displays:
 * - Header with contact info and connection status
 * - Scrollable message list
 * - Fixed input area at bottom
 * - Or GroupChatPanel when a group is selected
 */

import { useChat } from '@/stores/chat';
import { useMessages } from '@/stores/messages';
import { useContactsStore } from '@/stores/contacts';
import { useVoiceRecording } from '@/stores/voiceRecording';
import { useCall } from '@/stores/call';
import { useGroupStore } from '@/stores/groups';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';
import { FileUpload } from './FileUpload';
import { TransferProgress } from './TransferProgress';
import { ResumableTransfers } from './ResumableTransfers';
import { VoiceRecorder } from './VoiceRecorder';
import { GroupChatPanel } from '@/components/groups/GroupChatPanel';
import { Avatar } from '@/components/ui';
import { Phone, MessageSquare, Wifi, WifiOff, Loader2 } from 'lucide-react';

export function ChatPanel() {
  const { activeContactId, p2pStates, initiateConnection, typingContacts } = useChat();
  const { messagesByContact, loading, hasMore, loadMessages, sendMessage } = useMessages();
  const contacts = useContactsStore((s) => s.contacts);
  const { isRecording, startRecording, reset: resetRecording } = useVoiceRecording();
  const { startCall, state: callState } = useCall();
  const selectedGroupId = useGroupStore((s) => s.selectedGroupId);

  const contact = contacts.find((c) => c.id === activeContactId);
  const messages = activeContactId ? messagesByContact[activeContactId] || [] : [];
  const isLoading = activeContactId ? loading[activeContactId] : false;
  const canLoadMore = activeContactId ? hasMore[activeContactId] : false;
  const p2pState = activeContactId ? p2pStates[activeContactId] || 'disconnected' : 'disconnected';
  const isTyping = activeContactId ? typingContacts.has(activeContactId) : false;

  // If a group is selected, show group chat
  if (selectedGroupId) {
    return <GroupChatPanel groupId={selectedGroupId} />;
  }

  // No contact selected
  if (!activeContactId || !contact) {
    return (
      <div className="flex-1 flex items-center justify-center bg-discord-bg-primary">
        <div className="text-center text-discord-text-muted">
          <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg">Select a contact or group to start chatting</p>
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
    <div className="flex flex-col h-full bg-discord-bg-primary">
      {/* Header */}
      <header className="h-14 px-4 flex items-center justify-between border-b border-discord-bg-tertiary bg-discord-bg-primary shadow-sm">
        <div className="flex items-center gap-3">
          <Avatar name={contact.displayName} size="sm" />
          <div>
            <h2 className="text-discord-text-primary font-semibold">
              {contact.displayName}
            </h2>
            {isTyping && (
              <p className="text-sm text-accent-red animate-pulse">typing...</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Call button */}
          <button
            onClick={() => startCall(contact.id, contact.displayName)}
            disabled={callState !== 'idle' || p2pState !== 'connected'}
            className="p-2 text-discord-text-muted hover:text-discord-text-primary hover:bg-discord-bg-modifier-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title={callState !== 'idle' ? 'Call in progress' : p2pState !== 'connected' ? 'Connect first to call' : 'Start voice call'}
          >
            <Phone className="w-5 h-5" />
          </button>

          {/* Connection status */}
          {p2pState === 'connected' && (
            <div className="flex items-center gap-1 text-status-online text-sm">
              <Wifi className="w-4 h-4" />
              <span>Connected</span>
            </div>
          )}
          {p2pState === 'connecting' && (
            <div className="flex items-center gap-1 text-status-away text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Connecting...</span>
            </div>
          )}
          {p2pState === 'disconnected' && (
            <button
              onClick={handleConnect}
              className="flex items-center gap-1 text-discord-text-muted hover:text-discord-text-primary text-sm
                         px-3 py-1 rounded-lg bg-discord-bg-tertiary hover:bg-discord-bg-modifier-hover transition-colors"
            >
              <WifiOff className="w-4 h-4" />
              <span>Connect</span>
            </button>
          )}
          {p2pState === 'failed' && (
            <div className="flex items-center gap-2">
              <span className="text-status-busy text-sm">Connection failed</span>
              <button
                onClick={handleConnect}
                className="text-sm text-accent-red hover:text-accent-red/80"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Resumable transfers */}
      <ResumableTransfers contactId={activeContactId} />

      {/* Messages area */}
      <div className="flex-1 overflow-hidden">
        <MessageList
          messages={messages}
          contactId={activeContactId}
          loading={isLoading}
          hasMore={canLoadMore}
          onLoadMore={handleLoadMore}
        />
      </div>

      {/* Typing indicator */}
      {isTyping && <TypingIndicator displayName={contact.displayName} />}

      {/* Transfer progress */}
      <TransferProgress contactId={activeContactId} />

      {/* Input area */}
      <div className="p-4 bg-discord-bg-primary">
        {isRecording ? (
          // Voice recording mode
          <VoiceRecorder
            contactId={activeContactId}
            onSent={handleRecordingSent}
            onCancel={handleRecordingCancel}
          />
        ) : (
          // Normal input mode with integrated buttons
          <MessageInput
            contactId={activeContactId}
            contactName={contact.displayName}
            onSend={handleSend}
            disabled={p2pState !== 'connected'}
            onStartRecording={handleStartRecording}
            fileUploadSlot={
              <FileUpload
                contactId={activeContactId}
                disabled={p2pState !== 'connected'}
              />
            }
          />
        )}
      </div>
    </div>
  );
}
