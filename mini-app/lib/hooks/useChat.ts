/**
 * useChat Hook - Chat functionality for Emberholm Mini App
 * Handles polling, sending messages, and marking as read
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getMessages,
  sendMessage,
  markMessagesRead,
  getConversations,
  PrivateMessage,
  Conversation,
} from '../api';

interface UseChatOptions {
  wallet: string | null;
  otherWallet: string | null;
  pollInterval?: number; // ms, default 5000
}

interface UseChatReturn {
  messages: PrivateMessage[];
  conversations: Conversation[];
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  unreadCount: number;
  send: (message: string) => Promise<boolean>;
  refresh: () => Promise<void>;
  markRead: () => Promise<void>;
}

export function useChat({
  wallet,
  otherWallet,
  pollInterval = 5000,
}: UseChatOptions): UseChatReturn {
  const [messages, setMessages] = useState<PrivateMessage[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollRef = useRef<NodeJS.Timeout | null>(null);
  const isActiveRef = useRef(true);

  // Calculate total unread count
  const unreadCount = conversations.reduce((sum, c) => sum + c.unread_count, 0);

  // Fetch messages for active chat
  const fetchMessages = useCallback(async () => {
    if (!wallet || !otherWallet) return;

    try {
      const newMessages = await getMessages(wallet, otherWallet);
      if (isActiveRef.current) {
        setMessages(newMessages);
      }
    } catch (err) {
      console.error('Error fetching messages:', err);
      if (isActiveRef.current) {
        setError('Failed to load messages');
      }
    }
  }, [wallet, otherWallet]);

  // Fetch all conversations
  const fetchConversations = useCallback(async () => {
    if (!wallet) return;

    try {
      const convs = await getConversations(wallet);
      if (isActiveRef.current) {
        setConversations(convs);
      }
    } catch (err) {
      console.error('Error fetching conversations:', err);
    }
  }, [wallet]);

  // Combined refresh
  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    await Promise.all([
      fetchMessages(),
      fetchConversations(),
    ]);

    setIsLoading(false);
  }, [fetchMessages, fetchConversations]);

  // Send a message
  const send = useCallback(async (message: string): Promise<boolean> => {
    if (!wallet || !otherWallet || !message.trim()) return false;

    setIsSending(true);
    setError(null);

    try {
      const newMessage = await sendMessage(wallet, otherWallet, message.trim());

      // Optimistically add the message to the list
      setMessages(prev => [...prev, newMessage]);

      // Refresh conversations to update last message
      await fetchConversations();

      setIsSending(false);
      return true;
    } catch (err: any) {
      console.error('Error sending message:', err);
      setError(err.message || 'Failed to send message');
      setIsSending(false);
      return false;
    }
  }, [wallet, otherWallet, fetchConversations]);

  // Mark messages as read
  const markRead = useCallback(async () => {
    if (!wallet || !otherWallet) return;

    try {
      await markMessagesRead(wallet, otherWallet);

      // Update local state
      setMessages(prev => prev.map(m => ({
        ...m,
        read: m.from_wallet !== wallet ? true : m.read,
      })));

      // Refresh conversations to update unread count
      await fetchConversations();
    } catch (err) {
      console.error('Error marking messages as read:', err);
    }
  }, [wallet, otherWallet, fetchConversations]);

  // Initial load
  useEffect(() => {
    isActiveRef.current = true;

    if (wallet) {
      refresh();
    }

    return () => {
      isActiveRef.current = false;
    };
  }, [wallet, otherWallet]); // eslint-disable-line react-hooks/exhaustive-deps

  // Polling for new messages
  useEffect(() => {
    if (!wallet || !otherWallet) return;

    // Clear any existing poll
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }

    // Start polling
    pollRef.current = setInterval(fetchMessages, pollInterval);

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [wallet, otherWallet, pollInterval, fetchMessages]);

  // Auto mark as read when viewing messages
  useEffect(() => {
    if (messages.length > 0 && otherWallet) {
      const unreadFromOther = messages.some(
        m => m.from_wallet === otherWallet && !m.read
      );
      if (unreadFromOther) {
        markRead();
      }
    }
  }, [messages, otherWallet, markRead]);

  return {
    messages,
    conversations,
    isLoading,
    isSending,
    error,
    unreadCount,
    send,
    refresh,
    markRead,
  };
}

export default useChat;
