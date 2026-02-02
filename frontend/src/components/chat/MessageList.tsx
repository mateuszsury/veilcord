/**
 * Discord-style scrollable message list with virtual scrolling.
 *
 * This is a wrapper around VirtualMessageList that maintains
 * the existing interface while enabling virtual scrolling for
 * smooth performance with 1000+ messages.
 *
 * Features:
 * - Virtual scrolling (only renders visible messages)
 * - Auto-scroll when new messages arrive
 * - Scroll-to-bottom on initial load
 * - Loading skeletons
 * - Empty state when no messages
 * - Discord-style message display
 */

import { useMemo } from 'react';
import { VirtualMessageList } from './VirtualMessageList';
import type { Message } from '@/stores/messages';

interface MessageListProps {
  messages: Message[];
  contactId: number;
  loading?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
}

export function MessageList({
  messages,
  contactId,
  loading = false,
  hasMore = false,
  onLoadMore,
}: MessageListProps) {
  // Any preprocessing (grouping, sorting, etc.)
  const processedMessages = useMemo(() => {
    // Messages are already sorted by timestamp from store
    // Could add grouping logic here for "Today", "Yesterday", etc.
    return messages;
  }, [messages]);

  return (
    <VirtualMessageList
      messages={processedMessages}
      contactId={contactId}
      loading={loading}
      hasMore={hasMore}
      onLoadMore={onLoadMore}
    />
  );
}
