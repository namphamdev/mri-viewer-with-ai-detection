import { useRef, useEffect, useState, useCallback } from 'react';
import type { AIOverlay } from '@/types/dicom';

interface DicomViewerProps {
  imageUrl: string | null;
  loading: boolean;
  error: string | null;
  overlay: AIOverlay | null;
  overlayVisible: boolean;
  overlayOpacity: number;
}

export default function DicomViewer({
  imageUrl,
  loading,
  error,
  overlay,
  overlayVisible,
  overlayOpacity,
}: DicomViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  // Track last drawn image dimensions for overlay positioning
  const drawInfoRef = useRef<{ x: number; y: number; w: number; h: number } | null>(null);

  const drawImage = useCallback((img: HTMLImageElement) => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Size canvas to container
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    // Calculate aspect-fit dimensions
    const imgAspect = img.width / img.height;
    const containerAspect = containerWidth / containerHeight;

    let drawWidth: number;
    let drawHeight: number;

    if (imgAspect > containerAspect) {
      drawWidth = containerWidth;
      drawHeight = containerWidth / imgAspect;
    } else {
      drawHeight = containerHeight;
      drawWidth = containerHeight * imgAspect;
    }

    canvas.width = containerWidth;
    canvas.height = containerHeight;

    // Clear and draw centered
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, containerWidth, containerHeight);

    const x = (containerWidth - drawWidth) / 2;
    const y = (containerHeight - drawHeight) / 2;

    ctx.drawImage(img, x, y, drawWidth, drawHeight);

    // Store draw info for overlay
    drawInfoRef.current = { x, y, w: drawWidth, h: drawHeight };
  }, []);

  // Draw overlay on separate canvas
  const drawOverlay = useCallback(() => {
    const overlayCanvas = overlayCanvasRef.current;
    const container = containerRef.current;
    if (!overlayCanvas || !container) return;

    const ctx = overlayCanvas.getContext('2d');
    if (!ctx) return;

    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;
    overlayCanvas.width = containerWidth;
    overlayCanvas.height = containerHeight;

    ctx.clearRect(0, 0, containerWidth, containerHeight);

    if (!overlay || !overlayVisible || !drawInfoRef.current) return;

    const { x, y, w, h } = drawInfoRef.current;

    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, containerWidth, containerHeight);
      ctx.globalAlpha = overlayOpacity;
      ctx.drawImage(img, x, y, w, h);
      ctx.globalAlpha = 1;
    };
    img.src = `data:image/png;base64,${overlay.data}`;
  }, [overlay, overlayVisible, overlayOpacity]);

  useEffect(() => {
    if (!imageUrl) return;

    setImageLoading(true);
    setImageError(null);

    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      setImageLoading(false);
      drawImage(img);
      // Redraw overlay after main image
      drawOverlay();
    };

    img.onerror = () => {
      setImageLoading(false);
      setImageError('Failed to load image frame');
    };

    img.src = imageUrl;
  }, [imageUrl, drawImage, drawOverlay]);

  // Redraw overlay when overlay props change
  useEffect(() => {
    drawOverlay();
  }, [drawOverlay]);

  // Handle resize
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver(() => {
      // Re-render current image on resize
      if (imageUrl) {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
          drawImage(img);
          drawOverlay();
        };
        img.src = imageUrl;
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, [imageUrl, drawImage, drawOverlay]);

  // Render placeholder when no image
  const renderPlaceholder = () => (
    <div className="flex flex-col items-center justify-center h-full text-medical-text-muted gap-3">
      <svg
        className="w-16 h-16 opacity-30"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1}
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
      <p className="text-sm">No image loaded</p>
      <p className="text-xs opacity-60">
        Waiting for backend connection...
      </p>
    </div>
  );

  return (
    <div
      ref={containerRef}
      className="flex-1 bg-black relative overflow-hidden"
    >
      {/* Main DICOM canvas */}
      <canvas
        ref={canvasRef}
        className={`w-full h-full ${!imageUrl ? 'hidden' : ''}`}
      />

      {/* AI overlay canvas — sits on top, pointer-events disabled */}
      <canvas
        ref={overlayCanvasRef}
        className={`absolute inset-0 w-full h-full pointer-events-none transition-opacity duration-200 ${
          overlayVisible ? 'opacity-100' : 'opacity-0'
        } ${!imageUrl ? 'hidden' : ''}`}
      />

      {/* Loading overlay */}
      {(loading || imageLoading) && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/70">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-3 border-medical-accent border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-medical-text-muted">
              Loading DICOM data...
            </span>
          </div>
        </div>
      )}

      {/* Error display */}
      {(error || imageError) && !loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="bg-medical-panel border border-medical-error/30 rounded-lg p-6 max-w-md mx-4 text-center">
            <svg
              className="w-12 h-12 text-medical-error mx-auto mb-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <h3 className="text-medical-error font-semibold mb-1">
              Connection Error
            </h3>
            <p className="text-sm text-medical-text-muted">
              {error || imageError}
            </p>
          </div>
        </div>
      )}

      {/* Placeholder when no data */}
      {!imageUrl && !loading && !error && renderPlaceholder()}
    </div>
  );
}
