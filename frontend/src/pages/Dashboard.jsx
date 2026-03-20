import { TrendingUp, FileText, ShieldCheck, Zap, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'
import { useAnalysis } from '../App'
import useCountUp from '../hooks/useCountUp'

const GATE_ORDER  = ['TG-1', 'TG0', 'TG1', 'TG2', 'TG3']
const GATE_LABELS = {
  'TG-1': 'TG-1 · Initiation',
  'TG0':  'TG0  · Design',
  'TG1':  'TG1  · Implementation',
  'TG2':  'TG2  · Test',
  'TG3':  'TG3  · Deploy / Warranty',
}

/* ── Animated metric card ─────────────────────────────────── */
function MetricCard({ label, value, sub, icon: Icon, delay = 0, accent = false }) {
  const isPercent = String(value).includes('%')
  const num = parseInt(String(value).replace('%', '')) || 0
  const counted = useCountUp(num, 1300, delay)
  const display = isPercent ? `${counted}%` : counted

  return (
    <div className="metric-card p-6 animate-fade-in-up opacity-0-init" style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}>
      {/* Glow spot */}
      {accent && (
        <div className="absolute -top-6 -right-6 w-24 h-24 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(255,102,48,0.18) 0%, transparent 70%)' }} />
      )}
      <div className="flex items-start justify-between mb-4">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center"
          style={{ background: accent ? 'rgba(255,102,48,0.15)' : 'rgba(91,53,196,0.2)' }}>
          <Icon size={16} className={accent ? 'text-sds-orange' : 'text-sds-purple-glow'} />
        </div>
        <span className="text-[10px] text-sds-muted uppercase tracking-widest font-semibold">{label}</span>
      </div>
      <p className={`text-4xl font-black tracking-tight mb-1 ${accent ? 'text-gradient-orange' : 'text-white'}`}>
        {display}
      </p>
      {sub && <p className="text-sds-muted text-xs leading-relaxed">{sub}</p>}
    </div>
  )
}

/* ── Stage gate bar ───────────────────────────────────────── */
function GateBar({ label, value, index }) {
  const barColor =
    value >= 75 ? 'linear-gradient(90deg, #7B55E0, #9B75FF)' :
    value >= 40 ? 'linear-gradient(90deg, #FF8C58, #FF6630)' :
                  'linear-gradient(90deg, #FF6630, #FF3000)'

  return (
    <div className="flex items-center gap-4 py-2.5 border-b border-sds-border/20 last:border-0
                    animate-fade-in-up opacity-0-init"
      style={{ animationDelay: `${200 + index * 80}ms`, animationFillMode: 'forwards' }}>
      <span className="text-xs text-sds-muted font-mono w-44 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(46,26,106,0.5)' }}>
        <div
          className="progress-bar-fill"
          style={{ '--bar-w': `${Math.max(value, 2)}%`, background: barColor }}
        />
      </div>
      <span className="text-xs font-bold w-9 text-right shrink-0"
        style={{ color: value >= 75 ? '#9B75FF' : value >= 40 ? '#FF8C58' : '#FF6630' }}>
        {value}%
      </span>
    </div>
  )
}

