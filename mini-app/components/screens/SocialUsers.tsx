'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { getCountryUsers, CountryUser } from '@/lib/api';
import { getCountryName } from '@/lib/hooks/useGlobe';

/**
 * SocialUsers Screen - List of users from a country
 */

interface SocialUsersProps {
  countryCode: string;
  currentWallet: string | null;
  onMessageUser: (wallet: string) => void;
  onBack: () => void;
}

// Country flag emoji helper
function getCountryFlag(code: string): string {
  const codePoints = code
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

export function SocialUsers({
  countryCode,
  currentWallet,
  onMessageUser,
  onBack,
}: SocialUsersProps) {
  const [users, setUsers] = useState<CountryUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load users
  useEffect(() => {
    async function loadUsers() {
      setIsLoading(true);
      setError(null);
      try {
        const usersData = await getCountryUsers(countryCode);
        setUsers(usersData);
      } catch (err) {
        console.error('Error loading users:', err);
        setError('Failed to load operators');
      } finally {
        setIsLoading(false);
      }
    }
    loadUsers();
  }, [countryCode]);

  const countryName = getCountryName(countryCode);
  const flag = getCountryFlag(countryCode);
  const onlineCount = users.filter(u => u.is_online).length;

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-4"
      >
        <div className="text-4xl mb-2">{flag}</div>
        <h1 className="title text-xl">{countryName}</h1>
        <p className="subtitle">
          {users.length} Operator{users.length !== 1 ? 's' : ''} •{' '}
          <span className="text-green">{onlineCount} Online</span>
        </p>
      </motion.div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-amber animate-pulse">
            Scanning operator frequencies...
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex-1 flex items-center justify-center">
          <div className="data-box text-center">
            <div className="text-red mb-2">⚠ {error}</div>
            <button
              onClick={() => window.location.reload()}
              className="btn small"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Users List */}
      {!isLoading && !error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex-1 space-y-2 overflow-y-auto"
        >
          {users.length === 0 ? (
            <div className="text-center text-amber-dim py-8">
              No operators found in this region
            </div>
          ) : (
            users.map((user, index) => {
              const isCurrentUser = user.wallet.toLowerCase() === currentWallet?.toLowerCase();
              const displayName = user.farcaster_username || user.display_name ||
                `${user.wallet.slice(0, 6)}...${user.wallet.slice(-4)}`;

              return (
                <motion.div
                  key={user.wallet}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.02 * index }}
                  className={`data-box flex items-center gap-3 ${
                    isCurrentUser ? 'border-amber' : ''
                  }`}
                >
                  {/* Avatar */}
                  <div className="relative">
                    {user.farcaster_pfp_url ? (
                      <img
                        src={user.farcaster_pfp_url}
                        alt={displayName}
                        className="w-10 h-10 rounded-full border border-amber-dark"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-amber-dark/30
                                    flex items-center justify-center text-amber">
                        {displayName.charAt(0).toUpperCase()}
                      </div>
                    )}
                    {/* Online indicator */}
                    {user.is_online && (
                      <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3
                                    bg-green rounded-full border-2 border-dark" />
                    )}
                  </div>

                  {/* User Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`font-semibold truncate ${
                        user.is_online ? 'text-amber-bright' : 'text-amber'
                      }`}>
                        {displayName}
                      </span>
                      {isCurrentUser && (
                        <span className="text-xs text-cyan">(You)</span>
                      )}
                    </div>
                    <div className="text-xs text-amber-dim">
                      {user.is_online ? (
                        <span className="text-green">● Online</span>
                      ) : user.last_seen ? (
                        `Last seen ${formatLastSeen(user.last_seen)}`
                      ) : (
                        'Offline'
                      )}
                    </div>
                  </div>

                  {/* Message Button */}
                  {!isCurrentUser && (
                    <button
                      onClick={() => onMessageUser(user.wallet)}
                      className="btn small"
                    >
                      MSG
                    </button>
                  )}
                </motion.div>
              );
            })
          )}
        </motion.div>
      )}

      {/* Back button */}
      <button onClick={onBack} className="back-btn mt-4">
        ← BACK TO MAP
      </button>
    </div>
  );
}

// Helper to format last seen time
function formatLastSeen(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export default SocialUsers;
