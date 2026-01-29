'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';

/**
 * TutorialScreen - Game guide
 * Content from portal web tutorial sections
 */

interface TutorialScreenProps {
  onBack: () => void;
}

interface TutorialSection {
  id: string;
  title: string;
  icon: string;
  iconSrc?: string;
  summary: string;
  content: string[];
}

const TUTORIAL_SECTIONS: TutorialSection[] = [
  {
    id: 'getting-started',
    title: 'GETTING STARTED',
    icon: '',
    iconSrc: '/icons/Sparkles.png',
    summary: 'Your first steps in Emberholm',
    content: [
      '1. MINT YOUR EMISSARY: Get your first Emissary by minting from the portal. Each one is unique!',
      '2. CHECK YOUR STATS: View your Emissary\'s level, power, and energy in the Play menu.',
      '3. START A MISSION: Choose a mission that matches your level. Beginners should start with Easy missions.',
      '4. EARN REWARDS: Complete missions to earn $EMBER, XP, and rare items.',
      '5. LEVEL UP: Gain XP to increase your level and unlock harder missions with better rewards.',
    ],
  },
  {
    id: 'missions',
    title: 'MISSIONS',
    icon: '',
    iconSrc: '/icons/Swords.png',
    summary: 'Long adventures with high rewards',
    content: [
      'DURATION: Missions last 1-24 hours depending on difficulty.',
      'ENERGY: Each mission costs energy. Energy regenerates over time.',
      'DIFFICULTY: Easy → Medium → Hard → Legendary. Higher = better rewards but more risk.',
      'DEATH CHANCE: Harder missions have a chance of permanent death. Check the % before starting!',
      'REWARDS: $EMBER, XP, items, and rare runes. Legendary missions can drop exclusive gear.',
      'TIP: Don\'t rush into hard missions. Build up your power first!',
    ],
  },
  {
    id: 'micro-missions',
    title: 'MICRO-MISSIONS',
    icon: '',
    iconSrc: '/icons/Lightning.png',
    summary: 'Quick 1-5 minute adventures',
    content: [
      'DURATION: 1-5 minutes. Perfect for quick play sessions.',
      'REWARDS: Earn small amounts of $EMBER and XP.',
      'NO DEATH: Micro-missions are safe—no permadeath risk!',
      'NARRATIVE: Each micro-mission has a story with choices that affect your rewards.',
      'DAILY LIMIT: Some micro-missions have cooldowns. Check back often for new ones!',
      'TIP: Great way to earn $EMBER while your main Emissary is on a long mission.',
    ],
  },
  {
    id: 'economy',
    title: 'ECONOMY',
    icon: '',
    iconSrc: '/icons/moneybag.png',
    summary: 'Understanding $EMBER and $ASH',
    content: [
      '$EMBER: Main currency. Earned from missions. Used to buy items, upgrade gear, and more.',
      '$ASH: Created by burning $EMBER (10:1 ratio). Needed for certain rituals and rare items.',
      'CLAIMING: Pending rewards must be claimed. Check your Vault regularly!',
      'BURNING: Convert EMBER to ASH in the Vault. Think carefully—it\'s one-way!',
      'TIP: Balance your economy. Don\'t burn all your EMBER unless you need ASH.',
    ],
  },
  {
    id: 'equipment',
    title: 'EQUIPMENT',
    icon: '',
    iconSrc: '/icons/shield.png',
    summary: 'Gear up for battle',
    content: [
      'SLOTS: Weapon, Armor, Accessory, and 3 Rune slots.',
      'RARITY: Common → Uncommon → Rare → Epic → Legendary. Higher = better stats.',
      'EQUIPPING: Go to Vault → Items/Runes → Select item → Choose Emissary.',
      'BENEFITS: Equipment adds stats like Power, Defense, Crit chance, and special effects.',
      'FINDING GEAR: Items drop from missions. Runes are rarer—found in harder missions.',
      'TIP: Match your gear to your playstyle. Offensive? Load up on power. Defensive? Stack defense.',
    ],
  },
  {
    id: 'survival',
    title: 'SURVIVAL TIPS',
    icon: '',
    iconSrc: '/icons/skull.png',
    summary: 'Stay alive in a dangerous world',
    content: [
      '1. CHECK DEATH CHANCE: Always review the death % before starting a mission.',
      '2. DON\'T OVEREXTEND: If your Emissary is low level, avoid Hard+ missions.',
      '3. GEAR UP: Better equipment reduces death chance.',
      '4. WATCH YOUR ENERGY: Don\'t start a mission if energy is low.',
      '5. TAKE BREAKS: Long missions are safer when you\'re focused.',
      '6. HAVE BACKUP: Mint multiple Emissaries so losing one isn\'t devastating.',
      'REMEMBER: Permadeath is permanent. Play smart, live long!',
    ],
  },
];

export function TutorialScreen({ onBack }: TutorialScreenProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleSection = (id: string) => {
    setExpandedSection(expandedSection === id ? null : id);
  };

  return (
    <div className="screen-view flex flex-col min-h-screen">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 text-center"
      >
        <h1 className="title text-2xl">TUTORIAL</h1>
        <p className="subtitle">Learn to survive and thrive</p>
      </motion.div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {TUTORIAL_SECTIONS.map((section, index) => (
          <motion.div
            key={section.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full data-box text-left transition-all duration-200
                       hover:border-amber"
            >
              <div className="flex items-start gap-3">
                {section.iconSrc ? (
                  <Image
                    src={section.iconSrc}
                    alt=""
                    width={24}
                    height={24}
                    className="pixel-icon mt-1"
                  />
                ) : (
                  <span className="text-2xl">{section.icon}</span>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-amber-bright font-semibold">
                      {section.title}
                    </span>
                    <motion.span
                      animate={{ rotate: expandedSection === section.id ? 180 : 0 }}
                      className="text-amber-dim"
                    >
                      ▼
                    </motion.span>
                  </div>
                  <p className="text-xs text-amber-dim mt-1">{section.summary}</p>
                </div>
              </div>
            </button>

            <AnimatePresence>
              {expandedSection === section.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden"
                >
                  <div className="data-box mt-2 space-y-2">
                    {section.content.map((line, lIndex) => (
                      <motion.p
                        key={lIndex}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: lIndex * 0.05 }}
                        className="text-amber-dim text-sm leading-relaxed"
                      >
                        {line}
                      </motion.p>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      {/* Back button */}
      <div className="p-4">
        <button onClick={onBack} className="back-btn">
          ← BACK
        </button>
      </div>
    </div>
  );
}

export default TutorialScreen;
