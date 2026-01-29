'use client';

/**
 * Emberholm Icons - SVG icons to replace emojis
 * All icons are designed to match the amber/dark theme
 */

interface IconProps {
  className?: string;
  size?: number;
}

// Fire/Flame icon - replaces 🔥
export function FireIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M12 2C8.5 6 6 9.5 6 13c0 3.5 2.5 6 6 6s6-2.5 6-6c0-3.5-2.5-7-6-11z"
        fill="currentColor"
        opacity="0.3"
      />
      <path
        d="M12 4c2.5 3 4.5 5.5 4.5 9 0 2.5-1.8 4.5-4.5 4.5S7.5 15.5 7.5 13c0-3.5 2-6 4.5-9z"
        fill="currentColor"
      />
      <path
        d="M12 8c1.5 2 2.5 3.5 2.5 5.5 0 1.5-1 2.5-2.5 2.5s-2.5-1-2.5-2.5c0-2 1-3.5 2.5-5.5z"
        fill="currentColor"
        opacity="0.6"
      />
    </svg>
  );
}

// Swords/Combat icon - replaces ⚔️
export function SwordsIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M6.5 3L4 5.5l2.5 2.5L4 10.5 5.5 12l2.5-2.5L10.5 12 12 10.5 9.5 8 12 5.5 10.5 4 8 6.5 5.5 4 6.5 3z"
        fill="currentColor"
      />
      <path
        d="M17.5 3L15 5.5l2.5 2.5L15 10.5 16.5 12l2.5-2.5L21.5 12 23 10.5 20.5 8 23 5.5 21.5 4 19 6.5 16.5 4 17.5 3z"
        fill="currentColor"
      />
      <path
        d="M3 17.5L5.5 15l2.5 2.5L10.5 15 12 16.5l-2.5 2.5L12 21.5 10.5 23 8 20.5 5.5 23 4 21.5 6.5 19 4 16.5 3 17.5z"
        fill="currentColor"
        opacity="0.6"
      />
    </svg>
  );
}

// Lightning/Energy icon - replaces ⚡
export function LightningIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"
        fill="currentColor"
      />
    </svg>
  );
}

// Trophy icon - replaces 🏆
export function TrophyIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M12 17c-2.5 0-4.5-2-4.5-4.5V6h9v6.5c0 2.5-2 4.5-4.5 4.5z"
        fill="currentColor"
      />
      <path
        d="M7.5 6V4.5h9V6h2.5v2.5c0 1.5-1 2.5-2.5 2.5h-1c0 2-1.5 3.5-3.5 3.5S8.5 13 8.5 11h-1c-1.5 0-2.5-1-2.5-2.5V6h2.5z"
        fill="currentColor"
        opacity="0.5"
      />
      <rect x="10" y="17" width="4" height="2" fill="currentColor" />
      <rect x="8" y="19" width="8" height="2" rx="1" fill="currentColor" />
    </svg>
  );
}

// Crown icon - for 1st place
export function CrownIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M3 18h18v2H3v-2z"
        fill="currentColor"
      />
      <path
        d="M5 18l-2-10 5 4 4-7 4 7 5-4-2 10H5z"
        fill="currentColor"
      />
    </svg>
  );
}

// Medal icons for ranks
export function Medal1Icon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <circle cx="12" cy="14" r="7" fill="currentColor" opacity="0.3" />
      <circle cx="12" cy="14" r="5" fill="currentColor" />
      <path d="M9 3l3 6 3-6" stroke="currentColor" strokeWidth="2" fill="none" />
      <text x="12" y="17" textAnchor="middle" fontSize="8" fill="#0a0a0a" fontWeight="bold">1</text>
    </svg>
  );
}

export function Medal2Icon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <circle cx="12" cy="14" r="7" fill="currentColor" opacity="0.3" />
      <circle cx="12" cy="14" r="5" fill="currentColor" />
      <path d="M9 3l3 6 3-6" stroke="currentColor" strokeWidth="2" fill="none" />
      <text x="12" y="17" textAnchor="middle" fontSize="8" fill="#0a0a0a" fontWeight="bold">2</text>
    </svg>
  );
}

export function Medal3Icon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <circle cx="12" cy="14" r="7" fill="currentColor" opacity="0.3" />
      <circle cx="12" cy="14" r="5" fill="currentColor" />
      <path d="M9 3l3 6 3-6" stroke="currentColor" strokeWidth="2" fill="none" />
      <text x="12" y="17" textAnchor="middle" fontSize="8" fill="#0a0a0a" fontWeight="bold">3</text>
    </svg>
  );
}

// Map/Quest icon - replaces 🗺️
export function MapIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M3 5l6 2v12l-6-2V5z"
        fill="currentColor"
        opacity="0.5"
      />
      <path
        d="M9 7l6-2v12l-6 2V7z"
        fill="currentColor"
      />
      <path
        d="M15 5l6 2v12l-6-2V5z"
        fill="currentColor"
        opacity="0.5"
      />
    </svg>
  );
}

