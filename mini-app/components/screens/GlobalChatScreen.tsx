'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlobalMessage, getGlobalMessages, sendGlobalMessage } from '@/lib/api';
import { ChatIcon, GemIcon, GlobeIcon } from '@/components/ui/Icons';

/**
 * GlobalChatScreen - Realm-wide global chat
 * All operators can chat together and earn PYRE
 */

interface GlobalChatScreenProps {
  wallet: string | null;
  displayName?: string | null;
  onBack: () => void;
}

export function GlobalChatScreen({ wallet, displayName, onBack }: GlobalChatScreenProps) {
  const [messages, setMessages] = useState<GlobalMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pyreNotification, setPyreNotification] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Format timestamp
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Format wallet address
  const formatWallet = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  // Get display name for a message
  const getMessageDisplayName = (msg: GlobalMessage) => {
    if (msg.user.farcaster_username) return `@${msg.user.farcaster_username}`;
    if (msg.user.display_name) return msg.user.display_name;
    return formatWallet(msg.wallet);
  };

  // Load messages
  const loadMessages = useCallback(async (showLoading = false) => {
    if (showLoading) setIsLoading(true);
    setError(null);

    try {
      const data = await getGlobalMessages(50);
      setMessages(data.reverse()); // Oldest first for chat display
    } catch (err) {
      console.error('Failed to load global chat:', err);
      setError('Failed to load messages');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Send message
  const handleSend = async () => {
    if (!wallet || !newMessage.trim() || isSending) return;

    const messageText = newMessage.trim();
    if (messageText.length > 500) {
      setError('Message too long (max 500 characters)');
      return;
    }

    setIsSending(true);
    setError(null);

    try {
      const result = await sendGlobalMessage(wallet, messageText);
      setNewMessage('');

      // Add message to list
      setMessages(prev => [...prev, result.message]);

      // Show PYRE notification
      if (result.pyre_earned > 0) {
        setPyreNotification(result.pyre_earned);
        setTimeout(() => setPyreNotification(null), 3000);
      }

      // Scroll to bottom
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err: any) {
      setError(err.message || 'Failed to send message');
    } finally {
      setIsSending(false);
    }
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Initial load
  useEffect(() => {
    loadMessages(true);
  }, [loadMessages]);

  // Poll for new messages
  useEffect(() => {
    pollIntervalRef.current = setInterval(() => {
      loadMessages(false);
    }, 10000); // Poll every 10 seconds

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [loadMessages]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length]);

  return (
    <div className="screen-view flex flex-col min-h-screen">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 border-b border-amber-dark/30"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GlobeIcon size={24} className="text-amber" />
            <div>
              <h1 className="title text-lg">GLOBAL CHAT</h1>
              <p className="text-xs text-amber-dim">{messages.length} messages</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-cyan flex items-center gap-1">
              <GemIcon size={12} className="text-cyan" />
              +5 PYRE per message
            </div>
          </div>
        </div>
      </motion.div>

      {/* PYRE Notification */}
      <AnimatePresence>
        {pyreNotification && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-16 left-1/2 -translate-x-1/2 z-50"
          >
            <div className="bg-cyan/20 border border-cyan px-4 py-2 rounded-lg flex items-center gap-2">
              <GemIcon size={16} className="text-cyan" />
              <span className="text-cyan font-semibold">+{pyreNotification} PYRE</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <ChatIcon size={48} className="text-amber animate-pulse mx-auto mb-2" />
              <p className="text-amber-dim text-sm">Loading chat...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <ChatIcon size={48} className="text-amber-dim mx-auto mb-2" />
              <p className="text-amber-dim">No messages yet</p>
              <p className="text-xs text-amber-dark mt-1">Be the first to speak!</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => {
              const isOwn = wallet && msg.wallet.toLowerCase() === wallet.toLowerCase();

              return (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index < 10 ? 0.02 * index : 0 }}
                  className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] ${isOwn ? 'order-2' : ''}`}>
                    {/* User info */}
                    <div className={`flex items-center gap-2 mb-1 ${isOwn ? 'justify-end' : ''}`}>
                      {msg.user.farcaster_pfp_url && !isOwn && (
                        <img
                          src={msg.user.farcaster_pfp_url}
                          alt=""
                          className="w-5 h-5 rounded-full"
                        />
                      )}
                      <span className={`text-xs ${isOwn ? 'text-cyan' : 'text-amber'}`}>
                        {getMessageDisplayName(msg)}
                      </span>
                      {msg.user.country_code && (
                        <span className="text-xs text-amber-dark">
                          {msg.user.country_code}
                        </span>
                      )}
                      <span className="text-xs text-amber-darker">
                        {formatTime(msg.created_at)}
                      </span>
                    </div>

                    {/* Message bubble */}
                    <div
                      className={`px-3 py-2 rounded-lg ${
                        isOwn
                          ? 'bg-cyan/20 border border-cyan/30 text-cyan'
                          : 'bg-amber/10 border border-amber-dark/30 text-amber'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap break-words">
                        {msg.message}
                      </p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="px-4 py-2 bg-red/10 border-t border-red/30">
          <p className="text-red text-xs text-center">{error}</p>
        </div>
      )}

      {/* Input area */}
      <div className="p-4 border-t border-amber-dark/30">
        {wallet ? (
          <div className="flex gap-2">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message..."
              maxLength={500}
              disabled={isSending}
              className="flex-1 bg-dark border border-amber-dark rounded px-3 py-2
                       text-amber placeholder-amber-darker text-sm
                       focus:outline-none focus:border-amber
                       disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!newMessage.trim() || isSending}
              className="btn px-4 disabled:opacity-50"
            >
              {isSending ? '...' : 'SEND'}
            </button>
          </div>
        ) : (
          <div className="text-center py-2">
            <p className="text-amber-dim text-sm">Connect wallet to chat</p>
          </div>
        )}
        <div className="flex justify-between items-center mt-2">
          <span className="text-xs text-amber-darker">
            {newMessage.length}/500
          </span>
          <span className="text-xs text-amber-dark">
            Max 50 messages/day for PYRE
          </span>
        </div>
      </div>

      {/* Back button */}
      <div className="p-4 pt-0">
        <button onClick={onBack} className="back-btn">
          ← BACK
        </button>
      </div>
    </div>
  );
}

export default GlobalChatScreen;
