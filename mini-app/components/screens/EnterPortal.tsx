'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * EnterPortal - Initial splash screen
 * Shows random lore phrases with "Enter Portal" button
 */

const LORE_PHRASES = [
  "The Eternal Flame awaits...",
  "Emissaries rise from the ashes...",
  "In the Era of the Flame, legends are forged...",
  "The Void stirs in the shadows...",
  "Six guilds. One destiny.",
  "Ember burns eternal...",
  "The Order of Dawn calls...",
  "Forge Legion steel awaits...",
  "Whispers from the Circle of Mist...",
  "Shadow Guild secrets unfold...",
];

interface EnterPortalProps {
  onEnter: () => void;
}

export function EnterPortal({ onEnter }: EnterPortalProps) {
  const [phrase, setPhrase] = useState(LORE_PHRASES[0]);
  const [fadeKey, setFadeKey] = useState(0);

  useEffect(() => {
    // Rotate phrases every 3 seconds
    const interval = setInterval(() => {
      const randomIndex = Math.floor(Math.random() * LORE_PHRASES.length);
      setPhrase(LORE_PHRASES[randomIndex]);
      setFadeKey(prev => prev + 1);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 text-center">
      {/* Logo / Title */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="mb-8"
      >
        <h1 className="font-alagard text-4xl text-ember-400 text-glow-strong mb-2">
          EMBERHOLM
        </h1>
        <p className="text-ember-400/60 text-sm tracking-widest uppercase">
          Mini App
        </p>
      </motion.div>

      {/* Animated flame icon */}
      <motion.div
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="text-6xl mb-8"
      >
        🔥
      </motion.div>

      {/* Rotating lore phrase */}
      <div className="h-16 flex items-center justify-center mb-12">
        <AnimatePresence mode="wait">
          <motion.p
            key={fadeKey}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="text-ember-400/70 italic font-pixel text-sm max-w-[280px]"
          >
            "{phrase}"
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Enter button */}
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.5 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onEnter}
        className="btn-ember-primary px-8 py-3 text-lg tracking-wider uppercase"
      >
        Enter Portal
      </motion.button>

      {/* Version */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.4 }}
        transition={{ delay: 1 }}
        className="absolute bottom-6 text-xs text-ember-400/40"
      >
        v0.1.0 · Era of the Flame
      </motion.p>
    </div>
  );
}
