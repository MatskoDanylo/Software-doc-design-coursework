import { Link } from 'react-router-dom'

export default function Logo() {
  return (
    <Link
      to="/"
      aria-label="Cinema Platform — на головну"
      className="flex shrink-0 items-center gap-2 rounded-lg font-display text-lg font-semibold tracking-wide"
    >
      <img src="/favicon.svg" alt="" className="size-8" />
      <span className="hidden sm:inline">
        Cinema<span className="text-gold">Platform</span>
      </span>
    </Link>
  )
}
