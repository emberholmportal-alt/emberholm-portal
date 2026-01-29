'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import Image from 'next/image';
import { GlobalMessage, getGlobalMessages, sendGlobalMessage } from '@/lib/api';

/**
 * GlobalChatScreen - Global chat room for all operators
 * Earns $PYRE for participation
 */

interface GlobalChatScreenProps {
  wallet: string | null;
  onBack: () => void;
}

// Daily message rewards
const PYRE_PER_MESSAGE = 5;
const MAX_DAILY_MESSAGES = 50;

export function GlobalChatScreen({ wallet, onBack }: GlobalChatScreenProps) {
  const [messages, setMessages] = useState<GlobalMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dailyMessageCount, setDailyMessageCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load messages
  useEffect(() => {
    async function loadMessages() {
      setIsLoading(true);
      try {
        const data = await getGlobalMessages(100);
        setMessages(data);
      } catch (err) {
        setError('Failed to load messages');
      } finally {
        setIsLoading(false);
      }
    }
    loadMessages();

    // Poll for new messages every 5 seconds
    const interval = setInterval(async () => {
      try {
        const data = await getGlobalMessages(100);
        setMessages(data);
      } catch {
        // Silently fail on poll errors
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle send
  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || !wallet || isSending) return;

    setIsSending(true);
    try {
      const newMessage = await sendGlobalMessage(wallet, inputValue.trim());
      setMessages(prev => [...prev, newMessage]);
      setInputValue('');

      if (dailyMessageCount < MAX_DAILY_MESSAGES) {
        setDailyMessageCount(prev => prev + 1);
      }
    } catch (err) {
      setError('Failed to send message');
    } finally {
      setIsSending(false);
    }
  }, [inputValue, wallet, isSending, dailyMessageCount]);

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

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
          <button
            onClick={onBack}
            className="text-amber hover:text-amber-bright"
          >
            <Image src="/icons/portal.png" alt="" width={20} height={20} className="pixel-icon" />
          </button>

          <div className="flex-1">
            <h1 className="text-amber-bright font-semibold flex items-center gap-2">
              <Image src="/icons/fire.png" alt="" width={16} height={16} className="pixel-icon" />
              GLOBAL CHAT
            </h1>
            <p className="text-xs text-amber-dim">
              {messages.length} messages • All operators welcome
            </p>
          </div>

          {/* Reward indicator */}
          {canEarnReward && wallet && (
            <div className="text-xs text-amber-dim text-right">
              <span className="text-amber">+{PYRE_PER_MESSAGE}</span>
              <span className="text-amber-dark"> PYRE/msg</span>
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
            <Image
              src="/icons/fire.png"
              alt=""
              width={32}
              height={32}
              className="pixel-icon mx-auto mb-2 opacity-50"
            />
            <div className="text-amber-dim mb-2">No messages yet</div>
            <div className="text-xs text-amber-dark">
              Be the first to speak in the Global Chat!
            </div>
          </div>
        )}

        {messages.map((msg, index) => {
          const isMine = wallet && msg.wallet.toLowerCase() === wallet.toLowerCase();
          const displayName = msg.farcaster_username || msg.display_name ||
            `${msg.wallet.slice(0, 6)}...${msg.wallet.slice(-4)}`;
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

              {/* Message */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-2 ${isMine ? 'flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                {msg.farcaster_pfp_url ? (
                  <img
                    src={msg.farcaster_pfp_url}
                    alt={displayName}
                    className="w-8 h-8 rounded-full border border-amber-dark flex-shrink-0"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-amber-dark/30
                                flex items-center justify-center text-amber text-xs flex-shrink-0">
                    {displayName.charAt(0).toUpperCase()}
                  </div>
                )}

                {/* Message content */}
                <div className={`max-w-[75%] ${isMine ? 'text-right' : ''}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-semibold ${isMine ? 'text-amber-bright' : 'text-cyan'}`}>
                      {displayName}
                    </span>
                    <span className="text-xs text-amber-dark">
                      {formatMessageTime(msg.created_at)}
                    </span>
                  </div>
                  <div
                    className={`px-3 py-2 rounded-lg ${
                      isMine
                        ? 'bg-amber/20 border border-amber/30 text-amber-bright'
                        : 'bg-dark border border-amber-dark/30 text-amber-dim'
                    }`}
                  >
                    {msg.message}
                  </div>
                </div>
              </motion.div>
            </div>
          );
        })}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 border-t border-amber-dark/30"
      >
        {!wallet ? (
          <div className="text-center text-amber-dim text-sm py-2">
            Connect wallet to chat
          </div>
        ) : (
          <>
            {/* Daily reward progress */}
            {canEarnReward && (
              <div className="text-xs text-amber-dim mb-2 flex justify-between">
                <span>Daily messages: {dailyMessageCount}/{MAX_DAILY_MESSAGES}</span>
                <span className="text-amber">
                  Earn {(MAX_DAILY_MESSAGES - dailyMessageCount) * PYRE_PER_MESSAGE} more PYRE today
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
                maxLength={500}
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
                {isSending ? '...' : 'SEND'}
              </button>
            </div>
          </>
        )}
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

export default GlobalChatScreen;
