/**
 * Group chat panel component.
 *
 * Displays:
 * - Group header with name and member count
 * - Group call controls
 * - Message list from group members
 * - Message input
 * - Member sidebar
 */

import { useState, useRef, useEffect } from 'react';
import { useGroupStore } from '@/stores/groups';
import { useGroupMessagesStore } from '@/stores/groupMessages';
import { useIdentityStore } from '@/stores/identity';
import { GroupHeader } from './GroupHeader';
import { GroupMemberList } from './GroupMemberList';
import { GroupCallControls } from './GroupCallControls';

interface Props {
  groupId: string;
}

export function GroupChatPanel({ groupId }: Props) {
  const [input, setInput] = useState('');
  const [showMembers, setShowMembers] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const groups = useGroupStore((s) => s.groups);
  const members = useGroupStore((s) => s.members.get(groupId) || []);
  const messages = useGroupMessagesStore((s) => s.messages.get(groupId) || []);
  const sendMessage = useGroupMessagesStore((s) => s.sendMessage);
  const identity = useIdentityStore((s) => s.identity);

  const group = groups.find((g) => g.id === groupId);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  // Get display name for a public key
  const getDisplayName = (publicKey: string): string => {
    if (publicKey === 'self' || publicKey === identity?.publicKey) {
      return 'You';
    }
    const member = members.find((m) => m.public_key === publicKey);
    return member?.display_name || publicKey.slice(0, 8) + '...';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;

    setInput('');
    try {
      await sendMessage(groupId, text);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  if (!group) {
    return (
      <div className="flex-1 flex items-center justify-center text-discord-text-muted">
        Group not found
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-discord-bg-primary/50">
      <GroupHeader groupId={groupId} />

      <div className="flex-1 flex min-h-0 relative">
        {/* Chat area */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Call controls */}
          <GroupCallControls groupId={groupId} />

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 ? (
              <div className="text-center text-discord-text-muted py-8">
                No messages yet. Start the conversation!
              </div>
            ) : (
              messages.map((message) => {
                const isOwn = message.sender_public_key === 'self' ||
                  message.sender_public_key === identity?.publicKey;

                return (
                  <div
                    key={message.id}
                    className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-lg px-4 py-2 ${
                        isOwn
                          ? 'bg-accent-red text-white'
                          : 'bg-discord-bg-secondary text-discord-text-primary'
                      }`}
                    >
                      {!isOwn && (
                        <div className="text-xs text-accent-red-text mb-1">
                          {getDisplayName(message.sender_public_key)}
                        </div>
                      )}
                      <p className="break-words">{message.body}</p>
                      <div className="flex items-center justify-end gap-1 mt-1">
                        <span className="text-xs opacity-60">
                          {new Date(message.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                        {isOwn && message.status === 'sending' && (
                          <span className="text-xs opacity-60">...</span>
                        )}
                        {isOwn && message.status === 'failed' && (
                          <span className="text-xs text-red-400">!</span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-4 border-t border-discord-bg-tertiary">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 px-4 py-2 bg-discord-bg-secondary border border-discord-bg-tertiary rounded-lg text-discord-text-primary placeholder-discord-text-muted focus:outline-none focus:border-accent-red"
              />
              <button
                type="submit"
                disabled={!input.trim()}
                className="px-4 py-2 bg-accent-red hover:bg-accent-red-hover disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                Send
              </button>
            </div>
          </form>
        </div>

        {/* Members sidebar toggle */}
        {!showMembers && (
          <button
            onClick={() => setShowMembers(true)}
            className="absolute right-0 top-1/2 -translate-y-1/2 p-1 bg-discord-bg-secondary hover:bg-discord-bg-modifier-hover rounded-l text-discord-text-muted"
            title="Show members"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}

        {/* Members sidebar */}
        {showMembers && (
          <div className="relative">
            <button
              onClick={() => setShowMembers(false)}
              className="absolute left-2 top-2 p-1 hover:bg-discord-bg-modifier-hover rounded text-discord-text-muted z-10"
              title="Hide members"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <GroupMemberList groupId={groupId} />
          </div>
        )}
      </div>
    </div>
  );
}
