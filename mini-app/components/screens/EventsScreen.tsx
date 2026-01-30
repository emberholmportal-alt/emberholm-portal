'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';
import { getEvents, GameEvent, EventSettings } from '@/lib/api';

/**
 * EventsScreen - Active events from the backend
 * Loads real events from /api/events endpoint
 */

interface EventsScreenProps {
  wallet: string | null;
  onBack: () => void;
}

// Difficulty color mapping
const DIFFICULTY_COLORS: Record<string, string> = {
  EASY: 'text-green-400',
  MEDIUM: 'text-amber',
  HARD: 'text-orange-400',
  HEROIC: 'text-purple-400',
  LEGENDARY: 'text-amber-bright',
};

export function EventsScreen({ wallet, onBack }: EventsScreenProps) {
  const [events, setEvents] = useState<GameEvent[]>([]);
  const [eventSettings, setEventSettings] = useState<EventSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);

  // Load events from API
  useEffect(() => {
    async function loadEvents() {
      setIsLoading(true);
      try {
        const data = await getEvents();
        setEvents(data.events);
        setEventSettings(data.event_settings);
      } catch (error) {
        console.error('Error loading events:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadEvents();
  }, []);

  // Format time remaining
  const formatTimeRemaining = (hours: number): string => {
    if (hours <= 0) return 'Ending soon';
    if (hours < 1) return `${Math.round(hours * 60)}m remaining`;
    if (hours < 24) return `${Math.round(hours)}h remaining`;
    const days = Math.floor(hours / 24);
    const remainingHours = Math.round(hours % 24);
    return `${days}d ${remainingHours}h remaining`;
  };

  // Format date
  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="screen-view flex flex-col min-h-screen">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 text-center"
      >
        <h1 className="title text-2xl">EVENTS</h1>
        <p className="subtitle">Active realm events</p>
      </motion.div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading ? (
          <div className="text-center py-8 text-amber-dim">Loading events...</div>
        ) : events.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="portal-box text-center py-8"
          >
            <Image
              src="/icons/scroll.png"
              alt=""
              width={48}
              height={48}
              className="pixel-icon mx-auto mb-4 opacity-50"
            />
            <div className="text-amber-dim mb-2">No Active Events</div>
            <div className="text-xs text-amber-dark">
              Check back soon for new realm events!
            </div>
          </motion.div>
        ) : (
          <>
            {/* Event Settings Banner */}
            {eventSettings && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="data-box text-center text-xs"
              >
                <span className="text-amber-dim">Bonus Multiplier: </span>
                <span className="text-amber-bright">{eventSettings.bonus_multiplier}x</span>
              </motion.div>
            )}

            {/* Events List */}
            {events.map((event, index) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="portal-box">
                  <div className="ornament text-sm">═══ ◈ ═══</div>

                  {/* Event Header */}
                  <div className="my-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-xs font-semibold ${DIFFICULTY_COLORS[event.difficulty] || 'text-amber'}`}>
                        {event.difficulty}
                      </span>
                      {event.time_remaining_hours !== undefined && (
                        <span className="text-xs text-amber-dim">
                          {formatTimeRemaining(event.time_remaining_hours)}
                        </span>
                      )}
                    </div>
                    <h3 className="title text-lg">{event.name}</h3>
                  </div>

                  {/* Description */}
                  <p className="text-amber-dim text-sm mb-4">{event.description}</p>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-2 mb-4">
                    <div className="data-box text-center">
                      <div className="text-xs text-amber-dark">Duration</div>
                      <div className="text-amber-bright font-semibold">{event.duration_hours}h</div>
                    </div>
                    <div className="data-box text-center">
                      <div className="text-xs text-amber-dark">Energy</div>
                      <div className="text-amber-bright font-semibold">{event.energy_cost}</div>
                    </div>
                    <div className="data-box text-center">
                      <div className="text-xs text-amber-dark">XP Reward</div>
                      <div className="text-green-400 font-semibold">+{event.reward_xp}</div>
                    </div>
                    <div className="data-box text-center">
                      <div className="text-xs text-amber-dark">Aura Reward</div>
                      <div className="text-cyan-400 font-semibold">+{event.reward_aura}</div>
                    </div>
                  </div>

                  {/* Success Rate & Death Chance */}
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-amber-dim">Success Rate:</span>
                    <span className="text-green-400">{event.success_rate}%</span>
                  </div>
                  {event.death_chance > 0 && (
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-amber-dim">Death Chance:</span>
                      <span className="text-red-400">{event.death_chance}%</span>
                    </div>
                  )}

                  {/* Favored Bonuses */}
                  {(event.favored_guild || event.favored_class || event.favored_race) && (
                    <div className="data-box mt-3">
                      <div className="text-xs text-amber-dark uppercase mb-1">Favored Bonuses</div>
                      <div className="space-y-1 text-sm">
                        {event.favored_guild && (
                          <div className="flex justify-between">
                            <span className="text-amber-dim">Guild:</span>
                            <span className="text-amber">{event.favored_guild}</span>
                          </div>
                        )}
                        {event.favored_class && (
                          <div className="flex justify-between">
                            <span className="text-amber-dim">Class:</span>
                            <span className="text-amber">{event.favored_class}</span>
                          </div>
                        )}
                        {event.favored_race && (
                          <div className="flex justify-between">
                            <span className="text-amber-dim">Race:</span>
                            <span className="text-amber">{event.favored_race}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Expandable Lore Section */}
                  <button
                    onClick={() => setExpandedEvent(expandedEvent === event.id ? null : event.id)}
                    className="w-full mt-4 text-amber-dim text-xs hover:text-amber transition-colors"
                  >
                    {expandedEvent === event.id ? '▲ Hide Lore' : '▼ Read Lore'}
                  </button>

                  <AnimatePresence>
                    {expandedEvent === event.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-3 mt-3 border-t border-amber-dark/30">
                          <p className="text-amber-dim text-sm italic leading-relaxed">
                            "{event.lore}"
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Event Dates */}
                  <div className="mt-4 pt-3 border-t border-amber-dark/30 text-xs text-amber-dark">
                    <div className="flex justify-between">
                      <span>Started: {formatDate(event.available_from)}</span>
                      <span>Ends: {formatDate(event.available_until)}</span>
                    </div>
                  </div>

                  <div className="ornament text-sm mt-4">═══ ◈ ═══</div>
                </div>
              </motion.div>
            ))}
          </>
        )}
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

export default EventsScreen;
