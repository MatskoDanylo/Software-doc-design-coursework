import { Link } from 'react-router-dom'

export default function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-display text-lg font-semibold tracking-wide">
      <img src="/favicon.svg" alt="" className="size-8" />
      <span>
        Cinema<span className="text-gold">Platform</span>
      </span>
    </Link>
  )
}
