import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchImages, fetchImageMetadata, getImageUrl } from '@/api/dicomApi';
import type { ImageInfo, ImageMetadata, WindowLevel } from '@/types/dicom';

interface UseImageLoaderResult {
  metadata: ImageMetadata | null;
  images: ImageInfo[];
  currentSlice: number;
  totalSlices: number;
  loading: boolean;
  error: string | null;
  windowLevel: WindowLevel;
  setCurrentSlice: (slice: number) => void;
  setWindowLevel: (wl: WindowLevel) => void;
  nextSlice: () => void;
  prevSlice: () => void;
  getImageUrl: () => string | null;
  /** Current image filename (e.g. "image_003.jpg") */
  currentFilename: string | undefined;
  /** All filenames in order */
  allFilenames: string[];
}

export function useImageLoader(): UseImageLoaderResult {
  const [metadata, setMetadata] = useState<ImageMetadata | null>(null);
  const [images, setImages] = useState<ImageInfo[]>([]);
  const [currentSlice, setCurrentSlice] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [windowLevel, setWindowLevel] = useState<WindowLevel>({
    windowWidth: 256,
    windowCenter: 128,
  });

  const imagesRef = useRef<ImageInfo[]>([]);
  imagesRef.current = images;

  // Load image list on mount
  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const imgs = await fetchImages();
        if (cancelled) return;

        setImages(imgs);
        setCurrentSlice(0);

        // Load metadata from first image
        if (imgs.length > 0 && imgs[0]) {
          const meta = await fetchImageMetadata(imgs[0].filename);
          if (!cancelled) setMetadata(meta);
        }
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof Error ? err.message : 'Failed to load images';
        setError(
          message.includes('Network Error')
            ? 'Cannot connect to the backend server. Make sure it is running at http://localhost:8000'
            : message
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  const totalSlices = images.length;

  const nextSlice = useCallback(() => {
    setCurrentSlice((prev) => Math.min(prev + 1, totalSlices - 1));
  }, [totalSlices]);

  const prevSlice = useCallback(() => {
    setCurrentSlice((prev) => Math.max(prev - 1, 0));
  }, []);

  const getCurrentImageUrl = useCallback((): string | null => {
    const img = imagesRef.current[currentSlice];
    if (!img) return null;
    return getImageUrl(img.filename);
  }, [currentSlice]);

  const currentFilename = images[currentSlice]?.filename;
  const allFilenames = images.map((img) => img.filename);

  return {
    metadata,
    images,
    currentSlice,
    totalSlices,
    loading,
    error,
    windowLevel,
    setCurrentSlice,
    setWindowLevel,
    nextSlice,
    prevSlice,
    getImageUrl: getCurrentImageUrl,
    currentFilename,
    allFilenames,
  };
}
