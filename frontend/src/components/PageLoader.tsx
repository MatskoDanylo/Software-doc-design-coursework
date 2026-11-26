export default function PageLoader() {
  return (
    <div role="status" className="flex justify-center py-20">
      <span className="size-8 animate-spin rounded-full border-2 border-line border-t-gold" />
      <span className="sr-only">Завантаження…</span>
    </div>
  )
}
