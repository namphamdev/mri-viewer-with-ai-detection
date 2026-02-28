import type { ImageMetadata, WindowLevel, SliceAIState } from '@/types/dicom';
import WindowingControls from './WindowingControls';
import AIControls from './AIControls';

interface SidebarProps {
  metadata: ImageMetadata | null;
  windowLevel: WindowLevel;
  onWindowLevelChange: (wl: WindowLevel) => void;
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

export default function Sidebar({
  metadata,
  windowLevel,
  onWindowLevelChange,
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
}: SidebarProps) {
  return (
    <aside className="w-72 bg-medical-surface border-l border-medical-border flex flex-col overflow-y-auto">
      {/* Image Info */}
      <div className="p-4 border-b border-medical-border">
        <h2 className="text-sm font-semibold text-medical-text-muted uppercase tracking-wider mb-3">
          Image Info
        </h2>
        {metadata ? (
          <div className="space-y-2 text-sm">
            <InfoRow label="Modality" value={metadata.modality} />
            <InfoRow label="Description" value={metadata.series_description || '—'} />
            <InfoRow label="Slices" value={String(totalSlices)} />
            {metadata.rows && metadata.columns && (
              <InfoRow label="Matrix" value={`${metadata.rows} × ${metadata.columns}`} />
            )}
            {metadata.slice_thickness && (
              <InfoRow label="Slice Thickness" value={`${metadata.slice_thickness} mm`} />
            )}
            <InfoRow
              label="Current Slice"
              value={totalSlices > 0 ? `${currentSlice + 1} / ${totalSlices}` : '—'}
            />
          </div>
        ) : (
          <p className="text-sm text-medical-text-muted italic">Loading...</p>
        )}
      </div>

      {/* Windowing Controls */}
      <div className="p-4 border-b border-medical-border">
        <h2 className="text-sm font-semibold text-medical-text-muted uppercase tracking-wider mb-3">
          Window / Level
        </h2>
        <WindowingControls
          windowLevel={windowLevel}
          onChange={onWindowLevelChange}
        />
      </div>

      {/* AI Controls */}
      <div className="p-4">
        <h2 className="text-sm font-semibold text-medical-text-muted uppercase tracking-wider mb-3">
          AI Analysis
        </h2>
        <AIControls
          currentSlice={currentSlice}
          totalSlices={totalSlices}
          currentFilename={currentFilename}
          allFilenames={allFilenames}
          aiCache={aiCache}
          onAnalyzeSlice={onAnalyzeSlice}
          overlayVisible={overlayVisible}
          onToggleOverlay={onToggleOverlay}
          overlayOpacity={overlayOpacity}
          onOverlayOpacityChange={onOverlayOpacityChange}
        />
      </div>
    </aside>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-medical-text-muted">{label}</span>
      <span className="text-medical-text font-medium truncate ml-2 max-w-[140px]">
        {value}
      </span>
    </div>
  );
}
