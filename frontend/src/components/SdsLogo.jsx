/* SDS Logo — geometric S-mark matching Smart Data Solutions brand */
export default function SdsLogo({ size = 36, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Corner brackets */}
      <rect x="2" y="2" width="12" height="3" fill="#FF6630" rx="1" />
      <rect x="2" y="2" width="3" height="12" fill="#FF6630" rx="1" />
      <rect x="86" y="2" width="12" height="3" fill="#FF6630" rx="1" />
      <rect x="95" y="2" width="3" height="12" fill="#FF6630" rx="1" />
      <rect x="2" y="95" width="12" height="3" fill="#FF6630" rx="1" />
      <rect x="2" y="86" width="3" height="12" fill="#FF6630" rx="1" />
      <rect x="86" y="95" width="12" height="3" fill="#FF6630" rx="1" />
      <rect x="95" y="86" width="3" height="12" fill="#FF6630" rx="1" />

      {/* S-mark — top bar */}
      <rect x="28" y="22" width="44" height="12" fill="white" rx="6" />
      {/* S-mark — top-left vertical */}
      <rect x="22" y="22" width="12" height="28" fill="white" rx="6" />
      {/* S-mark — middle bar */}
      <rect x="28" y="44" width="44" height="12" fill="white" rx="6" />
      {/* S-mark — bottom-right vertical */}
      <rect x="66" y="50" width="12" height="28" fill="white" rx="6" />
      {/* S-mark — bottom bar */}
      <rect x="28" y="66" width="44" height="12" fill="white" rx="6" />
    </svg>
  )
}
