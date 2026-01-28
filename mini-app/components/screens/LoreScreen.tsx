'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * LoreScreen - World lore and story
 */

interface LoreScreenProps {
  onBack: () => void;
}

interface LoreSection {
  id: string;
  title: string;
  icon: string;
  content: string[];
}

const LORE_SECTIONS: LoreSection[] = [
  {
    id: 'dying-flame',
    title: 'THE DYING FLAME',
    icon: '🔥',
    content: [
      'In the heart of Emberholm burns the Eternal Flame, the source of all magic and life in the realm. For millennia, it blazed with power unmatched, but now it flickers and fades.',
      'The Ashen Blight spreads across the land, turning once-verdant forests into fields of grey dust. Villages fall silent, their inhabitants transformed into hollow husks.',
      'Only the Emissaries, those chosen by the Flame itself, can venture into the corrupted zones and gather the Ember—fragments of pure flame energy—needed to restore the dying light.',
      'Time is running out. Each day the Flame grows weaker, and the Blight grows stronger. The fate of Emberholm rests in the hands of the brave.',
    ],
  },
  {
    id: 'emissaries',
    title: 'THE EMISSARIES',
    icon: '⚔️',
    content: [
      'Emissaries are chosen warriors marked by the Eternal Flame. Each bears a unique brand that grants them resistance to the Ashen Blight and the ability to channel Ember energy.',
      'They are not born—they are made. In a ritual of fire and ash, ordinary mortals are transformed into vessels of flame, gaining powers beyond normal comprehension.',
      'But this power comes at a cost. Emissaries are bound to the Flame. If they stray too far from its influence, or if the Flame dies, they too will be consumed.',
      'Each Emissary is unique, with their own strengths, weaknesses, and destiny. Some will become legends. Others will fall, their stories lost to ash.',
    ],
  },
  {
    id: 'guilds',
    title: 'THE SIX GUILDS',
    icon: '🏰',
    content: [
      'PYREGUARD: The defenders. Masters of protective magic and martial prowess. They guard the remaining sanctuaries of light.',
      'ASHWALKERS: The explorers. Scouts who map the Blighted zones and recover lost artifacts from the ash.',
      'EMBERCOURT: The diplomats. Noble houses that maintain order and broker peace between the guilds.',
      'CINDERKIN: The rebels. Outcasts who believe the old ways must burn before new ones can rise.',
      'FLAMEKEEPERS: The scholars. Keepers of ancient knowledge, seeking the secrets to restore the Flame.',
      'SCORCHLORDS: The warriors. Elite combatants who lead the charge against the Blight\'s darkest creatures.',
    ],
  },
  {
    id: 'economy',
    title: 'THE EMBER ECONOMY',
    icon: '💰',
    content: [
      '$EMBER: The primary currency of Emberholm. Fragments of the Eternal Flame crystallized into tradeable tokens. Earned through missions and quests.',
      '$ASH: Created by burning $EMBER. While less valuable, $ASH has unique properties—it can unlock certain ancient artifacts and is required for dark rituals.',
      '$PYRE: Reputation tokens earned through social interaction and community participation. Cannot be traded, but grants access to exclusive rewards.',
      'The economy is cyclical: Ember is gathered, some is burned to create Ash, and both flow back into the system through trade and tribute to the Flame.',
    ],
  },
  {
    id: 'ranks',
    title: 'THE RANKS',
    icon: '📊',
    content: [
      'Emissaries progress through ranks as they gain experience and prove their worth:',
      'KINDLING (Levels 1-5): New Emissaries learning the basics of survival.',
      'SPARK (Levels 6-15): Competent warriors capable of standard missions.',
      'FLAME (Levels 16-30): Experienced fighters who can tackle dangerous zones.',
      'BLAZE (Levels 31-50): Elite Emissaries known throughout the realm.',
      'INFERNO (Levels 51-75): Legendary warriors whose names are spoken with reverence.',
      'ETERNAL (Levels 76+): The rarest rank. Those who have touched the Flame itself.',
    ],
  },
  {
    id: 'permadeath',
    title: 'PERMADEATH',
    icon: '💀',
    content: [
      'In Emberholm, death is real. When an Emissary falls in battle against the Blight, they do not simply respawn—they are consumed by the very darkness they fought against.',
      'Permadeath is the ultimate risk. Your Emissary can die permanently, losing all progress, equipment, and accumulated Ember.',
      'However, death is not the end. Fallen Emissaries leave behind their Legacy—a portion of their power that can be inherited by future warriors.',
      'Choose your battles wisely. Know when to fight and when to retreat. The bravest are not always the ones who charge forward, but those who live to fight another day.',
      'Some say the Fallen watch from the Ashlands, waiting for the day when the Flame is restored and they can rise again...',
    ],
  },
];

export function LoreScreen({ onBack }: LoreScreenProps) {
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
        <h1 className="title text-2xl">LORE</h1>
        <p className="subtitle">The history of Emberholm</p>
      </motion.div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {LORE_SECTIONS.map((section, index) => (
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
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{section.icon}</span>
                  <span className="text-amber-bright font-semibold">
                    {section.title}
                  </span>
                </div>
                <motion.span
                  animate={{ rotate: expandedSection === section.id ? 180 : 0 }}
                  className="text-amber-dim"
                >
                  ▼
                </motion.span>
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
                  <div className="portal-box mt-2 space-y-4">
                    {section.content.map((paragraph, pIndex) => (
                      <motion.p
                        key={pIndex}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: pIndex * 0.1 }}
                        className="text-amber-dim text-sm leading-relaxed"
                      >
                        {paragraph}
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

export default LoreScreen;
