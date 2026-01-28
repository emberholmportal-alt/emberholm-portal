'use client';

/**
 * CRTOverlay - Visual effects overlay
 * Adds scanlines, vignette, and moving scanline for retro CRT feel
 */

export function CRTOverlay() {
  return (
    <>
      {/* Static scanlines */}
      <div className="crt-scanlines pointer-events-none fixed inset-0 z-[9998]" />

      {/* Vignette effect */}
      <div className="crt-vignette pointer-events-none fixed inset-0 z-[9997]" />

      {/* Moving scanline */}
      <div className="crt-moving-line pointer-events-none fixed inset-0 z-[9996]" />
    </>
  );
}
