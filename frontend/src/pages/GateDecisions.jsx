import { useState } from 'react'
import {
  ShieldCheck, ShieldAlert, ShieldQuestion, AlertTriangle, CheckCircle2,
  XCircle, Clock, ChevronDown, ChevronRight, Lock, Unlock, ArrowRight,
  Target, TrendingUp, Ban,
} from 'lucide-react'
import { useAnalysis } from '../App'
import useCountUp from '../hooks/useCountUp'

const GATE_ORDER = ['TG-1', 'TG0', 'TG1', 'TG2', 'TG3']
const GATE_LABELS = {
  'TG-1': { short: 'TG-1', full: 'TG-1 · Initiation',        desc: 'Project kickoff, BRD, planning' },
  'TG0':  { short: 'TG0',  full: 'TG0 · Design',              desc: 'Workflow diagrams, data mapping, tech specs' },
  'TG1':  { short: 'TG1',  full: 'TG1 · Implementation',      desc: 'Config docs, workbooks, SLA setup' },
  'TG2':  { short: 'TG2',  full: 'TG2 · Test',                desc: 'UAT, compliance, volume testing' },
  'TG3':  { short: 'TG3',  full: 'TG3 · Deploy / Warranty',   desc: 'Go-live, warranty, handoff' },
}

const DECISION_CFG = {
  'GO': {
    color:    '#9B75FF',
    bg:       'rgba(155,117,255,0.08)',
    border:   'rgba(155,117,255,0.35)',
    badge:    'bg-sds-purple-glow/20 text-sds-purple-glow border border-sds-purple-glow/40',
    icon:     ShieldCheck,
    iconCls:  'text-sds-purple-glow',
    label:    'GO',
    ringGlow: 'rgba(155,117,255,0.25)',
  },
  'CONDITIONAL': {
    color:    '#FF8C58',
    bg:       'rgba(255,140,88,0.06)',
    border:   'rgba(255,140,88,0.35)',
    badge:    'bg-sds-orange-light/20 text-sds-orange-light border border-sds-orange-light/40',
    icon:     ShieldQuestion,
    iconCls:  'text-sds-orange-light',
    label:    'CONDITIONAL',
    ringGlow: 'rgba(255,140,88,0.25)',
  },
  'NO-GO': {
    color:    '#FF6630',
    bg:       'rgba(255,102,48,0.06)',
    border:   'rgba(255,102,48,0.4)',
    badge:    'bg-sds-orange/20 text-sds-orange border border-sds-orange/40',
    icon:     ShieldAlert,
    iconCls:  'text-sds-orange',
    label:    'NO-GO',
    ringGlow: 'rgba(255,102,48,0.25)',
  },
}

/* ── Confidence ring ─────────────────────────────────────── */
function ConfidenceRing({ value, color, size = 64 }) {
  const counted = useCountUp(value, 1200, 100)
  const r = (size / 2) - 6
  const circ = 2 * Math.PI * r
  const offset = circ - (counted / 100) * circ

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(46,26,106,0.4)" strokeWidth="4" />
        <circle
          cx={size/2} cy={size/2} r={r} fill="none"
          stroke={color} strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)' }}
        />
      </svg>
      <div className="absolute text-center">
        <span className="text-sm font-black" style={{ color }}>{counted}</span>
        <span className="text-[8px]" style={{ color }}>%</span>
      </div>
    </div>
  )
}

