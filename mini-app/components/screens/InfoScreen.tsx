'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import { AppScreen } from '@/lib/store';

/**
 * InfoScreen - Info submenu with informational options
 * LORE, EVENTS, WHITEPAPER, TOKENOMICS, SOCIAL/CREDITS
 */

interface InfoScreenProps {
  onNavigate: (screen: AppScreen) => void;
  onBack: () => void;
}

interface MenuItem {
  id: AppScreen | 'whitepaper' | 'tokenomics' | 'social-credits';
  title: string;
  subtitle: string;
  iconSrc: string;
  description: string;
  isExternal?: boolean;
  externalUrl?: string;
}

export function InfoScreen({
  onNavigate,
  onBack,
}: InfoScreenProps) {
  const menuItems: MenuItem[] = [
    {
      id: 'lore',
      title: 'LORE',
      subtitle: 'Story & World',
      iconSrc: '/icons/EternalTorch.png',
      description: 'Discover the history and mysteries of Emberholm',
    },
    {
      id: 'events',
      title: 'EVENTS',
      subtitle: 'Active Events',
      iconSrc: '/icons/scroll.png',
      description: 'Current events and special missions',
    },
    {
      id: 'whitepaper',
      title: 'WHITEPAPER',
      subtitle: 'Documentation',
      iconSrc: '/icons/scroll.png',
      description: 'Technical documentation and project details',
      isExternal: true,
      externalUrl: 'https://emberholm.gitbook.io/',
    },
    {
      id: 'tokenomics',
      title: 'TOKENOMICS',
      subtitle: '$EMBER Economy',
      iconSrc: '/icons/moneybag.png',
      description: 'Token distribution and economic model',
      isExternal: true,
      externalUrl: 'https://emberholm.gitbook.io/tokenomics',
    },
    {
      id: 'social-credits',
      title: 'SOCIAL / CREDITS',
      subtitle: 'Community',
      iconSrc: '/icons/crystalball.png',
      description: 'Community links and project credits',
      isExternal: true,
      externalUrl: 'https://twitter.com/emberholm',
    },
  ];

  const handleItemClick = (item: MenuItem) => {
    if (item.isExternal && item.externalUrl) {
      window.open(item.externalUrl, '_blank', 'noopener,noreferrer');
    } else {
      onNavigate(item.id as AppScreen);
    }
  };

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-6"
      >
        <h1 className="title text-2xl">INFO</h1>
        <p className="subtitle">Learn about Emberholm</p>
      </motion.div>

      {/* Menu items */}
      <div className="flex-1 space-y-3">
        {menuItems.map((item, index) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * index }}
            onClick={() => handleItemClick(item)}
            className="w-full data-box text-left transition-all duration-200
                       hover:border-amber active:scale-[0.98]"
          >
            <div className="flex items-start gap-3">
              <Image
                src={item.iconSrc}
                alt=""
                width={24}
                height={24}
                className="pixel-icon mt-1"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-amber-bright font-semibold">
                    {item.title}
                  </h3>
                  <span className="text-xs text-amber-dim flex items-center gap-1">
                    {item.subtitle}
                    {item.isExternal && <span>↗</span>}
                  </span>
                </div>
                <p className="text-xs text-amber-dim mt-1">
                  {item.description}
                </p>
              </div>
              <span className="text-amber-dark">›</span>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Back button */}
      <button onClick={onBack} className="back-btn">
        ← BACK TO MENU
      </button>
    </div>
  );
}
