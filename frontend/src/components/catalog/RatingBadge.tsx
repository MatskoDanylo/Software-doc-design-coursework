export default function RatingBadge({ rating, className = '' }: { rating: number; className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md bg-screen/85 px-2 py-0.5 text-xs font-semibold text-gold ${className}`}
      aria-label={`Рейтинг ${rating.toFixed(1)}`}
    >
      <span aria-hidden="true">★</span>
      {rating.toFixed(1)}
    </span>
  )
}
