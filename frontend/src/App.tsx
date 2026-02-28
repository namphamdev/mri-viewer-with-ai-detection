import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import DicomViewer from './components/DicomViewer';
import SliceNavigator from './components/SliceNavigator';
import { useImageLoader } from './hooks/useDicomLoader';
import { analyzeImage } from './api/dicomApi';
import type { SliceAIState, AIOverlay } from './types/dicom';

export default function App() {
  const {
    metadata,
    currentSlice,
    totalSlices,
    loading,
    error,
    windowLevel,
    setCurrentSlice,
    setWindowLevel,
    nextSlice,
    prevSlice,
    getImageUrl,
    currentFilename,
    allFilenames,
  } = useImageLoader();

  const imageUrl = getImageUrl();

  // AI state
  const [aiCache, setAiCache] = useState<Record<number, SliceAIState>>({});
  const [overlayVisible, setOverlayVisible] = useState(true);
  const [overlayOpacity, setOverlayOpacity] = useState(0.6);

  const currentOverlay: AIOverlay | null =
    aiCache[currentSlice]?.result?.overlay ?? null;

  // Analyze a single slice by filename
  const handleAnalyzeSlice = useCallback(
    async (sliceIndex: number, filename: string, sensitivity: number) => {
      const result = await analyzeImage(filename, sensitivity);
      setAiCache((prev) => ({
        ...prev,
        [sliceIndex]: { result, analyzedAt: Date.now() },
      }));
    },
    []
  );

  // Set of analyzed slice indices for the navigator
  const analyzedSlices = new Set(
    Object.keys(aiCache).map((k) => Number(k))
  );

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        nextSlice();
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        prevSlice();
      }
    },
    [nextSlice, prevSlice]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="h-screen flex flex-col bg-medical-bg text-medical-text overflow-hidden">
      {/* Header */}
      <Header metadata={metadata} />

      {/* Main content area */}
      <div className="flex flex-1 min-h-0">
        {/* Viewer */}
        <DicomViewer
          imageUrl={imageUrl}
          loading={loading}
          error={error}
          overlay={currentOverlay}
          overlayVisible={overlayVisible}
          overlayOpacity={overlayOpacity}
        />

        {/* Sidebar */}
        <Sidebar
          metadata={metadata}
          windowLevel={windowLevel}
          onWindowLevelChange={setWindowLevel}
          currentSlice={currentSlice}
          totalSlices={totalSlices}
          currentFilename={currentFilename}
          allFilenames={allFilenames}
          aiCache={aiCache}
          onAnalyzeSlice={handleAnalyzeSlice}
          overlayVisible={overlayVisible}
          onToggleOverlay={() => setOverlayVisible((v) => !v)}
          overlayOpacity={overlayOpacity}
          onOverlayOpacityChange={setOverlayOpacity}
        />
      </div>

      {/* Slice Navigator */}
      <SliceNavigator
        currentSlice={currentSlice}
        totalSlices={totalSlices}
        onSliceChange={setCurrentSlice}
        onNext={nextSlice}
        onPrev={prevSlice}
        analyzedSlices={analyzedSlices}
      />
    </div>
  );
}
