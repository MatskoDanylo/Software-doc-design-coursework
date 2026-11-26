export default function TestPaymentBanner() {
  return (
    <div role="note" className="rounded-lg border border-amber-400/50 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
      <p className="font-semibold tracking-wide uppercase">Тестова оплата</p>
      <p className="mt-1">Це імітація платіжного шлюзу: гроші не списуються, а відповідь банку ви обираєте самі.</p>
    </div>
  )
}
