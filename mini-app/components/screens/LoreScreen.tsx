'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';

/**
 * LoreScreen - World lore and story
 * Content from portal web lore sections
 */

interface LoreScreenProps {
  onBack: () => void;
}

interface LoreSection {
  id: string;
  title: string;
  icon: string;
  iconSrc?: string;
  content: string[];
}

const LORE_SECTIONS: LoreSection[] = [
  {
    id: 'beginning',
    title: 'I. THE BEGINNING',
    icon: '',
    iconSrc: '/icons/scroll.png',
    content: [
      'In the age before memory, when the world was young and formless, there existed only the Void—an endless expanse of nothingness where even time held no meaning.',
      'From this primordial darkness emerged a single spark of consciousness, a fragment of pure creative essence that would come to be known as the Eternal Flame.',
      'The Flame burned with an intensity that shattered the silence of eternity. Its light carved pathways through the Void, and from its heat, the first elements were forged.',
      'Mountains rose from nothing, seas filled the valleys, and the sky stretched infinite above. This was the birth of Emberholm—a world shaped by fire and will.',
    ],
  },
  {
    id: 'eternal-flame',
    title: 'II. THE ETERNAL FLAME',
    icon: '',
    iconSrc: '/icons/fire.png',
    content: [
      'At the heart of Emberholm burns the Eternal Flame, the source of all magic and life in the realm. For millennia, it blazed with power unmatched.',
      'But now the Flame flickers and fades. The Ashen Blight spreads across the land, turning once-verdant forests into fields of grey dust.',
      'The Flame\'s power is measured in states: BRIGHT when at full strength, STRONG during prosperous times, STEADY in balance, FLICKERING when threatened, WEAK when danger looms, and DYING when all hope seems lost.',
      'Only through the efforts of Emissaries can the Flame be restored to its former glory.',
    ],
  },
  {
    id: 'emissaries',
    title: 'III. THE EMISSARIES',
    icon: '',
    iconSrc: '/icons/Swords.png',
    content: [
      'Emissaries are chosen warriors marked by the Eternal Flame. Each bears a unique brand that grants them resistance to the Ashen Blight.',
      'They are not born—they are made. In a ritual of fire and ash, ordinary mortals are transformed into vessels of flame, gaining powers beyond normal comprehension.',
      'Each Emissary belongs to one of six races: Human, Elf, Orc, Halfling, Undead, or the rare Dragonborn. Their class determines their path: Warrior, Paladin, Wizard, Rogue, Ranger, or Necromancer.',
      'Some will become legends. Others will fall, their stories lost to ash. Such is the way of Emberholm.',
    ],
  },
  {
    id: 'guilds',
    title: 'IV. THE SIX GUILDS',
    icon: '',
    iconSrc: '/icons/shield.png',
    content: [
      'FORGE LEGION: Masters of metal and fire. Warriors who forge their own destiny in the heat of battle.',
      'CIRCLE OF MIST: Keepers of arcane secrets. Wizards who harness the mystical energies of the realm.',
      'ORDER OF DAWN: Champions of light. Paladins who stand as bulwarks against the encroaching darkness.',
      'SHADOW GUILD: Masters of stealth. Rogues who move unseen and strike from the shadows.',
      'HORIZON WATCH: Wardens of the wild. Rangers who patrol the boundaries between civilization and chaos.',
      'VOID ECHOES: Speakers of death. Necromancers who commune with the spirits beyond the veil.',
    ],
  },
  {
    id: 'permadeath',
    title: 'V. PERMADEATH',
    icon: '',
    iconSrc: '/icons/skull.png',
    content: [
      'In Emberholm, death is real. When an Emissary falls in battle, they can be brought back through the Reinvocation ritual—but at great cost.',
      'Each death weakens the connection to the Flame. The first death costs 500 XP and 100 Aura. The second demands 1,500 XP and 300 Aura. The third takes 5,000 XP and 1,000 Aura.',
      'Beyond the third death, the price becomes astronomical: 10,000 XP and 2,500 Aura. Few can afford such tribute.',
      'Choose your battles wisely. The bravest are not always those who charge forward, but those who live to fight another day.',
    ],
  },
  {
    id: 'ember-lands',
    title: 'VI. THE EMBER LANDS',
    icon: '',
    iconSrc: '/icons/map.gif',
    content: [
      'Emberholm is vast, with territories waiting to be claimed. The Ember Lands system allows operators to conquer and control regions of the realm.',
      'Each land generates resources, provides bonuses to missions, and can be upgraded with structures. Defend your territory from rivals or expand through conquest.',
      'The great houses compete for dominance: whoever controls the most lands holds sway over the realm\'s destiny.',
      'Will you build an empire of flame, or will your ambitions turn to ash?',
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
                  {section.iconSrc ? (
                    <Image
                      src={section.iconSrc}
                      alt=""
                      width={24}
                      height={24}
                      className="pixel-icon"
                    />
                  ) : (
                    <span className="text-2xl">{section.icon}</span>
                  )}
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
