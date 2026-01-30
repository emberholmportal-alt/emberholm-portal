'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';
import { AppScreen } from '@/lib/store';

/**
 * MainMenu - Main dashboard / command center
 * Shows: Logo, Connect Wallet, 7 menu buttons, bottom stats
 * Buttons: PLAY, MINT EMISSARY, SOCIAL, VAULT, EVENTS, LORE, TUTORIAL
 */

interface MenuItem {
  id: AppScreen;
  title: string;
  icon: string;
  iconSrc?: string;
  badge?: number;
}

interface MainMenuProps {
  wallet?: string | null;
  emberBalance?: number;
  emissaryCount?: number;
  unreadMessages?: number;
  onNavigate: (screen: AppScreen) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

// Wallet options for connection modal
const WALLET_OPTIONS = [
  { id: 'farcaster', name: 'Farcaster Wallet', icon: '/icons/farcaster.png', featured: true },
  { id: 'metamask', name: 'MetaMask', icon: '/icons/metamask.png' },
  { id: 'coinbase', name: 'Coinbase Wallet', icon: '/icons/coinbase.png' },
  { id: 'phantom', name: 'Phantom', icon: '/icons/phantom.png' },
  { id: 'rabby', name: 'Rabby', icon: '/icons/rabby.png' },
];

export function MainMenu({
  wallet = null,
  emberBalance = 0,
  emissaryCount = 0,
  unreadMessages = 0,
  onNavigate,
  onConnect,
  onDisconnect,
}: MainMenuProps) {
  const [showWalletModal, setShowWalletModal] = useState(false);

  const menuItems: MenuItem[] = [
    {
      id: 'play',
      title: 'PLAY',
      icon: '▶',
    },
    {
      id: 'mint',
      title: 'MINT EMISSARY',
      icon: '◈',
    },
    {
      id: 'social-globe',
      title: 'SOCIAL',
      icon: '',
      iconSrc: '/icons/crystalball.png',
      badge: unreadMessages,
    },
    {
      id: 'vault',
      title: 'VAULT',
      icon: '',
      iconSrc: '/icons/moneybag.png',
    },
    {
      id: 'events',
      title: 'EVENTS',
      icon: '',
      iconSrc: '/icons/scroll.png',
    },
    {
      id: 'lore',
      title: 'LORE',
      icon: '',
      iconSrc: '/icons/EternalTorch.png',
    },
    {
      id: 'tutorial',
      title: 'TUTORIAL',
      icon: '?',
    },
  ];

  // Truncate wallet address for display
  const truncateWallet = (address: string) => {
    if (!address || address === '0x0000000000000000000000000000000000000000') {
      return 'Demo Mode';
    }
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  // Handle wallet connection option
  const handleWalletOption = async (optionId: string) => {
    setShowWalletModal(false);
    // Trigger connection through parent
    onConnect?.();
  };

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header with Logo and Settings */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-2 relative"
      >
        {/* Settings Button - Top Right */}
        <button
          onClick={() => onNavigate('settings')}
          className="absolute top-0 right-0 w-10 h-10 flex items-center justify-center
                   text-amber-dim hover:text-amber transition-colors"
          title="Settings"
        >
          <span className="text-xl">⚙️</span>
        </button>

        <Image
          src="/logo.png"
          alt="Emberholm"
          width={180}
          height={60}
          className="logo-image mx-auto"
          priority
        />
        <p className="subtitle mt-1">MINI APP</p>
      </motion.div>

      {/* Connect Wallet Button */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-4"
      >
        {wallet ? (
          <div className="flex items-center justify-center gap-2">
            <div className="data-box px-3 py-2 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green animate-pulse" />
              <span className="text-amber text-sm font-mono">
                {truncateWallet(wallet)}
              </span>
            </div>
            <button
              onClick={onDisconnect}
              className="btn small secondary"
            >
              DISCONNECT
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowWalletModal(true)}
            className="w-full btn large"
          >
            CONNECT WALLET
          </button>
        )}
      </motion.div>

      {/* Menu buttons */}
      <div className="menu-container flex-1">
        {menuItems.map((item, index) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * index }}
            onClick={() => onNavigate(item.id)}
            className={`menu-btn ${index === 0 ? 'selected' : ''}`}
          >
            <span className="icon">
              {item.iconSrc ? (
                <Image
                  src={item.iconSrc}
                  alt=""
                  width={20}
                  height={20}
                  className="pixel-icon"
                />
              ) : (
                item.icon
              )}
            </span>
            <span className="flex-1 text-left">{item.title}</span>
            {item.badge && item.badge > 0 && (
              <span className="notif-badge">{item.badge}</span>
            )}
          </motion.button>
        ))}
      </div>

      {/* Wallet Connection Modal */}
      <AnimatePresence>
        {showWalletModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80"
            onClick={() => setShowWalletModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="portal-box w-full max-w-sm"
              onClick={e => e.stopPropagation()}
            >
              <div className="ornament mb-4">═══ ◈ ═══</div>

              <h2 className="title text-lg text-center mb-4">CONNECT WALLET</h2>

              <div className="space-y-2">
                {WALLET_OPTIONS.map((option) => (
                  <button
                    key={option.id}
                    onClick={() => handleWalletOption(option.id)}
                    className={`w-full data-box flex items-center gap-3 p-3 transition-all
                              hover:border-amber ${option.featured ? 'border-amber' : ''}`}
                  >
                    <div className="w-8 h-8 flex items-center justify-center">
                      <Image
                        src={option.icon}
                        alt=""
                        width={24}
                        height={24}
                        className="pixel-icon"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = '/icons/Sparkles.png';
                        }}
                      />
                    </div>
                    <span className={`flex-1 text-left ${option.featured ? 'text-amber-bright' : 'text-amber'}`}>
                      {option.name}
                    </span>
                    {option.featured && (
                      <span className="text-xs text-cyan">RECOMMENDED</span>
                    )}
                  </button>
                ))}
              </div>

              <div className="ornament mt-4">═══ ◈ ═══</div>

              <button
                onClick={() => setShowWalletModal(false)}
                className="w-full btn secondary mt-4"
              >
                CANCEL
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
