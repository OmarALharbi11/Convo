interface ConvoLogoProps {
  size?: number
  className?: string
}

export const ConvoLogo = ({ size = 36, className = '' }: ConvoLogoProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    {/* Background circle */}
    <circle cx="18" cy="18" r="18" fill="#2563eb" />

    {/* Speech bubble body */}
    <path
      d="M7 9C7 7.34315 8.34315 6 10 6H26C27.6569 6 29 7.34315 29 9V19C29 20.6569 27.6569 22 26 22H20.5L18 25L15.5 22H10C8.34315 22 7 20.6569 7 19V9Z"
      fill="white"
    />

    {/* Sound wave bars inside bubble */}
    <rect x="11.5" y="13" width="2" height="7" rx="1" fill="#2563eb" />
    <rect x="15" y="11" width="2" height="11" rx="1" fill="#2563eb" />
    <rect x="18.5" y="13" width="2" height="7" rx="1" fill="#2563eb" />
    <rect x="22" y="14.5" width="2" height="4" rx="1" fill="#2563eb" />
  </svg>
)
