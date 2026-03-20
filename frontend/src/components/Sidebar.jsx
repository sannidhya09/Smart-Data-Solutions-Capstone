import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, FolderOpen, ClipboardCheck,
  Zap, GitMerge, ChevronRight,
} from 'lucide-react'
import { useAnalysis } from '../App'
import SdsLogo from './SdsLogo'

const nav = [
  { path: '/',          label: 'Dashboard',          icon: LayoutDashboard, desc: 'Overview & metrics' },
  { path: '/documents', label: 'Documents',           icon: FolderOpen,      desc: 'Parsed file analysis' },
  { path: '/checklist', label: 'Checklist',           icon: ClipboardCheck,  desc: 'Evidence mapping' },
  { path: '/gaps',      label: 'Gap Analysis',        icon: Zap,             desc: 'Missing deliverables' },
  { path: '/workflow',  label: 'Workflow Narrative',  icon: GitMerge,        desc: 'Process intelligence' },
]

function CoverageRing({ value }) {
  const r = 18
  const circ = 2 * Math.PI * r
  const offset = circ - (value / 100) * circ
  const color = value >= 70 ? '#9B75FF' : value >= 40 ? '#FF8C58' : '#FF6630'

  return (
    <div className="relative w-14 h-14 flex items-center justify-center">
      <svg width="56" height="56" className="-rotate-90">
        <circle cx="28" cy="28" r={r} fill="none" stroke="rgba(46,26,106,0.5)" strokeWidth="3" />
        <circle
          cx="28" cy="28" r={r} fill="none"
          stroke={color} strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)' }}
        />
      </svg>
      <span className="absolute text-xs font-bold" style={{ color }}>{value}%</span>
    </div>
  )
}

export default function Sidebar() {
  const data = useAnalysis()
  const metrics   = data?.metrics    || {}
  const overview  = data?.client_overview || {}
  const coverage  = metrics.coverage_score ?? 0
  const highGaps  = metrics.high_risk_gaps ?? 0
  const totalDocs = metrics.total_documents ?? 0

  return (
    <aside className="w-64 sidebar-bg flex flex-col shrink-0 relative z-20">

      {/* ── Brand / SDS logo ── */}
      <div className="px-5 pt-7 pb-5 border-b border-sds-border/50">
        <div className="flex items-center gap-3 mb-1">
          <div>
            <h1 className="text-base font-black text-white tracking-wide leading-none">
              SMART <span className="text-gradient-orange">DATA</span>
            </h1>
            <p className="text-sds-muted text-[10px] tracking-widest uppercase leading-none mt-0.5">
              Solutions · Red Duke AI
            </p>
          </div>
        </div>
      </div>

      {/* ── Client context ── */}
      {overview.client_name && (
        <div className="px-5 py-4 border-b border-sds-border/40"
          style={{ background: 'rgba(255,102,48,0.04)' }}>
          <p className="text-[10px] text-sds-muted uppercase tracking-widest mb-1 font-semibold">
            Active Client
          </p>
          <p className="text-sds-white font-semibold text-sm truncate leading-snug">
            {overview.client_name}
          </p>
          <p className="text-sds-muted text-[11px] truncate mt-0.5">
            {overview.current_phase}
          </p>
        </div>
      )}

      {/* ── Navigation ── */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {nav.map(({ path, label, icon: Icon, desc }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) => [
              'group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
              isActive
                ? 'nav-active'
                : 'text-sds-muted hover:text-sds-white hover:bg-sds-card/60 border-l-3 border-l-transparent',
            ].join(' ')}
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={15}
                  className={`shrink-0 transition-colors ${isActive ? 'text-sds-orange' : 'text-sds-muted group-hover:text-sds-purple-glow'}`}
                />
                <span className="flex-1 leading-none">{label}</span>
                {isActive && (
                  <ChevronRight size={12} className="text-sds-orange/60" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* ── Intelligence stats ── */}
      {coverage > 0 && (
        <div className="px-4 py-4 border-t border-sds-border/40 mx-2 mb-2 rounded-xl"
          style={{ background: 'rgba(26,15,60,0.6)' }}>
          <p className="text-[10px] text-sds-muted uppercase tracking-widest mb-3 font-semibold">
            Red Duke AI Assessment
          </p>

          <div className="flex items-center gap-3 mb-3">
            <CoverageRing value={coverage} />
            <div>
              <p className="text-sds-white text-xs font-semibold">Coverage</p>
              <p className="text-sds-muted text-[10px]">{totalDocs} docs analyzed</p>
            </div>
          </div>

          {highGaps > 0 && (
            <div className="flex items-center justify-between bg-sds-orange/8 border border-sds-orange/20 rounded-lg px-3 py-2">
              <div className="flex items-center gap-2">
                <Zap size={11} className="text-sds-orange" />
                <span className="text-[11px] text-sds-muted-light">High-risk gaps</span>
              </div>
              <span className="text-xs font-bold text-sds-orange">{highGaps}</span>
            </div>
          )}
        </div>
      )}

      {/* ── Footer ── */}
      <div className="px-5 py-3 border-t border-sds-border/30">
        <p className="text-[10px] text-sds-muted/30 text-center">
          Smart Data Solutions · 26 Years of Healthcare AI
        </p>
      </div>
    </aside>
  )
}
