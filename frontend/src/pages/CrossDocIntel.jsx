import { useState } from 'react'
import {
  GitCompareArrows, AlertTriangle, Zap, Info, ChevronDown,
  FileWarning, Calendar, Type, Target, BarChart3, ArrowRight,
  CheckCircle2, ShieldAlert, Search,
} from 'lucide-react'
import { useAnalysis } from '../App'
import useCountUp from '../hooks/useCountUp'

/* ── Category config ─────────────────────────────────────── */
const CATEGORY_CFG = {
  field_mismatch:     { label: 'Field Mismatch',     icon: FileWarning,  color: '#FF6630' },
  timeline_conflict:  { label: 'Timeline Conflict',  icon: Calendar,     color: '#FF8C58' },
  terminology_drift:  { label: 'Terminology Drift',  icon: Type,         color: '#9B75FF' },
  requirement_gap:    { label: 'Requirement Gap',     icon: Target,       color: '#FF6630' },
  metric_conflict:    { label: 'Metric Conflict',     icon: BarChart3,    color: '#FF8C58' },
}

const SEVERITY_CFG = {
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

const RELATIONSHIP_COLORS = {
  supports:     { bg: 'rgba(155,117,255,0.12)', border: 'rgba(155,117,255,0.35)', text: 'text-sds-purple-glow' },
  contradicts:  { bg: 'rgba(255,102,48,0.12)',  border: 'rgba(255,102,48,0.4)',   text: 'text-sds-orange' },
  extends:      { bg: 'rgba(155,117,255,0.08)', border: 'rgba(155,117,255,0.25)', text: 'text-sds-purple-glow' },
  depends_on:   { bg: 'rgba(255,140,88,0.08)',  border: 'rgba(255,140,88,0.25)',  text: 'text-sds-orange-light' },
  duplicates:   { bg: 'rgba(100,100,140,0.08)', border: 'rgba(100,100,140,0.25)', text: 'text-sds-muted-light' },
}

/* ── Consistency ring ────────────────────────────────────── */
function ConsistencyRing({ value, delay = 0 }) {
  const counted = useCountUp(value, 1400, delay)
  const r = 40
  const circ = 2 * Math.PI * r
  const offset = circ - (counted / 100) * circ
  const color = value >= 75 ? '#9B75FF' : value >= 50 ? '#FF8C58' : '#FF6630'

  return (
    <div className="relative w-28 h-28 flex items-center justify-center">
      <svg width="112" height="112" className="-rotate-90">
        <circle cx="56" cy="56" r={r} fill="none" stroke="rgba(46,26,106,0.4)" strokeWidth="5" />
        <circle
          cx="56" cy="56" r={r} fill="none"
          stroke={color} strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.4,0,0.2,1)' }}
        />
      </svg>
      <div className="absolute text-center">
        <span className="text-2xl font-black" style={{ color }}>{counted}</span>
        <span className="text-xs" style={{ color }}>%</span>
      </div>
    </div>
  )
}

/* ── Metric card ─────────────────────────────────────────── */
function MetricCard({ label, value, icon: Icon, delay = 0, accent = false }) {
  const counted = useCountUp(value, 1300, delay)
  return (
    <div className="metric-card p-5 animate-fade-in-up opacity-0-init"
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}>
      {accent && (
        <div className="absolute -top-6 -right-6 w-24 h-24 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(255,102,48,0.18) 0%, transparent 70%)' }} />
      )}
      <div className="flex items-start justify-between mb-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: accent ? 'rgba(255,102,48,0.15)' : 'rgba(91,53,196,0.2)' }}>
          <Icon size={14} className={accent ? 'text-sds-orange' : 'text-sds-purple-glow'} />
        </div>
        <span className="text-[10px] text-sds-muted uppercase tracking-widest font-semibold">{label}</span>
      </div>
      <p className={`text-3xl font-black tracking-tight ${accent ? 'text-gradient-orange' : 'text-white'}`}>
        {counted}
      </p>
    </div>
  )
}

