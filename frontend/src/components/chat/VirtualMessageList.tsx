/**
 * Virtualized message list using TanStack Virtual.
 *
 * Features:
 * - Virtual scrolling for smooth performance with 1000+ messages
 * - Auto-scroll to bottom on new messages
 * - Loading skeletons with Discord colors
 * - Empty state display
 * - Load more button at top
 * - Dynamic height measurement for variable message sizes
 */

import { useEffect, useRef } from 'react';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import { useVirtualScroll } from '@/hooks/useVirtualScroll';
import { MessageBubble } from './MessageBubble';
import type { Message } from '@/stores/messages';

interface VirtualMessageListProps {
  messages: Message[];
  contactId: number;
  loading?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
}

export function VirtualMessageList({
  messages,
  contactId,
  loading = false,
  hasMore = false,
  onLoadMore,
}: VirtualMessageListProps) {
  const prevLength = useRef(messages.length);

  const {
    parentRef,
    virtualizer,
    virtualItems,
    totalSize,
    scrollToBottom,
  } = useVirtualScroll({
    items: messages,
    estimateSize: 80,
    overscan: 10,
    getItemKey: (index) => messages[index]?.id || index,
  });

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > prevLength.current) {
      // New message added
      scrollToBottom();
    }
    prevLength.current = messages.length;
  }, [messages.length, scrollToBottom]);

  // Scroll to bottom on initial load
  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom('auto');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Loading skeleton
  if (loading && messages.length === 0) {
    return (
      <div className="flex-1 p-4 space-y-4 h-full">
        {Array(5).fill(0).map((_, i) => (
          <MessageSkeleton key={i} />
        ))}
      </div>
    );
  }

  // Empty state
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-discord-text-muted h-full">
        <div className="text-center">
          <p className="text-lg">No messages yet</p>
          <p className="text-sm mt-1">Send a message to start the conversation</p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={parentRef}
      className="flex-1 overflow-y-auto h-full"
    >
      {/* Load more button */}
      {hasMore && (
        <div className="flex justify-center py-4">
          <button
            onClick={onLoadMore}
            disabled={loading}
            className="text-sm text-discord-text-link hover:underline disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Load earlier messages'}
          </button>
        </div>
      )}

      {/* Virtual container */}
      <div
        style={{
          height: `${totalSize}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualRow) => {
          const message = messages[virtualRow.index];
          if (!message) return null;
          return (
            <div
              key={virtualRow.key}
              data-index={virtualRow.index}
              ref={virtualizer.measureElement}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <MessageBubble
                message={message}
                isOwn={message.sender_id === 'self'}
                contactId={contactId}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Message skeleton for loading state.
 * Uses Discord theme colors.
 */
function MessageSkeleton() {
  return (
    <div className="flex gap-4 px-2 py-1">
      <Skeleton
        circle
        width={40}
        height={40}
        baseColor="#313338"
        highlightColor="#3f4147"
      />
      <div className="flex-1">
        <Skeleton
          width="30%"
          height={16}
          baseColor="#313338"
          highlightColor="#3f4147"
        />
        <Skeleton
          count={2}
          height={14}
          className="mt-2"
          baseColor="#313338"
          highlightColor="#3f4147"
        />
      </div>
    </div>
  );
}
