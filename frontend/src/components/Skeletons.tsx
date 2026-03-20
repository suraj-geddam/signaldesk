function Bone({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-stone-200/70 ${className}`}
    />
  );
}

export function FeedbackTableSkeleton() {
  return (
    <div className="space-y-3 mt-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 rounded-lg bg-white border border-stone-100 px-4 py-3.5"
        >
          <div className="flex-1 space-y-2">
            <Bone className="h-4 w-3/5" />
            <Bone className="h-3 w-2/5" />
          </div>
          <Bone className="h-5 w-16 rounded-md" />
          <Bone className="h-5 w-14 rounded-md" />
          <Bone className="h-4 w-12" />
          <Bone className="h-4 w-14" />
          <Bone className="h-4 w-8" />
        </div>
      ))}
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Bone className="h-4 w-20 mb-3" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-white rounded-lg border border-stone-100 p-4 space-y-2">
              <Bone className="h-3 w-16" />
              <Bone className="h-7 w-10" />
            </div>
          ))}
        </div>
      </div>
      <div>
        <Bone className="h-4 w-24 mb-3" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-white rounded-lg border border-stone-100 p-4 space-y-2">
              <Bone className="h-3 w-16" />
              <Bone className="h-7 w-10" />
            </div>
          ))}
        </div>
      </div>
      <div>
        <Bone className="h-4 w-40 mb-3" />
        <div className="bg-white rounded-lg border border-stone-100 p-4">
          <Bone className="h-48 w-full" />
        </div>
      </div>
    </div>
  );
}

export function InsightsSkeleton() {
  return (
    <div className="space-y-4 mt-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="bg-white rounded-lg border border-stone-200 p-5 space-y-3"
        >
          <div className="flex items-center justify-between">
            <Bone className="h-5 w-1/3" />
            <Bone className="h-5 w-16 rounded-md" />
          </div>
          <Bone className="h-4 w-full" />
          <Bone className="h-4 w-4/5" />
        </div>
      ))}
    </div>
  );
}
