export default function MesMetiersLoading() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <div className="mb-6 h-8 w-48 animate-pulse rounded bg-gray-200" />
      <div className="flex flex-col gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 animate-pulse rounded-xl bg-gray-100" />
        ))}
      </div>
    </div>
  );
}
