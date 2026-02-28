interface SliceNavigatorProps {
  currentSlice: number;
  totalSlices: number;
  onSliceChange: (slice: number) => void;
  onNext: () => void;
  onPrev: () => void;
  analyzedSlices?: Set<number>;
}

export default function SliceNavigator({
  currentSlice,
  totalSlices,
  onSliceChange,
  onNext,
  onPrev,
  analyzedSlices,
}: SliceNavigatorProps) {
  const disabled = totalSlices === 0;
  const hasAnalyzed = analyzedSlices && analyzedSlices.size > 0;

  return (
    <div className="flex items-center gap-4 px-6 py-3 bg-medical-surface border-t border-medical-border">
      {/* Previous button */}
      <button
        onClick={onPrev}
        disabled={disabled || currentSlice === 0}
        className="p-2 rounded-lg bg-medical-panel border border-medical-border text-medical-text hover:bg-medical-accent/20 hover:border-medical-accent/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Previous slice"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      {/* Slider with analyzed indicators */}
      <div className="flex-1 flex flex-col gap-1">
        {/* Analyzed dot indicators */}
        {hasAnalyzed && totalSlices > 0 && (
          <div className="flex w-full h-1.5 gap-px">
            {Array.from({ length: totalSlices }, (_, i) => (
              <div
                key={i}
                className={`flex-1 rounded-full transition-colors ${
                  analyzedSlices.has(i)
                    ? 'bg-green-500/60'
                    : 'bg-medical-panel'
                } ${i === currentSlice ? 'ring-1 ring-medical-accent' : ''}`}
              />
            ))}
          </div>
        )}

        <input
          type="range"
          min={0}
          max={Math.max(totalSlices - 1, 0)}
          value={currentSlice}
          onChange={(e) => onSliceChange(Number(e.target.value))}
          disabled={disabled}
          className="flex-1 h-2 bg-medical-panel rounded-lg appearance-none cursor-pointer accent-medical-accent disabled:opacity-30 disabled:cursor-not-allowed"
        />
      </div>

      {/* Next button */}
      <button
        onClick={onNext}
        disabled={disabled || currentSlice >= totalSlices - 1}
        className="p-2 rounded-lg bg-medical-panel border border-medical-border text-medical-text hover:bg-medical-accent/20 hover:border-medical-accent/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        aria-label="Next slice"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Slice counter */}
      <div className="text-sm text-medical-text-muted min-w-[100px] text-center tabular-nums">
        {disabled ? (
          <span className="italic">No data</span>
        ) : (
          <>
            Slice{' '}
            <span className="text-medical-text font-semibold">
              {currentSlice + 1}
            </span>{' '}
            / {totalSlices}
          </>
        )}
      </div>
    </div>
  );
}
