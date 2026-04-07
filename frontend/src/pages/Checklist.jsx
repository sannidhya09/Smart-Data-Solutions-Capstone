import React, { useState } from 'react'
import { ClipboardCheck, Search, CheckCircle2, Clock, XCircle, ChevronDown, ChevronRight, Download, FileText, Quote } from 'lucide-react'
import { useAnalysis } from '../App'

const STATUS_CFG = {
  PRESENT: {
    bar:   'border-l-2 border-l-sds-purple-glow',
    badge: 'badge-present',
    dot:   'bg-sds-purple-glow',
    icon:  CheckCircle2,
    iconCls: 'text-sds-purple-glow',
  },
  PARTIAL: {
    bar:   'border-l-2 border-l-sds-orange-light',
    badge: 'badge-partial',
    dot:   'bg-sds-orange-light',
    icon:  Clock,
    iconCls: 'text-sds-orange-light',
  },
  MISSING: {
    bar:   'border-l-2 border-l-sds-orange',
    badge: 'badge-missing',
    dot:   'bg-sds-orange',
    icon:  XCircle,
    iconCls: 'text-sds-orange',
  },
}

const CONFIDENCE_CFG = {
  HIGH:   'text-sds-purple-glow',
  MEDIUM: 'text-sds-orange-light',
  LOW:    'text-sds-orange',
}

const STAGE_GATES = [
  'ALL',
  'TG-1 (Initiation)',
  'TG0 (Design)',
  'TG1 (Implementation)',
  'TG2 (Test)',
  'TG3 (Deploy/Warranty)',
]

const STATUSES = ['ALL', 'PRESENT', 'PARTIAL', 'MISSING']

