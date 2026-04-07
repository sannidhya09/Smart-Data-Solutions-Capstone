import { useState } from 'react'
import {
  Brain, TrendingUp, Zap, Target, Clock, ArrowRight, Sparkles,
  AlertTriangle, CheckCircle2, FileText, PenLine, ChevronDown,
  Gauge, ShieldCheck, GitCompareArrows, CalendarClock, Rocket,
} from 'lucide-react'
import { useAnalysis } from '../App'
import useCountUp from '../hooks/useCountUp'

const GATE_ORDER = ['TG-1', 'TG0', 'TG1', 'TG2', 'TG3']
const GATE_LABELS = {
  'TG-1': 'Initiation', 'TG0': 'Design', 'TG1': 'Implementation',
  'TG2': 'Test', 'TG3': 'Deploy',
}

const MOMENTUM_CFG = {
  ACCELERATING: { color: '#9B75FF', bg: 'rgba(155,117,255,0.1)', icon: Rocket, label: 'Accelerating' },
  STEADY:       { color: '#9B75FF', bg: 'rgba(155,117,255,0.06)', icon: TrendingUp, label: 'Steady' },
  STALLING:     { color: '#FF8C58', bg: 'rgba(255,140,88,0.08)', icon: Clock, label: 'Stalling' },
  BLOCKED:      { color: '#FF6630', bg: 'rgba(255,102,48,0.1)', icon: AlertTriangle, label: 'Blocked' },
}

const DIM_CFG = {
  completeness: { label: 'Completeness', icon: Gauge,              color: '#9B75FF' },
  quality:      { label: 'Quality',      icon: ShieldCheck,        color: '#7B55E0' },
  consistency:  { label: 'Consistency',   icon: GitCompareArrows,   color: '#FF8C58' },
  freshness:    { label: 'Freshness',     icon: CalendarClock,      color: '#FF6630' },
}

/* ── Score ring ──────────────────────────────────────────── */
function ScoreRing({ value, color, size = 80, label, delay = 0 }) {
  const counted = useCountUp(value, 1400, delay)
  const r = (size / 2) - 6
  const circ = 2 * Math.PI * r
  const offset = circ - (counted / 100) * circ

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(46,26,106,0.4)" strokeWidth="4" />
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="4"
            strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.4,0,0.2,1)' }} />
        </svg>
        <div className="absolute text-center">
          <span className="text-lg font-black" style={{ color }}>{counted}</span>
        </div>
      </div>
      {label && <span className="text-[9px] text-sds-muted uppercase tracking-wider font-semibold">{label}</span>}
    </div>
  )
}

/* ── Dimension bar ───────────────────────────────────────── */
function DimBar({ dim, value, delay = 0 }) {
  const cfg = DIM_CFG[dim]
  const Icon = cfg.icon
  return (
    <div className="flex items-center gap-3 animate-fade-in-up opacity-0-init"
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}>
      <Icon size={12} style={{ color: cfg.color }} className="shrink-0" />
      <span className="text-[10px] text-sds-muted w-24 shrink-0">{cfg.label}</span>
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(46,26,106,0.5)' }}>
        <div className="h-full rounded-full transition-all duration-1000"
          style={{ width: `${Math.max(value, 2)}%`, background: cfg.color }} />
      </div>
      <span className="text-xs font-bold w-8 text-right" style={{ color: cfg.color }}>{value}%</span>
    </div>
  )
}

