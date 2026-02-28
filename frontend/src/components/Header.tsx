import type { ImageMetadata } from '@/types/dicom';

interface HeaderProps {
  metadata: ImageMetadata | null;
}

export default function Header({ metadata }: HeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 py-3 bg-medical-surface border-b border-medical-border">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <svg
            className="w-7 h-7 text-medical-accent"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
          <h1 className="text-xl font-bold text-white tracking-wide">
            MRI Viewer
          </h1>
        </div>
        {metadata && (
          <span className="ml-4 text-xs text-medical-text-muted bg-medical-panel px-3 py-1 rounded-full border border-medical-border">
            {metadata.modality}
            {metadata.series_description
              ? ` · ${metadata.series_description}`
              : ''}
          </span>
        )}
      </div>

      <div className="flex items-center gap-4 text-sm text-medical-text-muted">
        {metadata?.patient_id && (
          <span>
            Patient: <span className="text-medical-text">{metadata.patient_id}</span>
          </span>
        )}
        {metadata?.study_description && (
          <span>
            Study: <span className="text-medical-text">{metadata.study_description}</span>
          </span>
        )}
      </div>
    </header>
  );
}