export default function Checklist() {
  const data = useAnalysis()
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [stageFilter,  setStageFilter]  = useState('ALL')
  const [search,       setSearch]       = useState('')
  const [expandedRow,  setExpandedRow]  = useState(null)

  if (!data) return null

  const checklist = data.checklist || []

  const filtered = checklist.filter(item => {
    const matchStatus = statusFilter === 'ALL' || item.status === statusFilter
    const matchStage  = stageFilter  === 'ALL' || item.stage_gate === stageFilter
    const matchSearch = !search ||
      item.deliverable?.toLowerCase().includes(search.toLowerCase()) ||
      item.notes?.toLowerCase().includes(search.toLowerCase())
    return matchStatus && matchStage && matchSearch
  })

  const counts = {
    PRESENT: checklist.filter(c => c.status === 'PRESENT').length,
    PARTIAL: checklist.filter(c => c.status === 'PARTIAL').length,
    MISSING: checklist.filter(c => c.status === 'MISSING').length,
  }

  return (
    <div className="p-8 max-w-screen-xl">

      {/* Header */}
      <div className="flex items-start justify-between mb-8 animate-fade-in">
        <div>
          <p className="text-[10px] text-sds-orange uppercase tracking-widest font-bold mb-1">
            Red Duke · Evidence Mapping
          </p>
          <h1 className="text-3xl font-black text-white accent-line mb-4">Checklist</h1>
          <p className="text-sds-muted text-sm">{checklist.length} SDS stage-gate deliverables audited</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-sds-muted pointer-events-none" />
            <input
              type="text" placeholder="Search deliverables..."
              value={search} onChange={e => setSearch(e.target.value)}
              className="bg-sds-card border border-sds-border text-sds-white text-xs pl-8 pr-4 py-2.5 rounded-xl
                         focus:outline-none focus:border-sds-orange/50 placeholder:text-sds-muted/40 w-60"
            />
          </div>
          {/* Download */}
          <a href="/Red_Duke_Report.xlsx" download
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all hover:scale-105"
            style={{ background: 'rgba(255,102,48,0.15)', border: '1px solid rgba(255,102,48,0.4)', color: '#FF6630' }}>
            <Download size={13} /> Excel
          </a>
        </div>
      </div>

      {/* Summary pills */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Present',  count: counts.PRESENT, status: 'PRESENT' },
          { label: 'Partial',  count: counts.PARTIAL, status: 'PARTIAL' },
          { label: 'Missing',  count: counts.MISSING, status: 'MISSING' },
        ].map(({ label, count, status }, i) => {
          const cfg = STATUS_CFG[status]
          const Icon = cfg.icon
          return (
            <button
              key={label}
              onClick={() => setStatusFilter(statusFilter === status ? 'ALL' : status)}
              className={`glass glass-hover rounded-2xl p-5 text-left transition-all animate-fade-in-up opacity-0-init
                          ${statusFilter === status ? 'ring-1 ring-sds-orange/40' : ''}`}
              style={{ animationDelay: `${i * 80}ms`, animationFillMode: 'forwards' }}
            >
              <div className="flex items-center justify-between mb-2">
                <Icon size={14} className={cfg.iconCls} />
                <span className={`text-[10px] font-bold uppercase tracking-widest ${cfg.iconCls}`}>{label}</span>
              </div>
              <p className="text-3xl font-black text-white">{count}</p>
              <p className="text-sds-muted text-[10px] mt-1">
                {((count / (checklist.length || 1)) * 100).toFixed(0)}% of total
              </p>
            </button>
          )
        })}
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6 flex-wrap items-center animate-fade-in">
        {/* Status filter buttons */}
        <div className="flex gap-1.5">
          {STATUSES.map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${
                statusFilter === s
                  ? 'bg-sds-orange text-white'
                  : 'bg-sds-card border border-sds-border text-sds-muted hover:text-sds-white hover:border-sds-orange/40'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Stage gate dropdown */}
        <div className="relative">
          <select
            value={stageFilter}
            onChange={e => setStageFilter(e.target.value)}
            className="appearance-none bg-sds-card border border-sds-border text-sds-muted text-xs
                       px-3 pr-8 py-1.5 rounded-lg focus:outline-none focus:border-sds-orange/50
                       cursor-pointer hover:border-sds-border-bright transition-colors"
          >
            {STAGE_GATES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <ChevronDown size={11} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-sds-muted pointer-events-none" />
        </div>

        <span className="text-xs text-sds-muted/50 ml-auto font-mono">
          {filtered.length} / {checklist.length} items
        </span>
      </div>

      {/* Table */}
      <div className="glass rounded-2xl overflow-hidden animate-fade-in">
        <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[900px]">
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(46,26,106,0.5)', background: 'rgba(13,5,32,0.6)' }}>
              {['Deliverable', 'Stage Gate', 'Owner', 'Status', 'Confidence', 'Priority', 'Effort', 'Evidence Files', 'Notes'].map(h => (
                <th key={h} className="text-left px-5 py-3.5 text-[10px] font-bold text-sds-muted uppercase tracking-widest whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((item, i) => {
              const cfg = STATUS_CFG[item.status] || STATUS_CFG.MISSING
              const Icon = cfg.icon
              const isExpanded = expandedRow === i
              const hasEvidence = item.evidence_trail?.length > 0
              return (
                <React.Fragment key={i}>
                  <tr
                    className={`${cfg.bar} transition-colors animate-fade-in-up opacity-0-init ${hasEvidence ? 'cursor-pointer' : ''}`}
                    style={{
                      borderBottom: isExpanded ? 'none' : '1px solid rgba(46,26,106,0.2)',
                      animationDelay: `${i * 30}ms`,
                      animationFillMode: 'forwards',
                    }}
                    onClick={() => hasEvidence && setExpandedRow(isExpanded ? null : i)}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(46,26,106,0.15)'}
                    onMouseLeave={e => e.currentTarget.style.background = ''}
                  >
                    <td className="px-5 py-4 text-sds-white font-semibold text-xs max-w-[220px] leading-snug">
                      <div className="flex items-center gap-2">
                        {hasEvidence && (
                          <ChevronRight size={11}
                            className={`text-sds-muted/40 shrink-0 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                        )}
                        <span>{item.deliverable}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap">
                      <span className="text-[10px] font-mono text-sds-muted px-2 py-0.5 rounded"
                        style={{ background: 'rgba(46,26,106,0.4)', border: '1px solid rgba(46,26,106,0.6)' }}>
                        {item.stage_gate}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-sds-muted text-xs whitespace-nowrap">
                      {item.responsibility || '—'}
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-full font-bold ${cfg.badge}`}>
                        <Icon size={9} />
                        {item.status}
                      </span>
                    </td>
                    <td className={`px-5 py-4 text-xs font-bold ${CONFIDENCE_CFG[item.confidence] || 'text-sds-muted/40'}`}>
                      {item.confidence || '—'}
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap">
                      {item.priority && (
                        <span className={`text-[10px] font-black px-1.5 py-0.5 rounded ${
                          item.priority === 'P1' ? 'bg-sds-orange/20 text-sds-orange' :
                          item.priority === 'P2' ? 'bg-sds-orange-light/15 text-sds-orange-light' :
                          'bg-sds-purple/20 text-sds-purple-glow'
                        }`}>{item.priority}</span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-xs text-sds-muted whitespace-nowrap">
                      {item.estimated_effort || '—'}
                    </td>
                    <td className="px-5 py-4 text-xs max-w-[180px]">
                      {item.evidence_files?.length > 0
                        ? item.evidence_files.map((f, fi) => (
                          <div key={fi} className="text-sds-purple-glow truncate leading-snug">{f}</div>
                        ))
                        : <span className="text-sds-muted/30">—</span>
                      }
                    </td>
                    <td className="px-5 py-4 text-xs text-sds-muted/70 leading-relaxed min-w-[280px]">
                      {item.notes || '—'}
                    </td>
                  </tr>

                  {/* Evidence trail expansion */}
                  {isExpanded && hasEvidence && (
                    <tr style={{ borderBottom: '1px solid rgba(46,26,106,0.2)' }}>
                      <td colSpan={9} className="px-0 py-0">
                        <div className="animate-fade-in mx-5 mb-4 mt-1 rounded-xl overflow-hidden"
                          style={{ background: 'rgba(13,5,32,0.5)', border: '1px solid rgba(46,26,106,0.3)' }}>
                          <div className="px-5 py-3 flex items-center gap-2"
                            style={{ borderBottom: '1px solid rgba(46,26,106,0.25)', background: 'rgba(91,53,196,0.06)' }}>
                            <Quote size={11} className="text-sds-purple-glow" />
                            <span className="text-[10px] font-bold text-sds-purple-glow uppercase tracking-widest">
                              Evidence Trail — {item.evidence_trail.length} source(s)
                            </span>
                          </div>
                          <div className="divide-y divide-sds-border/15">
                            {item.evidence_trail.map((ev, ei) => (
                              <div key={ei} className="px-5 py-4">
                                <div className="flex items-center gap-2 mb-2">
                                  <FileText size={11} className="text-sds-purple-glow shrink-0" />
                                  <span className="text-[11px] text-sds-white font-semibold">{ev.source_file}</span>
                                  {ev.section_or_location && (
                                    <span className="text-[10px] font-mono text-sds-muted px-2 py-0.5 rounded"
                                      style={{ background: 'rgba(46,26,106,0.4)', border: '1px solid rgba(46,26,106,0.6)' }}>
                                      {ev.section_or_location}
                                    </span>
                                  )}
                                </div>
                                {ev.excerpt && (
                                  <div className="rounded-lg p-3 mb-2"
                                    style={{ background: 'rgba(91,53,196,0.06)', borderLeft: '2px solid rgba(155,117,255,0.4)' }}>
                                    <p className="text-[11px] text-sds-muted-light leading-relaxed italic">
                                      "{ev.excerpt}"
                                    </p>
                                  </div>
                                )}
                                {ev.assessment && (
                                  <p className="text-[11px] text-sds-muted leading-relaxed">
                                    {ev.assessment}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )
            })}
          </tbody>
        </table>

        {filtered.length === 0 && (
          <div className="text-center py-16">
            <ClipboardCheck size={24} className="text-sds-muted/30 mx-auto mb-3" />
            <p className="text-sds-muted text-sm">No items match the selected filters.</p>
          </div>
        )}
        </div>
      </div>
    </div>
  )
}
