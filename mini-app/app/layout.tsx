import type { Metadata, Viewport } from 'next';
import './globals.css';

const DOMAIN = 'https://miniapp.emberholmportal.xyz';

export const metadata: Metadata = {
  title: 'Emberholm Portal',
  description: 'Medieval fantasy RPG on Base blockchain. Summon Emissaries, complete missions, earn $EMBER.',
  keywords: ['Emberholm', 'NFT', 'Game', 'Farcaster', 'Mini App', 'Base', 'Blockchain', 'RPG'],

  // Open Graph meta tags
  openGraph: {
    title: 'Emberholm Portal',
    description: 'Medieval fantasy RPG on Base blockchain. Summon Emissaries, complete missions, earn $EMBER.',
    url: DOMAIN,
    siteName: 'Emberholm Portal',
    images: [
      {
        url: `${DOMAIN}/embed.png`,
        width: 1200,
        height: 630,
        alt: 'Emberholm Portal - Era of the Flame',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },

  // Twitter Card meta tags
  twitter: {
    card: 'summary_large_image',
    title: 'Emberholm Portal',
    description: 'Medieval fantasy RPG on Base blockchain. Summon Emissaries, complete missions, earn $EMBER.',
    images: [`${DOMAIN}/embed.png`],
  },

  // Farcaster Frame meta tags
  other: {
    'fc:frame': 'vNext',
    'fc:frame:image': `${DOMAIN}/embed.png`,
    'fc:frame:image:aspect_ratio': '1.91:1',
    'fc:frame:button:1': 'Play Now',
    'fc:frame:button:1:action': 'link',
    'fc:frame:button:1:target': DOMAIN,
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#0a0705',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/icon-1024.png" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="bg-void min-h-screen">
        {children}
      </body>
    </html>
  );
}
