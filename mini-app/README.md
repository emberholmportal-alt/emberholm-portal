# Emberholm Mini App

A Farcaster Mini App for the Emberholm Portal game. Built with Next.js 14, React 18, and Three.js.

## Overview

The Emberholm Mini App brings the full Emberholm Portal experience to Farcaster frames. Players can manage their Emissaries, complete missions, earn $PYRE tokens, and connect with other players worldwide through a 3D interactive globe.

## Features

- **CRT Visual Style**: Authentic retro computer terminal aesthetic with scanlines, vignette, and glow effects
- **3D Interactive Globe**: Three.js powered globe showing player distribution worldwide
- **Mission System**: Full missions (1-24h) and micro-missions (1-5 min)
- **Social Features**: Country-based player discovery and 1:1 chat
- **Token Economy**: $EMBER, $ASH, and $PYRE token management
- **Emissary Management**: View, equip, and send Emissaries on missions

## Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Environment Variables

Create a `.env.local` file in the root directory:

```env
# API Base URL (Flask backend)
NEXT_PUBLIC_API_URL=http://localhost:5000

# Optional: Farcaster Frame metadata
NEXT_PUBLIC_FRAME_URL=https://your-domain.com
```

## Project Structure

```
mini-app/
├── app/
│   ├── page.tsx          # Main app with navigation
│   ├── layout.tsx        # Root layout with providers
│   └── globals.css       # Global styles + CRT effects
├── components/
│   ├── screens/          # All screen components
│   │   ├── WelcomeScreen.tsx
│   │   ├── CountrySelect.tsx
│   │   ├── PortalEntry.tsx
│   │   ├── MainMenu.tsx
│   │   ├── PlayScreen.tsx
│   │   ├── EmissaryList.tsx
│   │   ├── EmissaryDetail.tsx
│   │   ├── MissionsScreen.tsx
│   │   ├── MicroMissionsScreen.tsx
│   │   ├── MissionPlayer.tsx
│   │   ├── TimerScreen.tsx
│   │   ├── LeaderboardScreen.tsx
│   │   ├── SocialGlobe.tsx
│   │   ├── SocialUsers.tsx
│   │   ├── ChatScreen.tsx
│   │   ├── VaultScreen.tsx
│   │   ├── MintScreen.tsx
│   │   ├── EventsScreen.tsx
│   │   ├── LoreScreen.tsx
│   │   ├── TutorialScreen.tsx
│   │   └── PyreGuide.tsx
│   ├── ui/               # Reusable UI components
│   │   ├── DataBox.tsx
│   │   ├── ProgressBar.tsx
│   │   ├── Modal.tsx
│   │   ├── TabBar.tsx
│   │   ├── ChatBubble.tsx
│   │   ├── EmissaryCard.tsx
│   │   ├── StatDisplay.tsx
│   │   └── ItemPopup.tsx
│   ├── CRTOverlay.tsx    # CRT visual effects
│   ├── ImmersionBar.tsx  # Top status bar
│   ├── Globe3D.tsx       # Three.js globe component
│   └── index.ts          # Component exports
├── lib/
│   ├── api.ts            # API client functions
│   ├── store.ts          # Global state (Context + Reducer)
│   └── hooks/
│       ├── useChat.ts    # Chat polling hook
│       ├── useGlobe.ts   # Globe utilities
│       └── useSound.ts   # Sound effects hook
└── public/
    └── sounds/           # Sound effect files
```

## Screens

| Screen | Route | Description |
|--------|-------|-------------|
| Welcome | `welcome` | Entry screen with "Enter the Portal" |
| Country Select | `country-select` | Choose your country |
| Portal Entry | `portal-entry` | Animated portal transition |
| Main Menu | `menu` | 6 main navigation options |
| Play | `play` | Play submenu (Missions, Emissaries, etc.) |
| Emissary List | `emissary-list` | View owned Emissaries |
| Emissary Detail | `emissary-detail` | Emissary stats and equipment |
| Missions | `missions` | Normal missions (1-24h) |
| Micro-Missions | `micro-missions` | Quick missions (1-5 min) |
| Mission Player | `timer` | Active mission with narrative |
| Timer | `timer` | Mission countdown |
| Leaderboard | `leaderboard` | Global rankings |
| Social Globe | `social-globe` | 3D globe with player markers |
| Social Users | `social-users` | Users from selected country |
| Chat | `chat` | 1:1 private messaging |
| Vault | `vault` | Tokens, items, runes |
| Mint | `mint` | Mint new Emissaries |
| Events | `events` | Active and past events |
| Lore | `lore` | World history |
| Tutorial | `tutorial` | Game guide |
| $PYRE Guide | `pyre-guide` | $PYRE token documentation |

## API Endpoints Used

### Realm
- `GET /api/realm-status` - Realm time, weather, flame state

### Player
- `GET /api/player/{wallet}` - Player data and Emissaries
- `POST /api/social/profile` - Update profile

### $PYRE
- `GET /api/pyre/{wallet}` - $PYRE balance
- `GET /api/pyre/history/{wallet}` - Transaction history

### Micro-Missions
- `GET /api/micro-missions` - List available missions
- `GET /api/micro-mission/{id}` - Mission details
- `POST /api/micro-mission/start` - Start a mission
- `POST /api/micro-mission/choice` - Submit narrative choice
- `POST /api/micro-mission/complete` - Complete and claim rewards
- `GET /api/micro-mission/active/{wallet}` - Check active mission

### Social
- `GET /api/social/countries` - Countries with users (for globe)
- `GET /api/social/country/{code}/users` - Users from country
- `GET /api/social/online-stats` - Global online stats
- `GET /api/social/conversations/{wallet}` - User's conversations
- `GET /api/social/messages/{wallet}/{other}` - Messages with user
- `POST /api/social/message` - Send message
- `POST /api/social/message/read` - Mark messages as read

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI**: React 18, Framer Motion
- **3D**: Three.js, React Three Fiber, Drei
- **State**: React Context + useReducer
- **Styling**: Tailwind CSS
- **Web3**: Wagmi, Viem, RainbowKit

## Development

### Running locally

1. Start the Flask backend on port 5000
2. Run `npm run dev` in the mini-app directory
3. Open http://localhost:3000

### Mobile testing

The app is optimized for 420px width (Farcaster frame size). Use browser dev tools to test mobile view.

## License

Copyright Emberholm Portal. All rights reserved.
