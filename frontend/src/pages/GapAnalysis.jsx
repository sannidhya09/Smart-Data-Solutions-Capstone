import { useState } from 'react'
import { Zap, AlertTriangle, ChevronDown, CheckCircle2, Info } from 'lucide-react'
import { useAnalysis } from '../App'

const IMPACT_CFG = {
  HIGH: {
    card:    { borderColor: 'rgba(255,102,48,0.4)', background: 'rgba(255,102,48,0.06)' },
    hover:   'rgba(255,102,48,0.1)',
    badge:   'bg-sds-orange/20 text-sds-orange border border-sds-orange/40',
    label:   'text-sds-orange',
    dot:     'bg-sds-orange',
    icon:    Zap,
    iconCls: 'text-sds-orange',
    num:     'text-sds-orange',
  },
  MEDIUM: {
    card:    { borderColor: 'rgba(255,140,88,0.35)', background: 'rgba(255,140,88,0.04)' },
    hover:   'rgba(255,140,88,0.08)',
    badge:   'bg-sds-orange-light/20 text-sds-orange-light border border-sds-orange-light/35',
    label:   'text-sds-orange-light',
    dot:     'bg-sds-orange-light',
    icon:    AlertTriangle,
    iconCls: 'text-sds-orange-light',
    num:     'text-sds-orange-light',
  },
  LOW: {
    card:    { borderColor: 'rgba(155,117,255,0.3)', background: 'rgba(155,117,255,0.04)' },
    hover:   'rgba(155,117,255,0.08)',
    badge:   'bg-sds-purple-glow/15 text-sds-purple-glow border border-sds-purple-glow/30',
    label:   'text-sds-purple-glow',
    dot:     'bg-sds-purple-glow',
    icon:    Info,
    iconCls: 'text-sds-purple-glow',
    num:     'text-sds-purple-glow',
  },
}

function GapCard({ gap, index }) {
  const cfg = IMPACT_CFG[gap.impact] || IMPACT_CFG.LOW
  const Icon = cfg.icon

  return (
    <div
      className="rounded-2xl p-5 border transition-all cursor-default animate-fade-in-up opacity-0-init"
      style={{
        ...cfg.card,
        animationDelay: `${index * 60}ms`,
        animationFillMode: 'forwards',
      }}
      onMouseEnter={e => e.currentTarget.style.background = cfg.hover}
      onMouseLeave={e => e.currentTarget.style.background = cfg.card.background}
    >
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-2.5">
          <Icon size={13} className={`${cfg.iconCls} shrink-0 mt-0.5`} />
          <p className="text-sds-white text-xs font-semibold leading-snug">{gap.gap}</p>
        </div>
        <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold shrink-0 ${cfg.badge}`}>
          {gap.impact}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 text-[11px]">
        <div>
          <p className="text-sds-muted/60 uppercase tracking-wider mb-1 font-semibold text-[9px]">Stage Gate</p>
          <p className="font-mono text-sds-muted px-1.5 py-0.5 rounded inline-block"
            style={{ background: 'rgba(46,26,106,0.5)', border: '1px solid rgba(46,26,106,0.8)' }}>
            {gap.stage_gate || '—'}
          </p>
        </div>
        <div>
          <p className="text-sds-muted/60 uppercase tracking-wider mb-1 font-semibold text-[9px]">Responsible</p>
          <p className="text-sds-muted-light">{gap.responsible_party || '—'}</p>
        </div>
        <div>
          <p className="text-sds-muted/60 uppercase tracking-wider mb-1 font-semibold text-[9px]">Recommendation</p>
          <p className="text-sds-muted leading-relaxed">{gap.recommendation || '—'}</p>
        </div>
      </div>
    </div>
  )
}

function GapSection({ level, gaps }) {
  const cfg = IMPACT_CFG[level] || IMPACT_CFG.LOW
  const Icon = cfg.icon
  if (!gaps.length) return null

  return (
    <div className="mb-8">
      <div className="flex items-center gap-2.5 mb-4 animate-fade-in">
        <Icon size={14} className={cfg.iconCls} />
        <h2 className={`text-xs font-black uppercase tracking-widest ${cfg.label}`}>{level} Impact</h2>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${cfg.badge}`}>{gaps.length}</span>
      </div>
      <div className="grid gap-3">
        {gaps.map((g, i) => <GapCard key={i} gap={g} index={i} />)}
      </div>
    </div>
  )
}