// Globe icon - replaces 🌍
export function GlobeIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" fill="none" />
      <ellipse cx="12" cy="12" rx="4" ry="9" stroke="currentColor" strokeWidth="1.5" fill="none" />
      <path d="M3 12h18" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 7h14" stroke="currentColor" strokeWidth="1" opacity="0.5" />
      <path d="M5 17h14" stroke="currentColor" strokeWidth="1" opacity="0.5" />
    </svg>
  );
}

// Vault/Bank icon - replaces 🏦
export function VaultIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <rect x="3" y="8" width="18" height="12" rx="2" fill="currentColor" opacity="0.5" />
      <rect x="5" y="10" width="14" height="8" rx="1" fill="currentColor" />
      <circle cx="12" cy="14" r="3" stroke="currentColor" strokeWidth="2" fill="none" />
      <path d="M6 8V6a6 6 0 0112 0v2" stroke="currentColor" strokeWidth="2" fill="none" />
    </svg>
  );
}

// Calendar/Events icon - replaces 📅
export function CalendarIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <rect x="3" y="6" width="18" height="15" rx="2" fill="currentColor" opacity="0.3" />
      <rect x="3" y="6" width="18" height="5" rx="2" fill="currentColor" />
      <path d="M7 3v4M17 3v4" stroke="currentColor" strokeWidth="2" />
      <rect x="6" y="14" width="3" height="3" fill="currentColor" />
      <rect x="10.5" y="14" width="3" height="3" fill="currentColor" opacity="0.5" />
      <rect x="15" y="14" width="3" height="3" fill="currentColor" opacity="0.5" />
    </svg>
  );
}

// Scroll/Lore icon - replaces 📜
export function ScrollIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M6 3c-1.5 0-3 1-3 2.5v13c0 1.5 1.5 2.5 3 2.5h12c1.5 0 3-1 3-2.5v-13c0-1.5-1.5-2.5-3-2.5H6z"
        fill="currentColor"
        opacity="0.3"
      />
      <path
        d="M6 4h12v16H6c-1 0-2-.5-2-1.5V5.5C4 4.5 5 4 6 4z"
        fill="currentColor"
      />
      <path d="M8 8h8M8 12h6M8 16h4" stroke="#0a0a0a" strokeWidth="1.5" opacity="0.5" />
    </svg>
  );
}

// Question/Help icon - replaces ❓
export function HelpIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <circle cx="12" cy="12" r="9" fill="currentColor" opacity="0.3" />
      <circle cx="12" cy="12" r="7" fill="currentColor" />
      <text x="12" y="16" textAnchor="middle" fontSize="12" fill="#0a0a0a" fontWeight="bold">?</text>
    </svg>
  );
}

// Coin/Money icon - replaces 💰
export function CoinIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <ellipse cx="12" cy="12" rx="8" ry="9" fill="currentColor" opacity="0.3" />
      <ellipse cx="12" cy="12" rx="6" ry="7" fill="currentColor" />
      <text x="12" y="16" textAnchor="middle" fontSize="10" fill="#0a0a0a" fontWeight="bold">$</text>
    </svg>
  );
}

// Chart/Stats icon - replaces 📊
export function ChartIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <rect x="4" y="14" width="4" height="6" fill="currentColor" opacity="0.5" />
      <rect x="10" y="10" width="4" height="10" fill="currentColor" />
      <rect x="16" y="6" width="4" height="14" fill="currentColor" opacity="0.7" />
      <path d="M2 20h20" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

// Pin/Key Points icon - replaces 📌
export function PinIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M12 2c-3 0-6 2.5-6 6 0 4 6 10 6 10s6-6 6-10c0-3.5-3-6-6-6z"
        fill="currentColor"
      />
      <circle cx="12" cy="8" r="2" fill="#0a0a0a" />
    </svg>
  );
}

// Hourglass/Timer icon - replaces ⏱️
export function HourglassIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M6 2h12v4l-4 4 4 4v4H6v-4l4-4-4-4V2z"
        fill="currentColor"
        opacity="0.3"
      />
      <path
        d="M7 3h10v3l-3.5 3.5L17 13v3H7v-3l3.5-3.5L7 6V3z"
        fill="currentColor"
      />
      <rect x="6" y="2" width="12" height="2" fill="currentColor" />
      <rect x="6" y="20" width="12" height="2" fill="currentColor" />
    </svg>
  );
}

// Check/Verified icon - replaces ✓
export function CheckIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M5 12l4 4 10-10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Sparkle/Magic icon - replaces ✨
export function SparkleIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5L12 2z"
        fill="currentColor"
      />
      <path
        d="M18 14l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3z"
        fill="currentColor"
        opacity="0.7"
      />
      <path
        d="M5 14l.7 2.3L8 17l-2.3.7L5 20l-.7-2.3L2 17l2.3-.7L5 14z"
        fill="currentColor"
        opacity="0.5"
      />
    </svg>
  );
}

