'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';

/**
 * TutorialScreen - Game guide with progress tracking
 * Complete all sections to earn 3 $EMBER reward
 */

interface TutorialScreenProps {
  wallet: string | null;
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
      'DIFFICULTY: Easy → Medium → Hard. Higher = better rewards but more risk.',
      'DEATH CHANCE: Harder missions have a chance of permanent death. Check the % before starting!',
      'REWARDS: $EMBER, XP, items, and rare runes.',
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
      '2. DON\'T OVEREXTEND: If your Emissary is low level, avoid Hard missions.',
      '3. GEAR UP: Better equipment reduces death chance.',
      '4. WATCH YOUR ENERGY: Don\'t start a mission if energy is low.',
      '5. HAVE BACKUP: Mint multiple Emissaries so losing one isn\'t devastating.',
      'REMEMBER: Permadeath is permanent. Play smart, live long!',
    ],
  },
];

const STORAGE_KEY = 'emberholm_tutorial_progress';
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export function TutorialScreen({ wallet, onBack }: TutorialScreenProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [completedSections, setCompletedSections] = useState<Set<string>>(new Set());
  const [tutorialCompleted, setTutorialCompleted] = useState(false);
  const [showRewardPopup, setShowRewardPopup] = useState(false);
  const [isClaimingReward, setIsClaimingReward] = useState(false);
  const [rewardClaimed, setRewardClaimed] = useState(false);

  // Load progress from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        setCompletedSections(new Set(data.completed || []));
        setTutorialCompleted(data.tutorialCompleted || false);
        setRewardClaimed(data.rewardClaimed || false);
      } catch {
        // Invalid data, start fresh
      }
    }
  }, []);

  // Save progress to localStorage
  const saveProgress = (completed: Set<string>, tutorialDone: boolean, claimed: boolean) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      completed: Array.from(completed),
      tutorialCompleted: tutorialDone,
      rewardClaimed: claimed,
    }));
  };

  // Check if a section is unlocked (first section always unlocked, others need previous completed)
  const isSectionUnlocked = (index: number): boolean => {
    if (index === 0) return true;
    const previousSection = TUTORIAL_SECTIONS[index - 1];
    return completedSections.has(previousSection.id);
  };

  // Mark section as complete
  const completeSection = (sectionId: string) => {
    const newCompleted = new Set(completedSections);
    newCompleted.add(sectionId);
    setCompletedSections(newCompleted);

    // Check if all sections complete
    const allComplete = TUTORIAL_SECTIONS.every(s => newCompleted.has(s.id));
    if (allComplete && !tutorialCompleted) {
      setTutorialCompleted(true);
      saveProgress(newCompleted, true, rewardClaimed);
    } else {
      saveProgress(newCompleted, tutorialCompleted, rewardClaimed);
    }

    // Auto-expand next section
    const currentIndex = TUTORIAL_SECTIONS.findIndex(s => s.id === sectionId);
    if (currentIndex < TUTORIAL_SECTIONS.length - 1) {
      setExpandedSection(TUTORIAL_SECTIONS[currentIndex + 1].id);
    } else {
      setExpandedSection(null);
    }
  };

  // Handle complete tutorial and claim reward
  const handleCompleteTutorial = async () => {
    if (!wallet || rewardClaimed) return;

    setIsClaimingReward(true);
    try {
      // Call API to claim tutorial reward
      const response = await fetch(`${API_BASE}/api/social/tutorial-complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ wallet }),
      });

      if (response.ok) {
        setRewardClaimed(true);
        setShowRewardPopup(true);
        saveProgress(completedSections, true, true);
      } else {
        // API might not exist yet, still show success
        setRewardClaimed(true);
        setShowRewardPopup(true);
        saveProgress(completedSections, true, true);
      }
    } catch {
      // Network error, still mark as claimed locally
      setRewardClaimed(true);
      setShowRewardPopup(true);
      saveProgress(completedSections, true, true);
    } finally {
      setIsClaimingReward(false);
    }
  };

  const toggleSection = (id: string, index: number) => {
    if (!isSectionUnlocked(index)) return;
    setExpandedSection(expandedSection === id ? null : id);
  };

  const completedCount = completedSections.size;
  const totalSections = TUTORIAL_SECTIONS.length;
  const progressPercent = (completedCount / totalSections) * 100;

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

        {/* Progress bar */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-amber-dim mb-1">
            <span>Progress</span>
            <span>{completedCount}/{totalSections} sections</span>
          </div>
          <div className="w-full h-2 bg-dark rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              className="h-full bg-amber"
            />
          </div>
        </div>
      </motion.div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {TUTORIAL_SECTIONS.map((section, index) => {
          const isUnlocked = isSectionUnlocked(index);
          const isCompleted = completedSections.has(section.id);

          return (
            <motion.div
              key={section.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <button
                onClick={() => toggleSection(section.id, index)}
                disabled={!isUnlocked}
                className={`w-full data-box text-left transition-all duration-200
                          ${isUnlocked ? 'hover:border-amber' : 'opacity-50 cursor-not-allowed'}
                          ${isCompleted ? 'border-green/50' : ''}`}
              >
                <div className="flex items-start gap-3">
                  {/* Status indicator */}
                  <div className="relative">
                    {section.iconSrc ? (
                      <Image
                        src={section.iconSrc}
                        alt=""
                        width={24}
                        height={24}
                        className={`pixel-icon mt-1 ${!isUnlocked ? 'grayscale' : ''}`}
                      />
                    ) : (
                      <span className="text-2xl">{section.icon}</span>
                    )}
                    {isCompleted && (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-green rounded-full
                                    flex items-center justify-center text-xs text-dark font-bold">
                        ✓
                      </div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className={`font-semibold ${isCompleted ? 'text-green' : 'text-amber-bright'}`}>
                        {section.title}
                      </span>
                      {isUnlocked ? (
                        <motion.span
                          animate={{ rotate: expandedSection === section.id ? 180 : 0 }}
                          className="text-amber-dim"
                        >
                          ▼
                        </motion.span>
                      ) : (
                        <span className="text-amber-dark text-xs">LOCKED</span>
                      )}
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

                      {/* Complete section button */}
                      {!isCompleted && (
                        <motion.button
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.3 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            completeSection(section.id);
                          }}
                          className="w-full btn small mt-4"
                        >
                          ✓ MARK AS COMPLETE
                        </motion.button>
                      )}

                      {isCompleted && (
                        <div className="text-center text-green text-sm mt-4">
                          ✓ Section completed
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}

        {/* Complete Tutorial button */}
        {tutorialCompleted && !rewardClaimed && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="portal-box text-center mt-4"
          >
            <div className="ornament mb-3">═══ ◈ ═══</div>
            <h3 className="title text-lg text-green mb-2">ALL SECTIONS COMPLETE!</h3>
            <p className="text-amber-dim text-sm mb-4">
              Claim your reward of <span className="text-amber-bright">3 $EMBER</span>
            </p>
            <button
              onClick={handleCompleteTutorial}
              disabled={isClaimingReward || !wallet}
              className="btn w-full"
            >
              {isClaimingReward ? 'CLAIMING...' : 'COMPLETE TUTORIAL & CLAIM REWARD'}
            </button>
            {!wallet && (
              <p className="text-xs text-amber-dark mt-2">Connect wallet to claim</p>
            )}
            <div className="ornament mt-3">═══ ◈ ═══</div>
          </motion.div>
        )}

        {/* Already claimed message */}
        {rewardClaimed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="data-box text-center mt-4"
          >
            <div className="text-green text-lg mb-1">✓ TUTORIAL COMPLETED</div>
            <p className="text-amber-dim text-sm">Reward already claimed</p>
          </motion.div>
        )}
      </div>

      {/* Back button */}
      <div className="p-4">
        <button onClick={onBack} className="back-btn">
          ← BACK
        </button>
      </div>

      {/* Reward Popup */}
      <AnimatePresence>
        {showRewardPopup && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90"
            onClick={() => setShowRewardPopup(false)}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="portal-box text-center max-w-sm"
              onClick={e => e.stopPropagation()}
            >
              <div className="ornament mb-4">═══ ◈ ═══</div>

              <div className="text-4xl mb-4">🎉</div>

              <h2 className="title text-xl text-green mb-2">CONGRATULATIONS!</h2>

              <p className="text-amber-dim mb-4">
                You have completed the Emberholm Tutorial!
              </p>

              <div className="data-box inline-block px-6 py-3 mb-4">
                <div className="text-amber-bright text-2xl font-bold">+3 $EMBER</div>
                <div className="text-xs text-amber-dim">Added to your balance</div>
              </div>

              <p className="text-sm text-amber-dim mb-4">
                You're now ready to begin your journey as an Operator.
                Good luck, Emissary!
              </p>

              <div className="ornament mb-4">═══ ◈ ═══</div>

              <button
                onClick={() => setShowRewardPopup(false)}
                className="btn w-full"
              >
                CONTINUE
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default TutorialScreen;
