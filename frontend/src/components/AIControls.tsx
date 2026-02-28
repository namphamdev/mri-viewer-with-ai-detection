import { useState, useCallback } from 'react';
import type { AIAnalysisResult, AIFinding, SliceAIState } from '@/types/dicom';

interface AIControlsProps {
  currentSlice: number;
  totalSlices: number;
  currentFilename: string | undefined;
  allFilenames: string[];
  aiCache: Record<number, SliceAIState>;
  onAnalyzeSlice: (sliceIndex: number, filename: string, sensitivity: number) => Promise<void>;
  overlayVisible: boolean;
  onToggleOverlay: () => void;
  overlayOpacity: number;
  onOverlayOpacityChange: (opacity: number) => void;
}

export default function AIControls({
  currentSlice,
  totalSlices,
  currentFilename,
  allFilenames,
  aiCache,
  onAnalyzeSlice,
  overlayVisible,
  onToggleOverlay,
  overlayOpacity,
  onOverlayOpacityChange,
}: AIControlsProps) {
  const [sensitivity, setSensitivity] = useState(0.5);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzingAll, setAnalyzingAll] = useState(false);
  const [analyzeAllProgress, setAnalyzeAllProgress] = useState(0);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  const currentResult: AIAnalysisResult | null = aiCache[currentSlice]?.result ?? null;

  const handleAnalyzeCurrent = useCallback(async () => {
    if (!currentFilename || analyzing || analyzingAll) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      await onAnalyzeSlice(currentSlice, currentFilename, sensitivity);
    } catch (err) {
      setAnalyzeError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  }, [currentFilename, currentSlice, sensitivity, analyzing, analyzingAll, onAnalyzeSlice]);

  const handleAnalyzeAll = useCallback(async () => {
    if (analyzingAll || totalSlices === 0) return;
    setAnalyzingAll(true);
    setAnalyzeAllProgress(0);
    setAnalyzeError(null);
    try {
      for (let i = 0; i < totalSlices; i++) {
        const fname = allFilenames[i];
        if (!fname) continue;
        if (aiCache[i]) {
          setAnalyzeAllProgress(i + 1);
          continue;
        }
        await onAnalyzeSlice(i, fname, sensitivity);
        setAnalyzeAllProgress(i + 1);
      }
    } catch (err) {
      setAnalyzeError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setAnalyzingAll(false);
    }
  }, [analyzingAll, totalSlices, allFilenames, aiCache, sensitivity, onAnalyzeSlice]);

  const analyzedCount = Object.keys(aiCache).length;

  return (
    <div className="space-y-3">
      {/* Sensitivity slider */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="text-xs text-medical-text-muted">Sensitivity</label>
          <span className="text-xs text-medical-text tabular-nums">{sensitivity.toFixed(2)}</span>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={sensitivity}
          onChange={(e) => setSensitivity(Number(e.target.value))}
          className="w-full h-1.5 bg-medical-panel rounded-lg appearance-none cursor-pointer accent-medical-accent"
        />
      </div>

      {/* Analyze buttons */}
      <button
        onClick={handleAnalyzeCurrent}
        disabled={!currentFilename || analyzing || analyzingAll}
        className="w-full px-3 py-2 rounded-lg bg-green-600/20 border border-green-500/40 text-green-400 text-sm font-medium
          hover:bg-green-600/30 hover:border-green-500/60 hover:shadow-[0_0_12px_rgba(34,197,94,0.15)]
          disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-none
          transition-all duration-200 flex items-center justify-center gap-2"
      >
        {analyzing ? (
          <>
            <Spinner />
            Analyzing...
          </>
        ) : (
          <>Analyze Current Slice</>
        )}
      </button>

      <button
        onClick={handleAnalyzeAll}
        disabled={analyzingAll || totalSlices === 0}
        className="w-full px-3 py-2 rounded-lg bg-green-600/10 border border-green-500/20 text-green-400/80 text-sm font-medium
          hover:bg-green-600/20 hover:border-green-500/40 hover:shadow-[0_0_12px_rgba(34,197,94,0.1)]
          disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-none
          transition-all duration-200 flex items-center justify-center gap-2"
      >
        {analyzingAll ? (
          <>
            <Spinner />
            Analyzing All...
          </>
        ) : (
          <>Analyze All Slices</>
        )}
      </button>

      {/* PLACEHOLDER_REST */}

      {/* Progress bar for Analyze All */}
      {analyzingAll && totalSlices > 0 && (
        <div>
          <div className="flex justify-between text-xs text-medical-text-muted mb-1">
            <span>Progress</span>
            <span className="tabular-nums">
              {analyzeAllProgress}/{totalSlices}
            </span>
          </div>
          <div className="w-full h-2 bg-medical-panel rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 rounded-full transition-all duration-300"
              style={{ width: `${(analyzeAllProgress / totalSlices) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Analyzed count */}
      {analyzedCount > 0 && !analyzingAll && (
        <div className="text-xs text-medical-text-muted text-center">
          {analyzedCount}/{totalSlices} slices analyzed
        </div>
      )}

      {/* Error */}
      {analyzeError && (
        <div className="text-xs text-medical-error bg-medical-error/10 rounded px-2 py-1.5 border border-medical-error/20">
          {analyzeError}
        </div>
      )}

      {/* Overlay controls */}
      {analyzedCount > 0 && (
        <div className="space-y-2 pt-2 border-t border-medical-border">
          <button
            onClick={onToggleOverlay}
            className={`w-full px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              overlayVisible
                ? 'bg-medical-accent text-white'
                : 'bg-medical-panel border border-medical-border text-medical-text-muted hover:bg-medical-accent/20'
            }`}
          >
            {overlayVisible ? 'Hide Overlay' : 'Show Overlay'}
          </button>

          {overlayVisible && (
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs text-medical-text-muted">Opacity</label>
                <span className="text-xs text-medical-text tabular-nums">
                  {Math.round(overlayOpacity * 100)}%
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={overlayOpacity}
                onChange={(e) => onOverlayOpacityChange(Number(e.target.value))}
                className="w-full h-1.5 bg-medical-panel rounded-lg appearance-none cursor-pointer accent-medical-accent"
              />
            </div>
          )}
        </div>
      )}

      {/* Results panel */}
      {currentResult && (
        <div className="space-y-2 pt-2 border-t border-medical-border">
          <h3 className="text-xs font-semibold text-medical-text-muted uppercase tracking-wider">
            Results
          </h3>
          <div className="grid grid-cols-2 gap-1.5 text-xs">
            <div className="bg-medical-panel rounded px-2 py-1.5">
              <div className="text-medical-text-muted">Findings</div>
              <div className="text-medical-text font-semibold">
                {currentResult.findings.length}
              </div>
            </div>
            <div className="bg-medical-panel rounded px-2 py-1.5">
              <div className="text-medical-text-muted">Time</div>
              <div className="text-medical-text font-semibold">
                {currentResult.processing_time_ms}ms
              </div>
            </div>
          </div>
          {currentResult.summary?.recommendation && (
            <p className="text-xs text-medical-text-muted leading-relaxed">
              {currentResult.summary.recommendation}
            </p>
          )}
          {currentResult.findings.length > 0 && (
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {currentResult.findings.map((finding) => (
                <FindingCard key={finding.id} finding={finding} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FindingCard({ finding }: { finding: AIFinding }) {
  const severityColor = getSeverityColor(finding.severity);
  return (
    <div className={`rounded border px-2 py-1.5 text-xs ${severityColor.bg} ${severityColor.border}`}>
      <div className="flex items-center justify-between mb-1">
        <span className={`font-medium ${severityColor.text}`}>
          {finding.severity.charAt(0).toUpperCase() + finding.severity.slice(1)}
        </span>
        <span className="text-medical-text-muted tabular-nums">
          {(finding.confidence * 100).toFixed(0)}%
        </span>
      </div>
      <div className="w-full h-1 bg-medical-bg/40 rounded-full overflow-hidden mb-1">
        <div
          className={`h-full rounded-full ${severityColor.bar}`}
          style={{ width: `${finding.confidence * 100}%` }}
        />
      </div>
      <p className="text-medical-text-muted leading-snug">{finding.description}</p>
    </div>
  );
}

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'high':
      return { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', bar: 'bg-red-500' };
    case 'moderate':
      return { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400', bar: 'bg-orange-500' };
    default:
      return { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', bar: 'bg-blue-500' };
  }
}

function Spinner() {
  return (
    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
  );
}
