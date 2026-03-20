import { useState, useEffect, createContext, useContext } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import AnimatedBackground from './components/AnimatedBackground'
import Sidebar from './components/Sidebar'
import SdsLogo from './components/SdsLogo'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import Checklist from './pages/Checklist'
import GapAnalysis from './pages/GapAnalysis'
import WorkflowNarrative from './pages/WorkflowNarrative'

export const AnalysisContext = createContext(null)
export function useAnalysis() { return useContext(AnalysisContext) }

/* ── Red Duke loading screen ─────────────────────────────── */
function LoadingScreen() {
  const [dots, setDots] = useState('.')
  const [step, setStep] = useState(0)
  const steps = [
    'Initialising Red Duke intelligence core...',
    'Parsing healthcare document corpus...',
    'Mapping evidence to SDS stage-gate standards...',
    'Generating AI-driven insights...',
    'Smart Data Solutions · Ready.',
  ]

  useEffect(() => {
    const d = setInterval(() => setDots(p => p.length >= 3 ? '.' : p + '.'), 400)
    const s = setInterval(() => setStep(p => Math.min(p + 1, steps.length - 1)), 600)
    return () => { clearInterval(d); clearInterval(s) }
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden" style={{ background: '#07021A' }}>
      <AnimatedBackground />
      <div className="relative z-10 text-center animate-fade-in">
        {/* Spinning ring loader */}
        <div className="relative mx-auto mb-8 w-24 h-24">
          <div className="absolute -inset-2 rounded-2xl border border-sds-orange/30 animate-spin-slow" />
        </div>

        <h1 className="text-3xl font-black text-white mb-1 tracking-tight">
          SMART <span className="text-gradient-orange">DATA</span>
        </h1>
        <p className="text-sds-muted text-sm mb-10 tracking-widest uppercase">Solutions · Red Duke AI</p>

        {/* Progress bar */}
        <div className="w-72 mx-auto mb-6">
          <div className="h-0.5 bg-sds-border rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${((step + 1) / steps.length) * 100}%`,
                background: 'linear-gradient(90deg, #5B35C4, #FF6630)',
              }}
            />
          </div>
        </div>

        <p className="text-sds-muted-light text-xs font-mono h-5">
          {steps[step]}{step < steps.length - 1 ? dots : ''}
        </p>

        <p className="text-sds-muted/40 text-xs mt-8">
          Smart Data Solutions · Documentation Intelligence
        </p>
      </div>
    </div>
  )
}

/* ── Error screen ────────────────────────────────────────── */
function ErrorScreen({ message }) {
  return (
    <div className="min-h-screen flex items-center justify-center relative" style={{ background: '#07021A' }}>
      <AnimatedBackground />
      <div className="relative z-10 max-w-md w-full mx-4 animate-fade-in">
        <div className="glass rounded-2xl p-10 text-center">
          {/* Logo */}

          <h2 className="text-white font-bold text-xl mb-2">No Analysis Found</h2>
          <p className="text-sds-muted text-sm mb-2">{message}</p>
          <p className="text-sds-orange/80 text-xs mb-8">
            Red Duke AI needs document data to get started.
          </p>

          <div className="bg-sds-darker rounded-xl p-5 text-left border border-sds-border">
            <p className="text-sds-muted-light text-xs uppercase tracking-wider mb-3 font-semibold">
              Run the pipeline
            </p>
            <div className="font-mono text-sm space-y-1">
              <p className="text-sds-purple-glow">$ cd red_duke_demo</p>
              <p className="text-sds-orange-light">$ PYTHONUTF8=1 python main.py</p>
            </div>
          </div>

          <p className="text-sds-muted/40 text-xs mt-6">Then refresh this page.</p>
        </div>
      </div>
    </div>
  )
}

/* ── Page wrapper with transition ────────────────────────── */
function PageWrapper({ children }) {
  const location = useLocation()
  return (
    <div key={location.pathname} className="page-enter min-h-full">
      {children}
    </div>
  )
}

/* ── App ─────────────────────────────────────────────────── */
export default function App() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    fetch('/analysis_output.json')
      .then(r => {
        if (!r.ok) throw new Error('analysis_output.json not found in frontend/public/')
        return r.json()
      })
      .then(json => { setData(json); setLoading(false) })
      .catch(e  => { setError(e.message); setLoading(false) })
  }, [])

  if (loading) return <LoadingScreen />
  if (error)   return <ErrorScreen message={error} />

  return (
    <AnalysisContext.Provider value={data}>
      <div className="flex min-h-screen" style={{ background: '#07021A' }}>
        <AnimatedBackground />
        <Sidebar />
        <main className="flex-1 overflow-auto relative z-10">
          <PageWrapper>
            <Routes>
              <Route path="/"          element={<Dashboard />} />
              <Route path="/documents" element={<Documents />} />
              <Route path="/checklist" element={<Checklist />} />
              <Route path="/gaps"      element={<GapAnalysis />} />
              <Route path="/workflow"  element={<WorkflowNarrative />} />
            </Routes>
          </PageWrapper>
        </main>
      </div>
    </AnalysisContext.Provider>
  )
}
