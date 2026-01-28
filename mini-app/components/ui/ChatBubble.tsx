'use client';

import { motion } from 'framer-motion';

/**
 * ChatBubble - Chat message bubble
 * Different styles for sent/received messages
 */

interface ChatBubbleProps {
  message: string;
  isMine: boolean;
  timestamp: string;
  isRead?: boolean;
  showTimestamp?: boolean;
  animated?: boolean;
}

export function ChatBubble({
  message,
  isMine,
  timestamp,
  isRead = false,
  showTimestamp = true,
  animated = true,
}: ChatBubbleProps) {
  const formatTime = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const Component = animated ? motion.div : 'div';
  const animationProps = animated
    ? {
        initial: { opacity: 0, y: 10, scale: 0.95 },
        animate: { opacity: 1, y: 0, scale: 1 },
        transition: { duration: 0.2 },
      }
    : {};

  return (
    <div className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
      <Component
        {...animationProps}
        className={`
          max-w-[80%] px-3 py-2 rounded-lg
          ${isMine
            ? 'bg-amber/20 border border-amber/30'
            : 'bg-cyan/10 border border-cyan/20'
          }
        `}
      >
        {/* Message text */}
        <p className={`break-words ${isMine ? 'text-amber-bright' : 'text-cyan'}`}>
          {message}
        </p>

        {/* Timestamp and read status */}
        {showTimestamp && (
          <div
            className={`
              flex items-center gap-1 mt-1 text-xs
              ${isMine ? 'text-amber-dark justify-end' : 'text-cyan/50'}
            `}
          >
            <span>{formatTime(timestamp)}</span>
            {isMine && isRead && <span>✓</span>}
          </div>
        )}
      </Component>
    </div>
  );
}

export default ChatBubble;
