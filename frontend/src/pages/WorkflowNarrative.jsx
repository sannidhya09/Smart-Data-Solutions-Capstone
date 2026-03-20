import { GitMerge, AlertTriangle, Layers, Target, ChevronRight } from 'lucide-react'
import { useAnalysis } from '../App'

export default function WorkflowNarrative() {
  const data = useAnalysis()
  if (!data) return null

  const { workflow_narrative, client_overview: co = {} } = data
  const paragraphs = (workflow_narrative || '').split('\n\n').filter(p => p.trim())

  return (
    <div className="p-8 max-w-screen-xl">

      {/* Header */}
      <div className="mb-8 animate-fade-in">
        <p className="text-[10px] text-sds-orange uppercase tracking-widest font-bold mb-1">
          Red Duke · Process Intelligence
        </p>
        <h1 className="text-3xl font-black text-white accent-line mb-4">Workflow Narrative</h1>
        <p className="text-sds-muted text-sm">
          AI-generated description of the end-to-end client process
        </p>
      </div>

      {/* Scope banner */}
      {co.scope && (
        <div className="flex items-start gap-4 mb-8 px-5 py-4 rounded-2xl border animate-fade-in"
          style={{ borderColor: 'rgba(91,53,196,0.3)', background: 'rgba(91,53,196,0.07)' }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: 'rgba(91,53,196,0.2)' }}>
            <Target size={14} className="text-sds-purple-glow" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-sds-purple-glow uppercase tracking-widest mb-1">Project Scope</p>
            <p className="text-sds-muted-light text-sm leading-relaxed">{co.scope}</p>
          </div>
        </div>
      )}

      {/* Systems & integrations */}
      {(co.integrations || []).length > 0 && (
        <div className="glass glass-hover rounded-2xl p-6 mb-6 animate-fade-in-up opacity-0-init"
          style={{ animationDelay: '80ms', animationFillMode: 'forwards' }}>
          <div className="flex items-center gap-2 mb-4">
            <Layers size={13} className="text-sds-orange" />
            <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest">
              Systems &amp; Integrations
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {co.integrations.map((item, i) => (
              <span key={i}
                className="text-xs px-3 py-1.5 rounded-full font-medium transition-all hover:scale-105 cursor-default"
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

      {/* Narrative body */}
      <div className="glass glass-hover rounded-2xl p-8 mb-6 animate-fade-in-up opacity-0-init"
        style={{ animationDelay: '160ms', animationFillMode: 'forwards' }}>
        <div className="flex items-center gap-2 mb-6">
          <GitMerge size={13} className="text-sds-orange" />
          <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest">
            End-to-End Process Description
          </h2>
        </div>

        {paragraphs.length > 0 ? (
          <div className="space-y-5 max-w-3xl">
            {paragraphs.map((para, i) => (
              <div key={i}
                className="flex gap-4 animate-fade-in-up opacity-0-init"
                style={{ animationDelay: `${200 + i * 50}ms`, animationFillMode: 'forwards' }}>
                <div className="shrink-0 flex flex-col items-center gap-1 pt-0.5">
                  <span className="text-[10px] font-black text-sds-orange w-5 h-5 rounded flex items-center justify-center"
                    style={{ background: 'rgba(255,102,48,0.12)', border: '1px solid rgba(255,102,48,0.25)' }}>
                    {i + 1}
                  </span>
                  {i < paragraphs.length - 1 && (
                    <div className="w-px flex-1 min-h-4" style={{ background: 'rgba(255,102,48,0.15)' }} />
                  )}
                </div>
                <p className="text-sds-muted-light text-sm leading-relaxed pb-3">{para}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sds-muted/40 italic text-sm">No workflow narrative was generated.</p>
        )}
      </div>

      {/* Key decisions + Open risks side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Key decisions */}
        {(co.key_decisions || []).length > 0 && (
          <div className="glass glass-hover rounded-2xl p-6 animate-fade-in-up opacity-0-init"
            style={{ animationDelay: '240ms', animationFillMode: 'forwards' }}>
            <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest mb-4">
              Key Decisions &amp; Configurations
            </h2>
            <div className="space-y-2.5">
              {co.key_decisions.map((d, i) => (
                <div key={i} className="flex gap-3 rounded-xl p-3.5"
                  style={{ background: 'rgba(91,53,196,0.08)', border: '1px solid rgba(91,53,196,0.2)' }}>
                  <ChevronRight size={12} className="text-sds-purple-glow shrink-0 mt-0.5" />
                  <p className="text-sds-muted-light text-xs leading-snug">{d}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Open risks */}
        {(co.open_risks || []).length > 0 && (
          <div className="glass glass-hover rounded-2xl p-6 animate-fade-in-up opacity-0-init"
            style={{ animationDelay: '320ms', animationFillMode: 'forwards', borderColor: 'rgba(255,102,48,0.2)' }}>
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle size={13} className="text-sds-orange" />
              <h2 className="text-xs font-bold text-sds-muted-light uppercase tracking-widest">Open Risks</h2>
            </div>
            <div className="space-y-2.5">
              {co.open_risks.map((r, i) => (
                <div key={i} className="flex gap-3 rounded-xl p-3.5"
                  style={{ background: 'rgba(255,102,48,0.06)', border: '1px solid rgba(255,102,48,0.18)' }}>
                  <AlertTriangle size={11} className="text-sds-orange shrink-0 mt-0.5" />
                  <p className="text-sds-muted-light text-xs leading-snug">{r}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
