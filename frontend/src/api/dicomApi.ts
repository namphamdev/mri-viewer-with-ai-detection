import axios from 'axios';
import type { ImageInfo, ImageMetadata, AIAnalysisResult } from '@/types/dicom';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
});

/** Fetch the list of available MRI images. */
export async function fetchImages(): Promise<ImageInfo[]> {
  const { data } = await api.get<{ images: ImageInfo[]; total: number }>('/images');
  return data.images;
}

/** Get the URL for a specific image file. */
export function getImageUrl(filename: string): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
  return `${baseUrl}/images/${encodeURIComponent(filename)}`;
}

/** Fetch synthetic metadata for an image. */
export async function fetchImageMetadata(filename: string): Promise<ImageMetadata> {
  const { data } = await api.get<ImageMetadata>(
    `/images/${encodeURIComponent(filename)}/metadata`
  );
  return data;
}

/** Run AI analysis on an image. */
export async function analyzeImage(
  imageName: string,
  sensitivity: number = 0.5
): Promise<AIAnalysisResult> {
  const { data } = await api.post<AIAnalysisResult>('/ai/analyze', {
    image_name: imageName,
    sensitivity,
  });
  return data;
}
