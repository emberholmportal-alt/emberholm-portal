'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useChat } from '@/lib/hooks/useChat';
import { getProfile, UserProfile } from '@/lib/api';

/**
 * ChatScreen - 1:1 Private Chat
 */

interface ChatScreenProps {
  wallet: string;
  otherWallet: string;
  onBack: () => void;
}

// Daily message rewards
const PYRE_PER_MESSAGE = 5;
const MAX_DAILY_MESSAGES = 50;

export function ChatScreen({ wallet, otherWallet, onBack }: ChatScreenProps) {
  const [otherUser, setOtherUser] = useState<UserProfile | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [dailyMessageCount, setDailyMessageCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    isLoading,
    isSending,
    error,
    send,
  } = useChat({ wallet, otherWallet });

  // Load other user's profile
  useEffect(() => {
    async function loadOtherUser() {
      try {
        const profile = await getProfile(otherWallet);
        setOtherUser(profile);
      } catch (err) {
        console.error('Error loading user profile:', err);
      }
    }
    loadOtherUser();
  }, [otherWallet]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle send
  const handleSend = async () => {
    if (!inputValue.trim() || isSending) return;

    const success = await send(inputValue);
    if (success) {
      setInputValue('');

      // Update daily message count for reward tracking
      if (dailyMessageCount < MAX_DAILY_MESSAGES) {
        setDailyMessageCount(prev => prev + 1);
      }
    }
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Display name for other user
  const otherDisplayName = otherUser?.farcaster_username ||
    otherUser?.display_name ||
    `${otherWallet.slice(0, 6)}...${otherWallet.slice(-4)}`;

  // Can earn rewards
  const canEarnReward = dailyMessageCount < MAX_DAILY_MESSAGES;

  return (
    <div className="screen-view flex flex-col h-screen">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 border-b border-amber-dark/30"
      >
        <div className="flex items-center gap-3">
          {/* Back button */}
          <button
            onClick={onBack}
            className="text-amber hover:text-amber-bright"
          >
            ←
          </button>

          {/* Other user info */}
          <div className="flex items-center gap-2 flex-1">
            {otherUser?.farcaster_pfp_url ? (
              <img
                src={otherUser.farcaster_pfp_url}
                alt={otherDisplayName}
                className="w-8 h-8 rounded-full border border-amber-dark"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-amber-dark/30
                            flex items-center justify-center text-amber text-sm">
                {otherDisplayName.charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              <div className="text-amber-bright font-semibold">
                {otherDisplayName}
              </div>
              {otherUser?.farcaster_username && otherUser?.display_name && (
                <div className="text-xs text-amber-dim">
                  {otherUser.display_name}
                </div>
              )}
            </div>
          </div>

          {/* Reward indicator */}
          {canEarnReward && (
            <div className="text-xs text-amber-dim">
              <span className="text-amber">+{PYRE_PER_MESSAGE} $PYRE</span>
              <span className="text-amber-dark"> per msg</span>
            </div>
          )}
        </div>
      </motion.div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading && messages.length === 0 && (
          <div className="text-center text-amber-dim py-8">
            Loading messages...
          </div>
        )}

        {error && (
          <div className="text-center text-red py-2 text-sm">
            {error}
          </div>
        )}

        {!isLoading && messages.length === 0 && (
          <div className="text-center py-8">
            <div className="text-amber-dim mb-2">No messages yet</div>
            <div className="text-xs text-amber-dark">
              Start a conversation and earn $PYRE!
            </div>
          </div>
        )}

        {messages.map((msg, index) => {
          const isMine = msg.is_mine;
          const showDate = index === 0 ||
            new Date(msg.created_at).toDateString() !==
            new Date(messages[index - 1].created_at).toDateString();

          return (
            <div key={msg.id}>
              {/* Date separator */}
              {showDate && (
                <div className="text-center text-xs text-amber-dark my-4">
                  {formatMessageDate(msg.created_at)}
                </div>
              )}

              {/* Message bubble */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] px-3 py-2 rounded-lg ${
                    isMine
                      ? 'bg-amber/20 border border-amber/30 text-amber-bright'
                      : 'bg-cyan/10 border border-cyan/20 text-cyan'
                  }`}
                >
                  <div className="break-words">{msg.message}</div>
                  <div className={`text-xs mt-1 ${
                    isMine ? 'text-amber-dark' : 'text-cyan/50'
                  }`}>
                    {formatMessageTime(msg.created_at)}
                    {isMine && msg.read && ' ✓'}
                  </div>
                </div>
              </motion.div>
            </div>
          );
        })}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 border-t border-amber-dark/30"
      >
        {/* Daily reward progress */}
        {canEarnReward && (
          <div className="text-xs text-amber-dim mb-2 flex justify-between">
            <span>Daily messages: {dailyMessageCount}/{MAX_DAILY_MESSAGES}</span>
            <span className="text-amber">
              Earn {(MAX_DAILY_MESSAGES - dailyMessageCount) * PYRE_PER_MESSAGE} more $PYRE today
            </span>
          </div>
        )}

        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={isSending}
            className="flex-1 bg-dark/50 border border-amber-dark/50 rounded px-3 py-2
                     text-amber placeholder:text-amber-dark/50
                     focus:outline-none focus:border-amber
                     disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isSending}
            className="btn px-4 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSending ? '...' : '→'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// Helper to format message date
function formatMessageDate(dateStr: string): string {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === today.toDateString()) {
    return 'Today';
  }
  if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday';
  }
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

// Helper to format message time
function formatMessageTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export default ChatScreen;
