import { useState } from 'react'
import { FileText, FileSpreadsheet, Presentation, GitBranch, Search, ChevronDown, ChevronUp, CheckCircle2, XCircle } from 'lucide-react'
import { useAnalysis } from '../App'

const TYPE_CFG = {
  'Word Document (.docx)':           { icon: FileText,       color: 'rgba(91,53,196,0.15)',  border: 'rgba(91,53,196,0.3)',   text: '#9B75FF', label: 'DOCX' },
  'Excel Workbook (.xlsx)':          { icon: FileSpreadsheet, color: 'rgba(255,140,88,0.1)', border: 'rgba(255,140,88,0.3)', text: '#FF8C58', label: 'XLSX' },
  'PowerPoint Presentation (.pptx)': { icon: Presentation,   color: 'rgba(255,102,48,0.1)',  border: 'rgba(255,102,48,0.3)',  text: '#FF6630', label: 'PPTX' },
  'Visio Diagram (.vsdx)':           { icon: GitBranch,      color: 'rgba(155,117,255,0.1)', border: 'rgba(155,117,255,0.3)', text: '#C4A8FF', label: 'VSDX' },
}

function DocCard({ doc, index }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = TYPE_CFG[doc.file_type] || { icon: FileText, color: 'rgba(46,26,106,0.3)', border: 'rgba(78,45,158,0.3)', text: '#8B7DB8', label: 'FILE' }
  const Icon = cfg.icon

  return (
    <div className="glass glass-hover rounded-2xl overflow-hidden animate-fade-in-up opacity-0-init"
      style={{ animationDelay: `${index * 80}ms`, animationFillMode: 'forwards' }}>

      {/* Header */}
      <div className="p-6">
        <div className="flex items-start gap-4 mb-4">
          {/* File type icon */}
          <div className="w-10 h-10 rounded-xl shrink-0 flex items-center justify-center"
            style={{ background: cfg.color, border: `1px solid ${cfg.border}` }}>
            <Icon size={16} style={{ color: cfg.text }} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-white font-semibold text-sm leading-snug truncate">{doc.filename}</h3>
              <span className="text-[10px] px-2 py-0.5 rounded font-bold shrink-0"
                style={{ background: cfg.color, border: `1px solid ${cfg.border}`, color: cfg.text }}>
                {cfg.label}
              </span>
            </div>
            <p className="text-sds-muted text-xs mt-1 leading-snug">{doc.purpose}</p>
          </div>
        </div>

        <p className="text-sds-muted-light text-sm leading-relaxed mb-4">{doc.summary}</p>

        {/* Topics */}
        {(doc.key_topics || []).length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {doc.key_topics.map((t, i) => (
              <span key={i} className="text-[11px] px-2 py-0.5 rounded text-sds-muted"
                style={{ background: 'rgba(26,15,60,0.8)', border: '1px solid rgba(46,26,106,0.4)' }}>
                {t}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Toggle */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-6 py-3 text-xs font-medium text-sds-muted hover:text-sds-orange transition-colors"
        style={{ borderTop: '1px solid rgba(46,26,106,0.4)', background: 'rgba(13,5,32,0.3)' }}>
        <span className="uppercase tracking-wider">{expanded ? 'Hide Evidence' : 'Show Evidence Details'}</span>
        {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
      </button>

      {/* Evidence detail */}
      {expanded && (
        <div className="px-6 pb-6 pt-5 grid grid-cols-2 gap-6"
          style={{ borderTop: '1px solid rgba(46,26,106,0.3)', background: 'rgba(7,2,26,0.3)' }}>

          <div>
            <div className="flex items-center gap-1.5 mb-3">
              <CheckCircle2 size={11} className="text-sds-purple-glow" />
              <p className="text-[10px] font-bold text-sds-muted uppercase tracking-widest">Evidence Present</p>
            </div>
            {(doc.artifacts_present || []).length > 0
              ? (doc.artifacts_present.map((a, i) => (
                <div key={i} className="flex gap-2 text-xs text-sds-muted-light leading-snug mb-2">
                  <div className="w-1 h-1 rounded-full bg-sds-purple-glow shrink-0 mt-1.5" />
                  <span>{a}</span>
                </div>
              )))
              : <p className="text-xs text-sds-muted/40 italic">None identified</p>
            }
          </div>

          <div>
            <div className="flex items-center gap-1.5 mb-3">
              <XCircle size={11} className="text-sds-orange" />
              <p className="text-[10px] font-bold text-sds-muted uppercase tracking-widest">Missing / Incomplete</p>
            </div>
            {(doc.artifacts_missing_or_incomplete || []).length > 0
              ? (doc.artifacts_missing_or_incomplete.map((a, i) => (
                <div key={i} className="flex gap-2 text-xs text-sds-orange-light leading-snug mb-2">
                  <div className="w-1 h-1 rounded-full bg-sds-orange shrink-0 mt-1.5" />
                  <span>{a}</span>
                </div>
              )))
              : <p className="text-xs text-sds-purple-glow italic">No gaps in this document ✓</p>
            }
          </div>
        </div>
      )}
    </div>
  )
}

export default function Documents() {
  const data = useAnalysis()
  const [search, setSearch] = useState('')
  if (!data) return null

  const docs = (data.documents || []).filter(d =>
    !search ||
    d.filename?.toLowerCase().includes(search.toLowerCase()) ||
    d.summary?.toLowerCase().includes(search.toLowerCase()) ||
    (d.key_topics || []).some(t => t.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div className="p-8 max-w-screen-xl">
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <p className="text-[10px] text-sds-orange uppercase tracking-widest font-bold mb-1">
            Red Duke · Document Intelligence
          </p>
          <h1 className="text-3xl font-black text-white accent-line mb-4">Documents</h1>
          <p className="text-sds-muted text-sm">{data.documents?.length || 0} files deeply analyzed</p>
        </div>
        <div className="relative">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-sds-muted pointer-events-none" />
          <input
            type="text" placeholder="Search documents..."
            value={search} onChange={e => setSearch(e.target.value)}
            className="bg-sds-card border border-sds-border text-sds-white text-xs pl-8 pr-4 py-2.5 rounded-xl
                       focus:outline-none focus:border-sds-orange/50 placeholder:text-sds-muted/40 w-60"
          />
        </div>
      </div>

      <div className="grid gap-4">
        {docs.map((doc, i) => <DocCard key={i} doc={doc} index={i} />)}
        {docs.length === 0 && (
          <div className="glass rounded-2xl p-16 text-center">
            <p className="text-sds-muted text-sm">No documents match your search.</p>
          </div>
        )}
      </div>
    </div>
  )
}
