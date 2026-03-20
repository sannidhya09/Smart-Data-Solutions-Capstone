import { useMemo } from 'react'

/* Deterministic pseudo-random to avoid hydration mismatch */
function seededRand(seed) {
  let s = seed
  return () => {
    s = (s * 16807 + 0) % 2147483647
    return (s - 1) / 2147483646
  }
}

export default function AnimatedBackground() {
  const particles = useMemo(() => {
    const rand = seededRand(42)
    return Array.from({ length: 55 }, (_, i) => ({
      id: i,
      x: rand() * 100,
      y: rand() * 100,
      size: rand() * 6 + 2,
      anim: ['animate-float-1', 'animate-float-2', 'animate-float-3'][i % 3],
      delay: `${(rand() * 8).toFixed(1)}s`,
      opacity: (rand() * 0.55 + 0.15).toFixed(2),
      color: i % 5 === 0 ? '#FF8C58' : i % 4 === 0 ? '#FF6630' : i % 3 === 0 ? '#9B75FF' : '#7B55E0',
      glow: rand() > 0.55,
    }))
  }, [])

  const lines = useMemo(() => {
    const rand = seededRand(99)
    return Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x1: `${rand() * 100}%`,
      y1: `${rand() * 100}%`,
      x2: `${rand() * 100}%`,
      y2: `${rand() * 100}%`,
      opacity: (rand() * 0.18 + 0.04).toFixed(2),
      color: rand() > 0.5 ? '#5B35C4' : '#FF6630',
    }))
  }, [])

  const rings = useMemo(() => {
    const rand = seededRand(77)
    return Array.from({ length: 4 }, (_, i) => ({
      id: i,
      x: rand() * 80 + 10,
      y: rand() * 80 + 10,
      size: rand() * 120 + 60,
      delay: `${(rand() * 4).toFixed(1)}s`,
      color: i % 2 === 0 ? 'rgba(91,53,196,0.25)' : 'rgba(255,102,48,0.18)',
    }))
  }, [])

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden>
      {/* Grid pattern */}
      <div className="absolute inset-0 bg-grid opacity-100" />

      {/* Large glowing orbs */}
      <div className="absolute -top-20 -right-20 w-[650px] h-[650px] rounded-full animate-orb-pulse"
        style={{ background: 'radial-gradient(circle, rgba(91,53,196,0.38) 0%, rgba(91,53,196,0.08) 50%, transparent 70%)' }}
      />
      <div className="absolute -bottom-32 -left-16 w-[500px] h-[500px] rounded-full animate-orb-pulse"
        style={{ background: 'radial-gradient(circle, rgba(255,102,48,0.28) 0%, rgba(255,102,48,0.06) 50%, transparent 70%)', animationDelay: '2.5s' }}
      />
      <div className="absolute top-1/3 left-1/2 w-[420px] h-[420px] rounded-full animate-orb-pulse"
        style={{ background: 'radial-gradient(circle, rgba(123,85,224,0.18) 0%, transparent 65%)', animationDelay: '1.2s' }}
      />
      <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] rounded-full animate-orb-pulse"
        style={{ background: 'radial-gradient(circle, rgba(255,140,88,0.14) 0%, transparent 65%)', animationDelay: '3.8s' }}
      />

      {/* SVG connecting lines + rings */}
      <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
        {lines.map(l => (
          <line
            key={l.id}
            x1={l.x1} y1={l.y1}
            x2={l.x2} y2={l.y2}
            stroke={l.color}
            strokeWidth="0.8"
            opacity={l.opacity}
          />
        ))}
        {rings.map(r => (
          <circle
            key={r.id}
            cx={`${r.x}%`}
            cy={`${r.y}%`}
            r={r.size}
            fill="none"
            stroke={r.color}
            strokeWidth="0.6"
            opacity="0.5"
          />
        ))}
      </svg>

      {/* Floating particles */}
      {particles.map(p => (
        <div
          key={p.id}
          className={`absolute rounded-full ${p.anim}`}
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            background: p.color,
            opacity: p.opacity,
            animationDelay: p.delay,
            filter: p.glow ? `blur(1px) drop-shadow(0 0 ${p.size * 2}px ${p.color})` : `blur(${p.size > 5 ? 1 : 0}px)`,
          }}
        />
      ))}

      {/* Scan line */}
      <div
        className="absolute left-0 right-0 h-px animate-scan-line pointer-events-none"
        style={{
          background: 'linear-gradient(90deg, transparent 0%, rgba(255,102,48,0.6) 35%, rgba(155,117,255,0.7) 65%, transparent 100%)',
        }}
      />

      {/* Secondary scan line (delayed, horizontal bands) */}
      <div
        className="absolute left-0 right-0 h-[2px] animate-scan-line pointer-events-none opacity-30"
        style={{
          background: 'linear-gradient(90deg, transparent 0%, rgba(91,53,196,0.8) 50%, transparent 100%)',
          animationDelay: '4s',
          animationDuration: '10s',
        }}
      />
    </div>
  )
}
