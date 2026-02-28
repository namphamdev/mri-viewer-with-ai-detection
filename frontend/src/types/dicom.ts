/** Image info returned by GET /api/images */
export interface ImageInfo {
  filename: string;
  size_bytes: number;
  url: string;
}

/** Metadata returned by GET /api/images/{filename}/metadata */
export interface ImageMetadata {
  filename: string;
  modality: string;
  series_description: string;
  rows: number;
  columns: number;
  slice_number: number;
  slice_thickness: number;
  pixel_spacing: number[];
  window_center: number;
  window_width: number;
  patient_id: string;
  study_description: string;
  size_bytes: number;
}

export interface WindowLevel {
  windowWidth: number;
  windowCenter: number;
}

export interface WindowPreset {
  name: string;
  windowWidth: number;
  windowCenter: number;
}

// --- AI Analysis types matching backend response ---

export interface AIFindingLocation {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface AIFinding {
  id: string;
  type: string;
  description: string;
  confidence: number;
  location: AIFindingLocation;
  severity: string;
}

export interface AIOverlay {
  type: string;
  data: string; // base64 PNG
  width: number;
  height: number;
  colormap: string;
}

export interface AISummary {
  total_findings: number;
  max_confidence: number;
  regions_analyzed: number;
  recommendation: string;
}

export interface AIAnalysisResult {
  status: string;
  analysis_type: string;
  processing_time_ms: number;
  findings: AIFinding[];
  overlay: AIOverlay;
  summary: AISummary;
}

/** Per-slice cached AI state */
export interface SliceAIState {
  result: AIAnalysisResult;
  analyzedAt: number;
}

export const WINDOW_PRESETS: WindowPreset[] = [
  { name: 'Brain', windowWidth: 80, windowCenter: 40 },
  { name: 'Subdural', windowWidth: 300, windowCenter: 75 },
  { name: 'Bone', windowWidth: 2800, windowCenter: 600 },
  { name: 'Soft Tissue', windowWidth: 400, windowCenter: 50 },
  { name: 'Lung', windowWidth: 1500, windowCenter: -600 },
  { name: 'Default', windowWidth: 400, windowCenter: 40 },
];