/* ── Issue card ──────────────────────────────────────────── */
function IssueCard({ issue, index }) {
  const [expanded, setExpanded] = useState(false)
  const sevCfg = SEVERITY_CFG[issue.severity] || SEVERITY_CFG.LOW
  const catCfg = CATEGORY_CFG[issue.category] || CATEGORY_CFG.field_mismatch
  const CatIcon = catCfg.icon
  const SevIcon = sevCfg.icon

  return (
    <div
      className="rounded-2xl border transition-all cursor-pointer animate-fade-in-up opacity-0-init"
      style={{
        ...sevCfg.card,
        animationDelay: `${index * 60}ms`,
        animationFillMode: 'forwards',
      }}
      onClick={() => setExpanded(e => !e)}
      onMouseEnter={e => e.currentTarget.style.background = sevCfg.hover}
      onMouseLeave={e => e.currentTarget.style.background = sevCfg.card.background}
    >
      {/* Header */}
      <div className="p-5 pb-3">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-start gap-2.5 flex-1 min-w-0">
            <CatIcon size={14} style={{ color: catCfg.color }} className="shrink-0 mt-0.5" />
            <div className="min-w-0">
              <p className="text-sds-white text-xs font-semibold leading-snug">{issue.title}</p>
              <p className="text-sds-muted text-[10px] mt-1 leading-relaxed line-clamp-2">{issue.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-[9px] px-2 py-0.5 rounded-full font-bold"
              style={{ background: `${catCfg.color}20`, color: catCfg.color, border: `1px solid ${catCfg.color}40` }}>
              {catCfg.label}
            </span>
            <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold shrink-0 ${sevCfg.badge}`}>
              {issue.severity}
            </span>
          </div>
        </div>

        {/* Documents involved */}
        <div className="flex items-center gap-2 flex-wrap">
          {(issue.documents || []).map((doc, i) => (
            <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded-md"
              style={{ background: 'rgba(46,26,106,0.5)', border: '1px solid rgba(46,26,106,0.8)', color: '#b0a0d0' }}>
              {doc}
            </span>
          ))}
          {issue.stage_gate && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md ml-auto"
              style={{ background: 'rgba(91,53,196,0.15)', border: '1px solid rgba(91,53,196,0.3)', color: '#9B75FF' }}>
              {issue.stage_gate}
            </span>
          )}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-5 pb-5 pt-2 border-t animate-fade-in"
          style={{ borderColor: sevCfg.card.borderColor }}>
          {/* Evidence */}
          {issue.evidence?.length > 0 && (
            <div className="mb-4">
              <p className="text-[9px] text-sds-muted/60 uppercase tracking-wider mb-2 font-semibold">Evidence</p>
              <div className="space-y-1.5">
                {issue.evidence.map((ev, i) => (
                  <div key={i} className="flex items-start gap-2 text-[11px] text-sds-muted-light">
                    <ArrowRight size={10} className="text-sds-muted/40 shrink-0 mt-0.5" />
                    <span className="font-mono leading-relaxed">{ev}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendation */}
          {issue.recommendation && (
            <div className="rounded-xl p-3"
              style={{ background: 'rgba(155,117,255,0.06)', border: '1px solid rgba(155,117,255,0.2)' }}>
              <p className="text-[9px] text-sds-purple-glow/70 uppercase tracking-wider mb-1 font-semibold">Recommendation</p>
              <p className="text-[11px] text-sds-muted-light leading-relaxed">{issue.recommendation}</p>
            </div>
          )}

          {/* Source badge */}
          <div className="mt-3 flex justify-end">
            <span className="text-[9px] text-sds-muted/40 uppercase tracking-wider">
              {issue.source === 'local_analysis' ? 'Pattern Detection' : 'AI Analysis'}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Cross-reference matrix card ─────────────────────────── */
function MatrixCard({ xref, index }) {
  const rel = RELATIONSHIP_COLORS[xref.relationship] || RELATIONSHIP_COLORS.supports
  return (
    <div
      className="rounded-xl p-4 border transition-all animate-fade-in-up opacity-0-init"
      style={{
        background: rel.bg,
        borderColor: rel.border,
        animationDelay: `${index * 50}ms`,
        animationFillMode: 'forwards',
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[11px] font-mono text-sds-muted-light truncate">{xref.document_a}</span>
        <ArrowRight size={10} className="text-sds-muted/50 shrink-0" />
        <span className="text-[11px] font-mono text-sds-muted-light truncate">{xref.document_b}</span>
      </div>
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${rel.text}`}
          style={{ background: rel.bg, border: `1px solid ${rel.border}` }}>
          {xref.relationship}
        </span>
      </div>
      <p className="text-[11px] text-sds-muted leading-relaxed">{xref.details}</p>
    </div>
  )
}

