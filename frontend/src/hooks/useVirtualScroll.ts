/**
 * Virtual scroll hook wrapping TanStack Virtual.
 *
 * Provides:
 * - Consistent virtual scrolling setup
 * - Scroll to bottom/top helpers
 * - Configurable estimate size and overscan
 */

import { useRef, useCallback } from 'react';
import { useVirtualizer, ScrollToOptions } from '@tanstack/react-virtual';

type VirtualScrollBehavior = 'auto' | 'smooth';

interface UseVirtualScrollOptions<T> {
  items: T[];
  estimateSize?: number;
  overscan?: number;
  getItemKey?: (index: number) => string | number;
}

export function useVirtualScroll<T>({
  items,
  estimateSize = 80,
  overscan = 10,
  getItemKey,
}: UseVirtualScrollOptions<T>) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    overscan,
    getItemKey: getItemKey || ((index) => index),
  });

  const scrollToBottom = useCallback((behavior: VirtualScrollBehavior = 'smooth') => {
    if (items.length > 0) {
      virtualizer.scrollToIndex(items.length - 1, {
        align: 'end',
        behavior,
      } as ScrollToOptions);
    }
  }, [items.length, virtualizer]);

  const scrollToTop = useCallback((behavior: VirtualScrollBehavior = 'smooth') => {
    virtualizer.scrollToIndex(0, {
      align: 'start',
      behavior,
    } as ScrollToOptions);
  }, [virtualizer]);

  return {
    parentRef,
    virtualizer,
    virtualItems: virtualizer.getVirtualItems(),
    totalSize: virtualizer.getTotalSize(),
    scrollToBottom,
    scrollToTop,
  };
}
