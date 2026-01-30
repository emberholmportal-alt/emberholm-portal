'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

/**
 * BootSequence - Welcome Operator typewriter screen
 * Shows terminal-style boot messages with typewriter effect
 * Matches portal web design exactly
 */

interface BootSequenceProps {
  onComplete: () => void;
}

export function BootSequence({ onComplete }: BootSequenceProps) {
  const [bootLines, setBootLines] = useState<string[]>([]);
  const [showWelcome, setShowWelcome] = useState(false);
  const [showButton, setShowButton] = useState(false);
  const [currentText, setCurrentText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const bootIndexRef = useRef(0);

  const BOOT_MESSAGES = [
    "INITIALIZING EMBERHOLM PORTAL...",
    "CONNECTING TO ETERNAL FLAME...",
    "SYNCING REALM STATUS...",
    "LOADING EMISSARY DATABASE...",
    "CALIBRATING $EMBER RESONANCE...",
    "ESTABLISHING GUILD LINKS...",
    "",
    "CONNECTION ESTABLISHED",
  ];

  // Typewriter effect for a single line
  const typewriterEffect = (text: string, callback: () => void) => {
    if (!text) {
      callback();
      return;
    }

    setIsTyping(true);
    setCurrentText('');
    let i = 0;

    const typeChar = () => {
      if (i < text.length) {
        setCurrentText(prev => prev + text.charAt(i));
        i++;
        // Random speed between 30-50ms for more natural feel
        const speed = 30 + Math.random() * 20;
        setTimeout(typeChar, speed);
      } else {
        setIsTyping(false);
        callback();
      }
    };

    typeChar();
  };

  // Boot sequence
  useEffect(() => {
    const runBootSequence = () => {
      if (bootIndexRef.current >= BOOT_MESSAGES.length) {
        // All messages done, show welcome
        setTimeout(() => {
          setShowWelcome(true);
          setTimeout(() => setShowButton(true), 800);
        }, 500);
        return;
      }

      const message = BOOT_MESSAGES[bootIndexRef.current];

      if (message === '') {
        // Empty line - just add it
        setBootLines(prev => [...prev, '']);
        bootIndexRef.current++;
        setTimeout(runBootSequence, 300);
      } else {
        typewriterEffect(message, () => {
          setBootLines(prev => [...prev, message]);
          setCurrentText('');
          bootIndexRef.current++;
          setTimeout(runBootSequence, 400);
        });
      }
    };

    // Start boot sequence after a short delay
    const timer = setTimeout(runBootSequence, 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="screen-view flex flex-col min-h-screen p-4 pt-8">
      {/* Terminal header */}
      <div className="mb-4 border-b border-amber-dark pb-2">
        <p className="text-xs text-amber-dim font-mono">
          EMBERHOLM TERMINAL v2.1.4
        </p>
      </div>

      {/* Boot messages */}
      <div className="flex-1 font-mono text-sm space-y-1 overflow-y-auto">
        {bootLines.map((line, index) => (
          <div key={index} className="flex items-center gap-2">
            {line ? (
              <>
                <span className="text-amber-dim">&gt;</span>
                <span className={
                  line === "CONNECTION ESTABLISHED"
                    ? "text-green"
                    : "text-amber"
                }>
                  {line}
                </span>
                {line !== "CONNECTION ESTABLISHED" && (
                  <span className="text-green ml-1">OK</span>
                )}
              </>
            ) : (
              <span>&nbsp;</span>
            )}
          </div>
        ))}

        {/* Current typing line */}
        {isTyping && currentText && (
          <div className="flex items-center gap-2">
            <span className="text-amber-dim">&gt;</span>
            <span className="text-amber">{currentText}</span>
            <span className="inline-block w-2 h-4 bg-amber animate-blink" />
          </div>
        )}
      </div>

      {/* Welcome message */}
      {showWelcome && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="py-6"
        >
          <div className="portal-box mx-auto">
            <div className="ornament">═══ ◈ ═══</div>
            <p className="text-amber-dim text-sm mt-4">TERMINAL ONLINE</p>
            <h1 className="title text-2xl mt-2">WELCOME</h1>
            <h1 className="title text-3xl">OPERATOR</h1>
            <p className="text-amber-dim text-xs mt-4">
              Initializing portal connection...<br />
              Emissary detected.
            </p>
            <div className="ornament mt-4">═══ ◈ ═══</div>
          </div>
        </motion.div>
      )}

      {/* Continue button */}
      {showButton && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="pb-6"
        >
          <button
            onClick={onComplete}
            className="btn w-full"
          >
            [ CONTINUE ]
          </button>
        </motion.div>
      )}

      {/* Blinking cursor when not showing button */}
      {!showButton && !isTyping && bootLines.length < BOOT_MESSAGES.length && (
        <div className="pb-6 flex items-center gap-2">
          <span className="text-amber-dim">&gt;</span>
          <span className="inline-block w-2 h-4 bg-amber animate-blink" />
        </div>
      )}
    </div>
  );
}