/* ── Blocker row ─────────────────────────────────────────── */
function BlockerRow({ blocker, index }) {
  const isMet = blocker.status === 'PRESENT'
  const isPartial = blocker.status === 'PARTIAL'

  return (
    <div
      className="flex items-start gap-3 py-3 border-b border-sds-border/15 last:border-0
                 animate-fade-in-up opacity-0-init"
      style={{ animationDelay: `${index * 40}ms`, animationFillMode: 'forwards' }}
    >
      <div className="mt-0.5 shrink-0">
        {isMet ? (
          <Unlock size={12} className="text-sds-purple-glow" />
        ) : isPartial ? (
          <Clock size={12} className="text-sds-orange-light" />
        ) : (
          <Lock size={12} className="text-sds-orange" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-xs text-sds-white font-semibold truncate">{blocker.deliverable}</p>
          <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold shrink-0 ${
            isMet ? 'bg-sds-purple-glow/15 text-sds-purple-glow border border-sds-purple-glow/30' :
            isPartial ? 'bg-sds-orange-light/15 text-sds-orange-light border border-sds-orange-light/30' :
            'bg-sds-orange/15 text-sds-orange border border-sds-orange/30'
          }`}>{blocker.status}</span>
        </div>
        <p className="text-[10px] text-sds-muted">{blocker.owner} · {blocker.effort}</p>
        {blocker.notes && (
          <p className="text-[10px] text-sds-muted/60 mt-1 leading-relaxed line-clamp-2">{blocker.notes}</p>
        )}
      </div>
    </div>
  )
}

/* ── Gate decision card ──────────────────────────────────── */
function GateCard({ gateKey, gateData, index }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = DECISION_CFG[gateData.decision] || DECISION_CFG['NO-GO']
  const Icon = cfg.icon
  const gateInfo = GATE_LABELS[gateKey] || { short: gateKey, full: gateKey, desc: '' }

  const blockers = gateData.blockers || []
  const optionalGaps = gateData.optional_gaps || []
  const highGaps = gateData.high_risk_gaps || []

  return (
    <div
      className="rounded-2xl border transition-all animate-fade-in-up opacity-0-init"
      style={{
        background: cfg.bg,
        borderColor: cfg.border,
        animationDelay: `${index * 100}ms`,
        animationFillMode: 'forwards',
      }}
    >
      {/* Main card */}
      <div
        className="p-6 cursor-pointer"
        onClick={() => setExpanded(e => !e)}
        onMouseEnter={e => e.currentTarget.parentElement.style.boxShadow = `0 0 30px ${cfg.ringGlow}`}
        onMouseLeave={e => e.currentTarget.parentElement.style.boxShadow = ''}
      >
        <div className="flex items-start gap-5">
          {/* Confidence ring */}
          <ConfidenceRing value={gateData.confidence_score || 0} color={cfg.color} />

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-white text-sm font-black tracking-tight">{gateInfo.full}</h3>
              <span className={`text-[10px] px-3 py-1 rounded-full font-black ${cfg.badge}`}>
                <Icon size={10} className="inline -mt-0.5 mr-1" />
                {cfg.label}
              </span>
              <ChevronDown
                size={14}
                className={`text-sds-muted/40 ml-auto transition-transform ${expanded ? 'rotate-180' : ''}`}
              />
            </div>
            <p className="text-[11px] text-sds-muted mb-3">{gateInfo.desc}</p>

            {/* Stats row */}
            <div className="flex items-center gap-6 text-[11px]">
              <div className="flex items-center gap-1.5">
                <TrendingUp size={10} className="text-sds-muted/50" />
                <span className="text-sds-muted">Completion:</span>
                <span className="font-bold" style={{ color: cfg.color }}>{gateData.completion_pct || 0}%</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Target size={10} className="text-sds-muted/50" />
                <span className="text-sds-muted">Blockers:</span>
                <span className="font-bold text-sds-white">
                  {gateData.blockers_met || 0}/{(gateData.blockers_met || 0) + (gateData.blockers_remaining || 0)}
                </span>
                <span className="text-sds-muted">met</span>
              </div>
              {gateData.suggested_delay && gateData.suggested_delay !== 'None' && (
                <div className="flex items-center gap-1.5">
                  <Clock size={10} className="text-sds-muted/50" />
                  <span className="text-sds-muted">Est. delay:</span>
                  <span className="font-bold" style={{ color: cfg.color }}>{gateData.suggested_delay}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Rationale */}
        <div className="mt-4 rounded-xl p-3"
          style={{ background: 'rgba(13,5,32,0.4)', border: '1px solid rgba(46,26,106,0.3)' }}>
          <p className="text-[11px] text-sds-muted-light leading-relaxed">{gateData.rationale}</p>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-6 pb-6 pt-0 animate-fade-in">
          {/* Blockers */}
          {blockers.length > 0 && (
            <div className="mb-5">
              <p className="text-[9px] text-sds-muted/60 uppercase tracking-wider mb-2 font-semibold flex items-center gap-1.5">
                <Lock size={9} /> Required Blockers ({blockers.length})
              </p>
              <div className="rounded-xl overflow-hidden"
                style={{ background: 'rgba(13,5,32,0.3)', border: '1px solid rgba(46,26,106,0.2)' }}>
                <div className="px-4 py-1">
                  {blockers.map((b, i) => <BlockerRow key={i} blocker={b} index={i} />)}
                </div>
              </div>
            </div>
          )}

          {/* Optional gaps */}
          {optionalGaps.length > 0 && (
            <div className="mb-5">
              <p className="text-[9px] text-sds-muted/60 uppercase tracking-wider mb-2 font-semibold flex items-center gap-1.5">
                <AlertTriangle size={9} /> Optional Gaps ({optionalGaps.length})
              </p>
              <div className="space-y-1.5">
                {optionalGaps.map((g, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px] text-sds-muted-light">
                    <ArrowRight size={9} className="text-sds-muted/30 shrink-0" />
                    <span className="truncate">{g.deliverable}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold shrink-0 ${
                      g.status === 'PARTIAL' ? 'bg-sds-orange-light/10 text-sds-orange-light' :
                      'bg-sds-orange/10 text-sds-orange'
                    }`}>{g.status}</span>
                    <span className="text-sds-muted/40 text-[10px] shrink-0">{g.effort}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* High-risk gaps */}
          {highGaps.length > 0 && (
            <div>
              <p className="text-[9px] text-sds-orange uppercase tracking-wider mb-2 font-semibold flex items-center gap-1.5">
                <Ban size={9} /> High-Risk Gaps ({highGaps.length})
              </p>
              <div className="space-y-1.5">
                {highGaps.map((g, i) => (
                  <div key={i} className="flex items-start gap-2 text-[11px] text-sds-orange-light">
                    <XCircle size={10} className="text-sds-orange shrink-0 mt-0.5" />
                    <span>{g}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ── No data state ───────────────────────────────────────── */
function NoDataState() {
  return (
    <div className="glass rounded-2xl p-16 text-center animate-fade-in"
      style={{ border: '1px solid rgba(155,117,255,0.3)', background: 'rgba(155,117,255,0.05)' }}>
      <ShieldQuestion size={32} className="text-sds-purple-glow mx-auto mb-4" />
      <p className="text-white text-lg font-semibold">No Gate Decisions Available</p>
      <p className="text-sds-muted text-sm mt-1">
        Re-run the pipeline to generate Go/No-Go recommendations.
      </p>
    </div>
  )
}

/* ── Main page ───────────────────────────────────────────── */
export default function GateDecisions() {
  const data = useAnalysis()

  if (!data) return null

  const gateDecisions = data.gate_decisions
  if (!gateDecisions || Object.keys(gateDecisions).length === 0) {
    return <div className="p-8 max-w-screen-xl"><NoDataState /></div>
  }

  const goCount = Object.values(gateDecisions).filter(g => g.decision === 'GO').length
  const conditionalCount = Object.values(gateDecisions).filter(g => g.decision === 'CONDITIONAL').length
  const noGoCount = Object.values(gateDecisions).filter(g => g.decision === 'NO-GO').length
  const avgConfidence = Math.round(
    Object.values(gateDecisions).reduce((sum, g) => sum + (g.confidence_score || 0), 0) /
    Object.values(gateDecisions).length
  )

  return (
    <div className="p-8 max-w-screen-xl">

      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <p className="text-[10px] text-sds-orange uppercase tracking-widest font-bold mb-1">
          Red Duke · Decision Engine
        </p>
        <h1 className="text-3xl font-black text-white accent-line mb-4">
          Go / No-Go Decisions
        </h1>
        <p className="text-sds-muted text-sm">
          Stage gate readiness assessment with blocker analysis and confidence scoring
        </p>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: 'GO',          count: goCount,          cfg: DECISION_CFG['GO'] },
          { label: 'CONDITIONAL', count: conditionalCount, cfg: DECISION_CFG['CONDITIONAL'] },
          { label: 'NO-GO',      count: noGoCount,        cfg: DECISION_CFG['NO-GO'] },
        ].map(({ label, count, cfg }, i) => {
          const Icon = cfg.icon
          return (
            <div key={label}
              className="glass glass-hover rounded-2xl p-5 animate-fade-in-up opacity-0-init"
              style={{ animationDelay: `${i * 80}ms`, animationFillMode: 'forwards' }}>
              <div className="flex items-center justify-between mb-2">
                <Icon size={14} className={cfg.iconCls} />
                <span className={`text-[10px] font-bold uppercase tracking-widest`}
                  style={{ color: cfg.color }}>{label}</span>
              </div>
              <p className="text-3xl font-black" style={{ color: cfg.color }}>{count}</p>
              <p className="text-sds-muted text-[10px] mt-1">stage gates</p>
            </div>
          )
        })}
        <div className="glass glass-hover rounded-2xl p-5 animate-fade-in-up opacity-0-init"
          style={{ animationDelay: '240ms', animationFillMode: 'forwards' }}>
          <div className="flex items-center justify-between mb-2">
            <TrendingUp size={14} className="text-sds-purple-glow" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-sds-purple-glow">
              Avg Confidence
            </span>
          </div>
          <p className="text-3xl font-black text-white">{avgConfidence}%</p>
          <p className="text-sds-muted text-[10px] mt-1">across all gates</p>
        </div>
      </div>

      {/* Gate cards */}
      <div className="space-y-4">
        {GATE_ORDER.map((key, i) => {
          const gateData = gateDecisions[key]
          if (!gateData) return null
          return <GateCard key={key} gateKey={key} gateData={gateData} index={i} />
        })}
      </div>
    </div>
  )
}
