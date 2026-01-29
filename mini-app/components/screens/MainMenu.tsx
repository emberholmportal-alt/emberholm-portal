'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import { AppScreen } from '@/lib/store';

/**
 * MainMenu - Main dashboard / command center
 * Shows: Logo, 7 menu buttons, bottom stats
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
  pyreBalance?: number;
  emissaryCount?: number;
  unreadMessages?: number;
  onNavigate: (screen: AppScreen) => void;
}

export function MainMenu({
  pyreBalance = 0,
  emissaryCount = 0,
  unreadMessages = 0,
  onNavigate,
}: MainMenuProps) {
  // Menu items - using PNG icons with orange filter (per prototype v8 spec)
  // Simple ASCII fallbacks: ▶ ◈ only
  const menuItems: MenuItem[] = [
    {
      id: 'play',
      title: 'PLAY',
      icon: '▶',
      iconSrc: '/icons/Swords.png',
    },
    {
      id: 'mint',
      title: 'MINT EMISSARY',
      icon: '◈',
      iconSrc: '/icons/Sparkles.png',
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
      iconSrc: '/icons/Lightning.png',
    },
  ];

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header with Logo */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-4"
      >
        <Image
          src="/logo.png"
          alt="Emberholm"
          width={180}
          height={60}
          className="logo-image mx-auto"
          priority
        />
        <p className="subtitle mt-2">MINI APP</p>
      </motion.div>

      {/* Menu buttons */}
      <div className="menu-container">
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

      {/* Stats footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="stats-footer"
      >
        <div className="stat-item">
          <div className="stat-value">{emissaryCount}</div>
          <div className="stat-label">EMISSARIES</div>
        </div>
        <div className="stat-item">
          <div className="stat-value cyan">{pyreBalance.toLocaleString()}</div>
          <div className="stat-label flex items-center justify-center gap-1">
            <Image src="/icons/Sparkles.png" alt="" width={12} height={12} className="pixel-icon-small" />
            PYRE
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-value">0</div>
          <div className="stat-label flex items-center justify-center gap-1">
            <Image src="/icons/fire.png" alt="" width={12} height={12} className="pixel-icon-small" />
            EMBER
          </div>
        </div>
      </motion.div>
    </div>
  );
}