/* ── Gap chip ─────────────────────────────────────────────── */
function GapChip({ gap, index }) {
  const isHigh = gap.impact === 'HIGH'
  return (
    <div className={`rounded-xl p-4 border transition-all hover:scale-[1.01] cursor-default
                     animate-fade-in-up opacity-0-init`}
      style={{
        animationDelay: `${300 + index * 70}ms`,
        animationFillMode: 'forwards',
        borderColor: isHigh ? 'rgba(255,102,48,0.35)' : 'rgba(255,140,88,0.25)',
        background: isHigh ? 'rgba(255,102,48,0.07)' : 'rgba(255,140,88,0.05)',
      }}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <p className="text-sds-white text-xs font-semibold leading-snug">{gap.gap}</p>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold shrink-0 ${
          isHigh ? 'bg-sds-orange/20 text-sds-orange' : 'bg-sds-orange-light/15 text-sds-orange-light'
        }`}>{gap.impact}</span>
      </div>
      <p className="text-sds-muted text-[11px]">{gap.stage_gate} · {gap.responsible_party}</p>
      <p className="text-sds-muted/60 text-[11px] mt-1 italic line-clamp-2">{gap.recommendation}</p>
    </div>
  )
}

/* ── Main dashboard ───────────────────────────────────────── */
export default function Dashboard() {
  const data = useAnalysis()
  if (!data) return null

  const { client_overview: co = {}, metrics = {}, gap_analysis = [], checklist = [], pipeline_metadata: pm } = data
  const sg          = metrics.stage_gate_completion || {}
  const presentCount = checklist.filter(c => c.status === 'PRESENT').length
  const partialCount = checklist.filter(c => c.status === 'PARTIAL').length
  const highGaps    = gap_analysis.filter(g => g.impact === 'HIGH')
  const medGaps     = gap_analysis.filter(g => g.impact === 'MEDIUM')
  const genTime     = new Date().toLocaleString()

  return (
    <div className="p-8 max-w-screen-xl">

      {/* ── Page header ── */}
      <div className="flex items-start justify-between mb-2 animate-fade-in">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] text-sds-orange uppercase tracking-widest font-bold">
              Smart Data Solutions · Red Duke AI Report
            </span>
          </div>
          <h1 className="text-4xl font-black text-white tracking-tight accent-line mb-4">
            Virtual Mailroom · Implementation Audit
          </h1>
          <p className="text-sds-muted-light text-sm leading-relaxed max-w-2xl">
            {co.summary}
          </p>
        </div>
      </div>

      {/* Red Duke insight banner */}
      {co.current_phase && (
        <div className="flex items-center gap-3 mb-8 px-4 py-2.5 rounded-xl border border-sds-purple/30 animate-fade-in"
          style={{ background: 'rgba(91,53,196,0.08)' }}>
          <div className="w-5 h-5 rounded duke-ring flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg,#2E1A6A,#1A0F3C)' }}>
            <span className="text-[8px] font-black text-gradient-orange">RD</span>
          </div>
          <p className="text-sds-muted-light text-xs">
            <span className="text-sds-orange font-semibold">Red Duke AI detected: </span>
            Based on evidence found across {metrics.total_documents ?? 0} documents, this project is currently at stage{' '}
            <span className="text-white font-semibold">{co.current_phase}</span>
            {' '}— documentation coverage must reach ~70% before advancing to TG1 (Implementation).
          </p>
        </div>
      )}

      {/* ── Metric cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Coverage Score"   value={`${metrics.coverage_score ?? 0}%`}
          sub={`${presentCount} present · ${partialCount} partial`}
          icon={TrendingUp}  delay={0}   accent />
        <MetricCard label="Documents"        value={metrics.total_documents ?? 0}
          sub={`${metrics.successfully_parsed ?? 0} parsed successfully`}
          icon={FileText}    delay={100} />
        <MetricCard label="Deliverables Met" value={presentCount + partialCount}
          sub={`${checklist.filter(c => c.status === 'MISSING').length} still missing`}
          icon={ShieldCheck} delay={200} />
        <MetricCard label="High-Risk Gaps"   value={metrics.high_risk_gaps ?? 0}
          sub={`${metrics.total_gaps ?? 0} total gaps identified`}
          icon={Zap}         delay={300} accent />
      </div>

      {/* ── Stage gates + top gaps ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

        {/* Stage gate progress */}
        <div className="glass glass-hover rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <CheckCircle2 size={14} className="text-sds-orange" />
            <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest">
              Stage Gate Completion
            </h2>
          </div>
          <div>
            {GATE_ORDER.map((key, i) => (
              <GateBar key={key} label={GATE_LABELS[key]} value={sg[key] ?? 0} index={i} />
            ))}
          </div>
        </div>

        {/* High-risk gaps */}
        <div className="glass glass-hover rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <AlertTriangle size={14} className="text-sds-orange" />
              <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest">
                High-Risk Gaps
              </h2>
            </div>
            <span className="text-xs font-bold text-sds-orange bg-sds-orange/10 px-2 py-0.5 rounded-full">
              {highGaps.length}
            </span>
          </div>

          {highGaps.length > 0 ? (
            <div className="space-y-2">
              {highGaps.slice(0, 4).map((g, i) => <GapChip key={i} gap={g} index={i} />)}
              {highGaps.length > 4 && (
                <p className="text-sds-muted text-[11px] text-center pt-1">
                  +{highGaps.length - 4} more · see Gap Analysis page
                </p>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-3 rounded-xl p-4 border border-sds-purple/20"
              style={{ background: 'rgba(91,53,196,0.06)' }}>
              <CheckCircle2 size={18} className="text-sds-purple-glow" />
              <div>
                <p className="text-white text-sm font-semibold">No high-risk gaps</p>
                <p className="text-sds-muted text-xs mt-0.5">Red Duke found no critical issues.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Bottom row: Risks · Decisions · Medium gaps ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">

        {/* Open risks */}
        <div className="glass glass-hover rounded-2xl p-6">
          <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest mb-4">
            Open Risks
          </h2>
          <ul className="space-y-2.5">
            {(co.open_risks || []).length > 0
              ? co.open_risks.map((r, i) => (
                <li key={i} className="flex gap-2.5 text-xs text-sds-muted-light leading-relaxed">
                  <AlertTriangle size={12} className="text-sds-orange shrink-0 mt-0.5" />
                  <span>{r}</span>
                </li>
              ))
              : <li className="text-xs text-sds-muted/40 italic">None identified</li>
            }
          </ul>
        </div>

        {/* Key decisions */}
        <div className="glass glass-hover rounded-2xl p-6">
          <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest mb-4">
            Key Decisions
          </h2>
          <ul className="space-y-2.5">
            {(co.key_decisions || []).length > 0
              ? co.key_decisions.map((d, i) => (
                <li key={i} className="flex gap-2.5 text-xs text-sds-muted-light leading-relaxed">
                  <div className="w-1.5 h-1.5 rounded-full bg-sds-purple-glow shrink-0 mt-1.5" />
                  <span>{d}</span>
                </li>
              ))
              : <li className="text-xs text-sds-muted/40 italic">None documented</li>
            }
          </ul>
        </div>

        {/* Medium gaps */}
        <div className="glass glass-hover rounded-2xl p-6">
          <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest mb-4">
            Medium-Risk Gaps <span className="text-sds-orange-light ml-1">({medGaps.length})</span>
          </h2>
          <ul className="space-y-2.5">
            {medGaps.length > 0
              ? medGaps.slice(0, 4).map((g, i) => (
                <li key={i} className="flex gap-2.5 text-xs text-sds-muted-light leading-relaxed">
                  <div className="w-1.5 h-1.5 rounded-full bg-sds-orange-light shrink-0 mt-1.5" />
                  <span>{g.gap}</span>
                </li>
              ))
              : <li className="text-xs text-sds-muted/40 italic">None identified</li>
            }
          </ul>
        </div>
      </div>

      {/* ── Integrations ── */}
      {(co.integrations || []).length > 0 && (
        <div className="glass glass-hover rounded-2xl p-6">
          <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest mb-4">
            Systems &amp; Integrations
          </h2>
          <div className="flex flex-wrap gap-2">
            {co.integrations.map((item, i) => (
              <span key={i} className="text-xs px-3 py-1.5 rounded-full font-medium transition-all hover:scale-105 cursor-default"
                style={{
                  background: 'rgba(91,53,196,0.12)',
                  border: '1px solid rgba(91,53,196,0.3)',
                  color: '#B0A4D4',
                }}>
                {item}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
