import { useState, useEffect, useRef } from 'react'

export default function useCountUp(target, duration = 1200, delay = 0) {
  const [value, setValue] = useState(0)
  const frameRef = useRef(null)

  useEffect(() => {
    const num = parseFloat(target) || 0
    if (num === 0) { setValue(0); return }

    const timeout = setTimeout(() => {
      const start = performance.now()

      const tick = (now) => {
        const elapsed = now - start
        const progress = Math.min(elapsed / duration, 1)
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3)
        setValue(Math.round(eased * num))
        if (progress < 1) {
          frameRef.current = requestAnimationFrame(tick)
        }
      }

      frameRef.current = requestAnimationFrame(tick)
    }, delay)

    return () => {
      clearTimeout(timeout)
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
    }
  }, [target, duration, delay])

  return value
}