/* ── Stage readiness card ────────────────────────────────── */
function StageCard({ gate, data, index }) {
  const [expanded, setExpanded] = useState(false)
  const readiness = data?.readiness || 0
  const color = readiness >= 70 ? '#9B75FF' : readiness >= 40 ? '#FF8C58' : '#FF6630'

  return (
    <div
      className="glass rounded-xl p-4 cursor-pointer transition-all hover:scale-[1.01]
                 animate-fade-in-up opacity-0-init"
      style={{ animationDelay: `${index * 80}ms`, animationFillMode: 'forwards' }}
      onClick={() => setExpanded(e => !e)}
    >
      <div className="flex items-center gap-3 mb-3">
        <ScoreRing value={readiness} color={color} size={48} delay={index * 100} />
        <div className="flex-1 min-w-0">
          <p className="text-white text-xs font-bold">{gate} · {GATE_LABELS[gate]}</p>
          <p className="text-sds-muted text-[10px]">{data?.item_count || 0} deliverables</p>
        </div>
        <ChevronDown size={12}
          className={`text-sds-muted/40 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </div>

      {expanded && (
        <div className="space-y-2 pt-2 border-t border-sds-border/20 animate-fade-in">
          {Object.keys(DIM_CFG).map((dim, i) => (
            <DimBar key={dim} dim={dim} value={data?.[dim] || 0} delay={i * 50} />
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Proactive action card ───────────────────────────────── */
function ActionCard({ action, index }) {
  const isCreate = action.type === 'create_deliverable'
  const isComplete = action.type === 'complete_deliverable'
  const isResolve = action.type === 'resolve_inconsistency'

  const accentColor = isCreate ? '#FF6630' : isComplete ? '#FF8C58' : '#9B75FF'
  const TypeIcon = isCreate ? PenLine : isComplete ? Sparkles : GitCompareArrows

  return (
    <div
      className="rounded-xl border p-4 transition-all hover:scale-[1.005]
                 animate-fade-in-up opacity-0-init"
      style={{
        borderColor: `${accentColor}30`,
        background: `${accentColor}08`,
        animationDelay: `${index * 60}ms`,
        animationFillMode: 'forwards',
      }}
    >
      <div className="flex items-start gap-3">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
          style={{ background: `${accentColor}20` }}>
          <span className="text-[10px] font-black" style={{ color: accentColor }}>
            {action.rank}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <TypeIcon size={11} style={{ color: accentColor }} />
            <p className="text-sds-white text-xs font-semibold leading-snug">{action.action}</p>
          </div>
          <p className="text-[10px] text-sds-muted mb-2">{action.owner} · {action.stage_gate} · {action.effort}</p>
          <p className="text-[10px] text-sds-muted/70 leading-relaxed line-clamp-2">{action.reason}</p>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span className="text-[9px] font-bold px-2 py-0.5 rounded-full"
            style={{ background: `${accentColor}15`, color: accentColor, border: `1px solid ${accentColor}30` }}>
            Impact: {action.impact_score}
          </span>
          {action.can_generate_draft && (
            <span className="text-[9px] px-2 py-0.5 rounded-full bg-sds-purple-glow/10 text-sds-purple-glow
                             border border-sds-purple-glow/25 flex items-center gap-1">
              <Sparkles size={8} /> Draft available
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

/* ── Main page ───────────────────────────────────────────── */
export default function ProjectMind() {
  const data = useAnalysis()

  if (!data) return null

  const mind = data.project_mind || {}
  const stageReadiness = data.stage_readiness || {}
  const proactiveActions = data.proactive_actions || []
  const overallReadiness = data.overall_readiness_score || 0
  const momentum = MOMENTUM_CFG[mind.momentum_assessment] || MOMENTUM_CFG.STEADY
  const MomentumIcon = momentum.icon

  return (
    <div className="p-8 max-w-screen-xl">

      {/* ── Header ── */}
      <div className="mb-8 animate-fade-in">
        <p className="text-[10px] text-sds-orange uppercase tracking-widest font-bold mb-1">
          Red Duke · Intelligence Core
        </p>
        <h1 className="text-3xl font-black text-white accent-line mb-4">
          Project Mind
        </h1>
        <p className="text-sds-muted text-sm">
          Unified project intelligence — the system's understanding of where this project stands
        </p>
      </div>

      {/* ── Top: Overall readiness + momentum + critical insight ── */}
      <div className="grid grid-cols-3 gap-5 mb-8">

        {/* Overall readiness */}
        <div className="glass glass-hover rounded-2xl p-6 flex flex-col items-center justify-center
                        animate-fade-in-up opacity-0-init"
          style={{ animationDelay: '0ms', animationFillMode: 'forwards' }}>
          <ScoreRing value={overallReadiness} size={100} delay={0}
            color={overallReadiness >= 70 ? '#9B75FF' : overallReadiness >= 40 ? '#FF8C58' : '#FF6630'} />
          <p className="text-[10px] text-sds-muted uppercase tracking-widest font-semibold mt-3">
            Overall Readiness
          </p>
          <p className="text-sds-muted text-[10px] mt-1">Multi-dimensional composite</p>
        </div>

        {/* Momentum */}
        <div className="glass glass-hover rounded-2xl p-6 animate-fade-in-up opacity-0-init"
          style={{ animationDelay: '100ms', animationFillMode: 'forwards' }}>
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: momentum.bg }}>
              <MomentumIcon size={14} style={{ color: momentum.color }} />
            </div>
            <div>
              <p className="text-[10px] text-sds-muted uppercase tracking-widest font-semibold">Momentum</p>
              <p className="text-sm font-bold" style={{ color: momentum.color }}>{momentum.label}</p>
            </div>
          </div>
          <p className="text-[11px] text-sds-muted-light leading-relaxed mb-3">
            {mind.momentum_reason}
          </p>
          {mind.time_to_next_gate && (
            <div className="flex items-center gap-2 text-[10px]">
              <Clock size={10} className="text-sds-muted/50" />
              <span className="text-sds-muted">Next gate:</span>
              <span className="font-bold text-sds-white">{mind.time_to_next_gate}</span>
            </div>
          )}
          {mind.predicted_bottleneck && (
            <div className="flex items-center gap-2 text-[10px] mt-1.5">
              <AlertTriangle size={10} className="text-sds-orange/60" />
              <span className="text-sds-muted">Bottleneck:</span>
              <span className="font-semibold text-sds-orange-light">{mind.predicted_bottleneck}</span>
            </div>
          )}
        </div>

        {/* Critical insight */}
        <div className="glass glass-hover rounded-2xl p-6 animate-fade-in-up opacity-0-init"
          style={{ animationDelay: '200ms', animationFillMode: 'forwards' }}>
          <div className="flex items-center gap-2 mb-3">
            <Zap size={14} className="text-sds-orange" />
            <p className="text-[10px] text-sds-orange uppercase tracking-widest font-bold">
              Critical Insight
            </p>
          </div>
          <p className="text-sm text-sds-white font-semibold leading-relaxed mb-4">
            {mind.critical_insight}
          </p>
          <div className="rounded-lg p-3"
            style={{ background: 'rgba(255,102,48,0.06)', borderLeft: '2px solid rgba(255,102,48,0.4)' }}>
            <p className="text-[10px] text-sds-muted/60 uppercase tracking-wider mb-1 font-semibold">
              Risk Narrative
            </p>
            <p className="text-[11px] text-sds-muted-light leading-relaxed">{mind.risk_narrative}</p>
          </div>
        </div>
      </div>

      {/* ── Project Understanding ── */}
      {mind.project_understanding && (
        <div className="glass rounded-2xl p-6 mb-8 animate-fade-in" style={{ animationDelay: '150ms' }}>
          <div className="flex items-center gap-2.5 mb-4">
            <Brain size={14} className="text-sds-purple-glow" />
            <h2 className="text-xs font-black uppercase tracking-widest text-sds-purple-glow">
              What Red Duke Understands
            </h2>
          </div>
          <div className="text-sm text-sds-muted-light leading-relaxed space-y-3">
            {mind.project_understanding.split('\n').filter(Boolean).map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
        </div>
      )}

      {/* ── Stage Readiness Scores ── */}
      <div className="mb-8">
        <div className="flex items-center gap-2.5 mb-5 animate-fade-in">
          <Target size={14} className="text-sds-orange" />
          <h2 className="text-xs font-black uppercase tracking-widest text-sds-muted-light">
            Stage Readiness Scores
          </h2>
          <span className="text-[10px] text-sds-muted/40 font-mono ml-2">
            Completeness · Quality · Consistency · Freshness
          </span>
        </div>
        <div className="grid grid-cols-5 gap-3">
          {GATE_ORDER.map((gate, i) => (
            <StageCard key={gate} gate={gate} data={stageReadiness[gate]} index={i} />
          ))}
        </div>
      </div>

      {/* ── Tomorrow Morning / Next Actions ── */}
      {mind.next_actions_narrative && (
        <div className="glass rounded-2xl p-5 mb-8 animate-fade-in"
          style={{ background: 'rgba(91,53,196,0.06)', border: '1px solid rgba(91,53,196,0.25)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Rocket size={13} className="text-sds-purple-glow" />
            <p className="text-[10px] text-sds-purple-glow uppercase tracking-widest font-bold">
              Tomorrow Morning
            </p>
          </div>
          <p className="text-sm text-sds-muted-light leading-relaxed">{mind.next_actions_narrative}</p>
        </div>
      )}

      {/* ── Proactive Actions ── */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-5 animate-fade-in">
          <div className="flex items-center gap-2.5">
            <Sparkles size={14} className="text-sds-orange" />
            <h2 className="text-xs font-black uppercase tracking-widest text-sds-muted-light">
              Proactive Recommendations
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold
                             bg-sds-orange/15 text-sds-orange border border-sds-orange/30">
              {proactiveActions.length} actions
            </span>
          </div>
          <span className="text-[10px] text-sds-muted/40 font-mono">
            Ranked by impact score
          </span>
        </div>

        {proactiveActions.length > 0 ? (
          <div className="space-y-2.5">
            {proactiveActions.map((action, i) => (
              <ActionCard key={i} action={action} index={i} />
            ))}
          </div>
        ) : (
          <div className="glass rounded-2xl p-12 text-center">
            <CheckCircle2 size={28} className="text-sds-purple-glow mx-auto mb-3" />
            <p className="text-white font-semibold">All deliverables accounted for</p>
            <p className="text-sds-muted text-sm mt-1">No proactive actions needed at this time.</p>
          </div>
        )}
      </div>
    </div>
  )
}
