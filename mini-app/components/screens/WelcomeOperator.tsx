'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

/**
 * WelcomeOperator - Boot sequence screen
 * Typewriter effect with system initialization messages
 */

const BOOT_MESSAGES = [
  { text: "INITIALIZING EMBERHOLM PORTAL...", delay: 0 },
  { text: "CONNECTING TO ETERNAL FLAME...", delay: 800 },
  { text: "SYNCING REALM STATUS...", delay: 1600 },
  { text: "LOADING EMISSARY DATABASE...", delay: 2400 },
  { text: "CALIBRATING $SPARK RESONANCE...", delay: 3200 },
  { text: "ESTABLISHING GUILD LINKS...", delay: 4000 },
  { text: "", delay: 4800 },
  { text: "CONNECTION ESTABLISHED", delay: 5000 },
  { text: "", delay: 5500 },
];

interface WelcomeOperatorProps {
  onComplete: () => void;
}

export function WelcomeOperator({ onComplete }: WelcomeOperatorProps) {
  const [visibleMessages, setVisibleMessages] = useState<string[]>([]);
  const [showWelcome, setShowWelcome] = useState(false);
  const [showButton, setShowButton] = useState(false);

  useEffect(() => {
    // Show messages sequentially
    BOOT_MESSAGES.forEach(({ text, delay }) => {
      setTimeout(() => {
        setVisibleMessages(prev => [...prev, text]);
      }, delay);
    });

    // Show welcome message
    setTimeout(() => {
      setShowWelcome(true);
    }, 5800);

    // Show continue button
    setTimeout(() => {
      setShowButton(true);
    }, 6500);
  }, []);

  return (
    <div className="flex flex-col min-h-screen p-4 pt-12">
      {/* Terminal header */}
      <div className="mb-4 border-b border-ember-400/30 pb-2">
        <p className="text-xs text-ember-400/60 font-mono">
          EMBERHOLM TERMINAL v1.0
        </p>
      </div>

      {/* Boot messages */}
      <div className="flex-1 font-mono text-sm space-y-1">
        {visibleMessages.map((msg, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
            className="flex items-center gap-2"
          >
            {msg ? (
              <>
                <span className="text-ember-400/50">&gt;</span>
                <span className={
                  msg === "CONNECTION ESTABLISHED"
                    ? "text-green-500"
                    : "text-ember-400/80"
                }>
                  {msg}
                </span>
                {msg !== "CONNECTION ESTABLISHED" && msg !== "" && (
                  <span className="text-green-500 ml-1">✓</span>
                )}
              </>
            ) : (
              <span>&nbsp;</span>
            )}
          </motion.div>
        ))}
      </div>

      {/* Welcome message */}
      {showWelcome && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="text-center py-8"
        >
          <h2 className="font-alagard text-2xl text-ember-400 text-glow mb-2">
            WELCOME, OPERATOR
          </h2>
          <p className="text-ember-400/60 text-sm">
            The Realm of Emberholm awaits your command
          </p>
        </motion.div>
      )}

      {/* Continue button */}
      {showButton && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="pb-8"
        >
          <button
            onClick={onComplete}
            className="w-full btn-ember-primary py-3 text-center"
          >
            PROCEED TO COMMAND CENTER
          </button>
        </motion.div>
      )}

      {/* Blinking cursor */}
      {!showButton && (
        <div className="pb-8">
          <span className="inline-block w-2 h-4 bg-ember-400 animate-blink" />
        </div>
      )}
    </div>
  );
}