/* ── Issue section by severity ───────────────────────────── */
function IssueSection({ level, issues }) {
  const cfg = SEVERITY_CFG[level] || SEVERITY_CFG.LOW
  const Icon = cfg.icon
  if (!issues.length) return null

  return (
    <div className="mb-8">
      <div className="flex items-center gap-2.5 mb-4 animate-fade-in">
        <Icon size={14} className={cfg.iconCls} />
        <h2 className={`text-xs font-black uppercase tracking-widest ${cfg.label}`}>{level} Severity</h2>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${cfg.badge}`}>{issues.length}</span>
      </div>
      <div className="grid gap-3">
        {issues.map((issue, i) => <IssueCard key={i} issue={issue} index={i} />)}
      </div>
    </div>
  )
}

/* ── No data state ───────────────────────────────────────── */
function NoDataState() {
  return (
    <div className="glass rounded-2xl p-16 text-center animate-fade-in"
      style={{ border: '1px solid rgba(155,117,255,0.3)', background: 'rgba(155,117,255,0.05)' }}>
      <ShieldAlert size={32} className="text-sds-purple-glow mx-auto mb-4" />
      <p className="text-white text-lg font-semibold">No Cross-Document Data</p>
      <p className="text-sds-muted text-sm mt-1">
        Re-run the pipeline to generate cross-document intelligence.
      </p>
    </div>
  )
}

/* ── Main page ───────────────────────────────────────────── */
export default function CrossDocIntel() {
  const data = useAnalysis()
  const [categoryFilter, setCategoryFilter] = useState('ALL')
  const [search, setSearch] = useState('')

  if (!data) return null

  const crossIntel = data.cross_document_intel
  if (!crossIntel) return (
    <div className="p-8 max-w-screen-xl"><NoDataState /></div>
  )

  const {
    cross_document_issues: allIssues = [],
    cross_reference_matrix: matrix = [],
    consistency_score = 0,
    summary = '',
    total_issues = 0,
    high_severity_count = 0,
    medium_severity_count = 0,
    low_severity_count = 0,
  } = crossIntel

  const categories = ['ALL', ...new Set(allIssues.map(i => i.category).filter(Boolean))]

  const filtered = allIssues.filter(issue => {
    const matchCat = categoryFilter === 'ALL' || issue.category === categoryFilter
    const matchSearch = !search ||
      issue.title?.toLowerCase().includes(search.toLowerCase()) ||
      issue.description?.toLowerCase().includes(search.toLowerCase()) ||
      issue.documents?.some(d => d.toLowerCase().includes(search.toLowerCase()))
    return matchCat && matchSearch
  })

  const high   = filtered.filter(i => i.severity === 'HIGH')
  const medium = filtered.filter(i => i.severity === 'MEDIUM')
  const low    = filtered.filter(i => i.severity === 'LOW')

  return (
    <div className="p-8 max-w-screen-xl">

      {/* ── Header ── */}
      <div className="flex items-start justify-between mb-8 animate-fade-in">
        <div>
          <p className="text-[10px] text-sds-orange uppercase tracking-widest font-bold mb-1">
            Red Duke · Cross-Document Intelligence
          </p>
          <h1 className="text-3xl font-black text-white accent-line mb-4">
            Cross-Document Intelligence
          </h1>
          <p className="text-sds-muted text-sm">
            {total_issues} inconsistencies detected across {(data.documents || []).length} documents
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-sds-muted pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search issues..."
              className="bg-sds-card border border-sds-border text-sds-muted-light text-xs
                         pl-8 pr-4 py-2.5 rounded-xl focus:outline-none focus:border-sds-orange/50
                         placeholder:text-sds-muted/40 w-48 transition-colors"
            />
          </div>
          <div className="relative">
            <select
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
              className="appearance-none bg-sds-card border border-sds-border text-sds-muted text-xs
                         px-4 pr-9 py-2.5 rounded-xl focus:outline-none focus:border-sds-orange/50
                         cursor-pointer hover:border-sds-border-bright transition-colors"
            >
              {categories.map(c => (
                <option key={c} value={c}>
                  {c === 'ALL' ? 'All Categories' : (CATEGORY_CFG[c]?.label || c)}
                </option>
              ))}
            </select>
            <ChevronDown size={12} className="absolute right-3 top-1/2 -translate-y-1/2 text-sds-muted pointer-events-none" />
          </div>
        </div>
      </div>

      {/* ── Summary row ── */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        {/* Consistency ring */}
        <div className="col-span-2 glass glass-hover rounded-2xl p-6 flex items-center gap-6
                        animate-fade-in-up opacity-0-init"
          style={{ animationDelay: '0ms', animationFillMode: 'forwards' }}>
          <ConsistencyRing value={consistency_score} />
          <div>
            <p className="text-[10px] text-sds-muted uppercase tracking-widest font-semibold mb-1">
              Consistency Score
            </p>
            <p className="text-sds-white text-sm font-semibold leading-snug mb-2">
              {consistency_score >= 75 ? 'Documents are well-aligned' :
               consistency_score >= 50 ? 'Moderate inconsistencies found' :
               'Significant mismatches detected'}
            </p>
            <p className="text-sds-muted text-[11px] leading-relaxed">{summary}</p>
          </div>
        </div>

        {/* Metric cards */}
        <MetricCard label="Total Issues" value={total_issues} icon={GitCompareArrows} delay={80} />
        <MetricCard label="High Severity" value={high_severity_count} icon={Zap} delay={160} accent />
        <MetricCard label="Med + Low" value={medium_severity_count + low_severity_count}
          icon={AlertTriangle} delay={240} />
      </div>

      {/* ── Category breakdown ── */}
      <div className="grid grid-cols-5 gap-3 mb-8">
        {Object.entries(CATEGORY_CFG).map(([key, cfg], i) => {
          const count = allIssues.filter(issue => issue.category === key).length
          const Icon = cfg.icon
          return (
            <button
              key={key}
              onClick={() => setCategoryFilter(categoryFilter === key ? 'ALL' : key)}
              className={`glass rounded-xl p-4 text-left transition-all hover:scale-[1.02]
                         animate-fade-in-up opacity-0-init ${categoryFilter === key ? 'ring-1' : ''}`}
              style={{
                animationDelay: `${100 + i * 50}ms`,
                animationFillMode: 'forwards',
                ringColor: cfg.color,
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon size={13} style={{ color: cfg.color }} />
                <span className="text-lg font-black" style={{ color: count > 0 ? cfg.color : '#4a4060' }}>
                  {count}
                </span>
              </div>
              <p className="text-[10px] text-sds-muted font-semibold uppercase tracking-wider">{cfg.label}</p>
            </button>
          )
        })}
      </div>

      {/* ── Issues list ── */}
      {filtered.length === 0 ? (
        <div className="glass rounded-2xl p-16 text-center animate-fade-in"
          style={{ border: '1px solid rgba(155,117,255,0.3)', background: 'rgba(155,117,255,0.05)' }}>
          <CheckCircle2 size={32} className="text-sds-purple-glow mx-auto mb-4" />
          <p className="text-white text-lg font-semibold">No issues found</p>
          <p className="text-sds-muted text-sm mt-1">
            {search || categoryFilter !== 'ALL'
              ? 'Try adjusting your filters.'
              : 'Red Duke found no cross-document inconsistencies.'}
          </p>
        </div>
      ) : (
        <>
          <IssueSection level="HIGH"   issues={high}   />
          <IssueSection level="MEDIUM" issues={medium} />
          <IssueSection level="LOW"    issues={low}    />
        </>
      )}

      {/* ── Cross-Reference Matrix ── */}
      {matrix.length > 0 && (
        <div className="mt-10">
          <div className="flex items-center gap-2.5 mb-5 animate-fade-in">
            <GitCompareArrows size={14} className="text-sds-purple-glow" />
            <h2 className="text-xs font-black uppercase tracking-widest text-sds-purple-glow">
              Cross-Reference Matrix
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold
                             bg-sds-purple-glow/15 text-sds-purple-glow border border-sds-purple-glow/30">
              {matrix.length} relationships
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {matrix.map((xref, i) => (
              <MatrixCard key={i} xref={xref} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