// Users/Party icon - replaces 👥
export function UsersIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <circle cx="8" cy="8" r="4" fill="currentColor" />
      <path d="M2 20c0-4 3-6 6-6s6 2 6 6" fill="currentColor" opacity="0.5" />
      <circle cx="16" cy="8" r="3" fill="currentColor" opacity="0.7" />
      <path d="M14 20c0-3 2-5 5-5s5 2 5 5" fill="currentColor" opacity="0.3" />
    </svg>
  );
}

// Star/Aura icon - replaces ✧
export function StarIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M12 2l2.4 7.4h7.6l-6 4.6 2.3 7-6.3-4.6-6.3 4.6 2.3-7-6-4.6h7.6L12 2z"
        fill="currentColor"
      />
    </svg>
  );
}

// Power/Combat icon - replaces ⚔ (single sword)
export function PowerIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M14.5 3l-7 7 3.5 3.5-6.5 6.5 1.5 1.5 6.5-6.5 3.5 3.5 7-7L14.5 3z"
        fill="currentColor"
      />
    </svg>
  );
}

// Play icon - replaces ▶
export function PlayIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M6 4l14 8-14 8V4z"
        fill="currentColor"
      />
    </svg>
  );
}

// Diamond/Gem icon - replaces ◈
export function GemIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M12 2L4 9l8 13 8-13-8-7z"
        fill="currentColor"
      />
      <path
        d="M4 9l8 4 8-4"
        stroke="currentColor"
        strokeWidth="1"
        opacity="0.5"
      />
      <path
        d="M12 13v9"
        stroke="currentColor"
        strokeWidth="1"
        opacity="0.5"
      />
    </svg>
  );
}

// Chat/Message icon
export function ChatIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M4 4h16c1 0 2 1 2 2v10c0 1-1 2-2 2H8l-4 4v-4c-1 0-2-1-2-2V6c0-1 1-2 2-2z"
        fill="currentColor"
      />
    </svg>
  );
}

// Ghost icon - for unregistered/unknown users
export function GhostIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <path
        d="M12 2C7 2 3 6 3 11v9c0 1 1 2 2 2 1 0 1.5-.5 2-1s1.5-1 2-1 1.5.5 2 1 1 1 2 1 1.5-.5 2-1 1.5-1 2-1 1.5.5 2 1 1 1 2 1c1 0 2-1 2-2v-9c0-5-4-9-9-9z"
        fill="currentColor"
        opacity="0.3"
      />
      <path
        d="M12 3C8 3 5 6.5 5 11v8c0 .5.5 1 1 1 .5 0 1-.5 1.5-1s1.5-1 2.5-1 2 .5 2.5 1 1 1 1.5 1 1-.5 1.5-1 1.5-1 2.5-1 2 .5 2.5 1 1 1 1.5 1c.5 0 1-.5 1-1v-8c0-4.5-3-8-7-8z"
        fill="currentColor"
      />
      <circle cx="9" cy="11" r="2" fill="#0a0a0a" />
      <circle cx="15" cy="11" r="2" fill="#0a0a0a" />
    </svg>
  );
}

// Wallet icon - for wallet connection
export function WalletIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <rect x="2" y="6" width="20" height="14" rx="2" fill="currentColor" opacity="0.3" />
      <rect x="3" y="7" width="18" height="12" rx="1.5" fill="currentColor" />
      <rect x="14" y="11" width="6" height="4" rx="1" fill="#0a0a0a" />
      <circle cx="17" cy="13" r="1" fill="currentColor" />
      <path d="M4 6V5a2 2 0 012-2h10a2 2 0 012 2v1" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

// NFT/Token icon
export function NftIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <rect x="3" y="3" width="18" height="18" rx="2" fill="currentColor" opacity="0.3" />
      <rect x="4" y="4" width="16" height="16" rx="1.5" fill="currentColor" />
      <path d="M8 12l3 3 5-6" stroke="#0a0a0a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// Export all icons as a map for easy access
export const Icons = {
  fire: FireIcon,
  swords: SwordsIcon,
  lightning: LightningIcon,
  trophy: TrophyIcon,
  crown: CrownIcon,
  medal1: Medal1Icon,
  medal2: Medal2Icon,
  medal3: Medal3Icon,
  map: MapIcon,
  globe: GlobeIcon,
  vault: VaultIcon,
  calendar: CalendarIcon,
  scroll: ScrollIcon,
  help: HelpIcon,
  coin: CoinIcon,
  chart: ChartIcon,
  pin: PinIcon,
  hourglass: HourglassIcon,
  check: CheckIcon,
  sparkle: SparkleIcon,
  users: UsersIcon,
  star: StarIcon,
  power: PowerIcon,
  play: PlayIcon,
  gem: GemIcon,
  chat: ChatIcon,
  ghost: GhostIcon,
  wallet: WalletIcon,
  nft: NftIcon,
};

export default Icons;