export default function GapAnalysis() {
  const data = useAnalysis()
  const [stageFilter, setStageFilter] = useState('ALL')

  if (!data) return null

  const { gap_analysis = [], metrics = {} } = data
  const stages = ['ALL', ...new Set(gap_analysis.map(g => g.stage_gate).filter(Boolean))]

  const filtered = stageFilter === 'ALL'
    ? gap_analysis
    : gap_analysis.filter(g => g.stage_gate === stageFilter)

  const high   = filtered.filter(g => g.impact === 'HIGH')
  const medium = filtered.filter(g => g.impact === 'MEDIUM')
  const low    = filtered.filter(g => g.impact === 'LOW')

  return (
    <div className="p-8 max-w-screen-xl">

      {/* Header */}
      <div className="flex items-start justify-between mb-8 animate-fade-in">
        <div>
          <p className="text-[10px] text-sds-orange uppercase tracking-widest font-bold mb-1">
            Red Duke · Risk Intelligence
          </p>
          <h1 className="text-3xl font-black text-white accent-line mb-4">Gap Analysis</h1>
          <p className="text-sds-muted text-sm">
            {gap_analysis.length} gaps identified &middot; {metrics.high_risk_gaps || 0} high-risk
          </p>
        </div>

        {/* Stage gate filter */}
        <div className="relative">
          <select
            value={stageFilter}
            onChange={e => setStageFilter(e.target.value)}
            className="appearance-none bg-sds-card border border-sds-border text-sds-muted text-xs
                       px-4 pr-9 py-2.5 rounded-xl focus:outline-none focus:border-sds-orange/50
                       cursor-pointer hover:border-sds-border-bright transition-colors"
          >
            {stages.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <ChevronDown size={12} className="absolute right-3 top-1/2 -translate-y-1/2 text-sds-muted pointer-events-none" />
        </div>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: 'High Impact',   count: gap_analysis.filter(g => g.impact === 'HIGH').length,   level: 'HIGH' },
          { label: 'Medium Impact', count: gap_analysis.filter(g => g.impact === 'MEDIUM').length, level: 'MEDIUM' },
          { label: 'Low Impact',    count: gap_analysis.filter(g => g.impact === 'LOW').length,    level: 'LOW' },
        ].map(({ label, count, level }, i) => {
          const cfg = IMPACT_CFG[level]
          const Icon = cfg.icon
          return (
            <div
              key={label}
              className="glass glass-hover rounded-2xl p-6 animate-fade-in-up opacity-0-init"
              style={{ animationDelay: `${i * 80}ms`, animationFillMode: 'forwards' }}
            >
              <div className="flex items-center justify-between mb-3">
                <Icon size={14} className={cfg.iconCls} />
                <span className={`text-[10px] font-bold uppercase tracking-widest ${cfg.label}`}>{label}</span>
              </div>
              <p className={`text-4xl font-black ${cfg.num}`}>{count}</p>
            </div>
          )
        })}
      </div>

      {/* No gaps */}
      {filtered.length === 0 && (
        <div className="glass rounded-2xl p-16 text-center animate-fade-in"
          style={{ border: '1px solid rgba(155,117,255,0.3)', background: 'rgba(155,117,255,0.05)' }}>
          <CheckCircle2 size={32} className="text-sds-purple-glow mx-auto mb-4" />
          <p className="text-white text-lg font-semibold">No gaps found</p>
          <p className="text-sds-muted text-sm mt-1">
            {stageFilter !== 'ALL' ? `No gaps for ${stageFilter}` : 'Red Duke found no deliverable gaps.'}
          </p>
        </div>
      )}

      {/* Gap sections */}
      <GapSection level="HIGH"   gaps={high}   />
      <GapSection level="MEDIUM" gaps={medium} />
      <GapSection level="LOW"    gaps={low}    />
    </div>
  )
}
