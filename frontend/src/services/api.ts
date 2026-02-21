/**
 * API service for communicating with the Vedic Astrology backend
 */

import type { BirthData, Chart, DashaTimeline, CurrentDasha } from '../types/astrology';

// In production (Vercel), VITE_API_BASE_URL is set to the Render backend URL.
// In local dev, it is unset and Vite's proxy forwards /api/* to localhost:8000.
const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api/v1`
  : '/api/v1';

// Helper to convert camelCase to snake_case for API requests
function toSnakeCase(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const key in obj) {
    const snakeKey = key.replace(/([A-Z])/g, '_$1').toLowerCase();
    result[snakeKey] = obj[key];
  }
  return result;
}

// Helper to convert snake_case to camelCase for API responses
function toCamelCase<T>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map(item => toCamelCase(item)) as T;
  }

  if (obj !== null && typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const key in obj as Record<string, unknown>) {
      const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
      result[camelKey] = toCamelCase((obj as Record<string, unknown>)[key]);
    }
    return result as T;
  }

  return obj as T;
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  const data = await response.json();
  return toCamelCase<T>(data);
}

/**
 * Generate a complete Vedic birth chart
 */
export async function generateChart(birthData: BirthData): Promise<Chart> {
  return apiRequest<Chart>('/chart', {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

/**
 * Get complete Dasha timeline with Antardashas
 */
export async function getDashaTimeline(
  birthData: BirthData,
  yearsAhead: number = 120
): Promise<DashaTimeline> {
  const params = new URLSearchParams({ years_ahead: yearsAhead.toString() });
  return apiRequest<DashaTimeline>(`/dasha/timeline?${params}`, {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

/**
 * Get currently running Dasha periods
 */
export async function getCurrentDasha(
  birthData: BirthData,
  targetDate?: Date
): Promise<CurrentDasha> {
  const params = new URLSearchParams();
  if (targetDate) {
    params.set('target_date', targetDate.toISOString());
  }

  const queryString = params.toString();
  const url = queryString ? `/dasha/current?${queryString}` : '/dasha/current';

  return apiRequest<CurrentDasha>(url, {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

/**
 * Get planetary positions only
 */
export async function getPlanetPositions(birthData: BirthData) {
  return apiRequest<{ planets: Chart['planets']; ascendant: Chart['ascendant'] }>('/planets', {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

/**
 * Get Moon's nakshatra details
 */
export async function getMoonNakshatra(birthData: BirthData) {
  return apiRequest<Chart['moonNakshatra']>('/nakshatra', {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

/**
 * Health check
 */
export async function healthCheck() {
  return apiRequest<{ status: string; version: string; timestamp: string }>('/health');
}

// ============ PREDICTIONS API ============

export interface AreaPrediction {
  trend: 'positive' | 'negative' | 'mixed' | 'neutral';
  intensity: string;
  summary: string;
  details: string[];
  remedies: string[];
  keywords: string[];
}

export interface DashaPredictionData {
  dashaLord: string;
  periodType: string;
  overallTheme: string;
  overallRating: number;
  predictions: {
    health: AreaPrediction;
    wealth: AreaPrediction;
    career: AreaPrediction;
    relationships: AreaPrediction;
    general: AreaPrediction;
  };
  favorableActivities: string[];
  unfavorableActivities: string[];
  remedies: {
    gemstone: string | null;
    mantra: string | null;
    deity: string | null;
  };
  currentPeriods?: {
    mahadasha: { lord: string; start: string; end: string };
    antardasha?: { lord: string; start: string; end: string };
    pratyantardasha?: { lord: string; start: string; end: string };
  };
}

/**
 * Get prediction for the current Dasha period
 */
export async function getCurrentPrediction(
  birthData: BirthData,
  targetDate?: Date
): Promise<DashaPredictionData> {
  const params = new URLSearchParams();
  if (targetDate) {
    params.set('target_date', targetDate.toISOString());
  }

  const queryString = params.toString();
  const url = queryString ? `/predictions/current?${queryString}` : '/predictions/current';

  return apiRequest<DashaPredictionData>(url, {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

/**
 * Get prediction for a specific Mahadasha
 */
export async function getMahadashaPrediction(
  birthData: BirthData,
  dashaLord: string
): Promise<DashaPredictionData> {
  return apiRequest<DashaPredictionData>(`/predictions/mahadasha/${dashaLord}`, {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

/**
 * Get prediction for a specific Antardasha combination
 */
export async function getAntardashaPrediction(
  birthData: BirthData,
  mahadasha: string,
  antardasha: string
): Promise<DashaPredictionData> {
  return apiRequest<DashaPredictionData>(`/predictions/antardasha/${mahadasha}/${antardasha}`, {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

/**
 * Get timeline with full predictions
 */
export async function getTimelineWithPredictions(
  birthData: BirthData,
  yearsAhead: number = 80
): Promise<unknown[]> {
  const params = new URLSearchParams({ years_ahead: yearsAhead.toString() });
  return apiRequest<unknown[]>(`/predictions/timeline?${params}`, {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

/**
 * Get remedies for current period
 */
export async function getRemedies(birthData: BirthData): Promise<{
  currentPeriods: unknown;
  gemstone: string | null;
  mantra: string | null;
  deity: string | null;
  favorableActivities: string[];
  unfavorableActivities: string[];
  areaRemedies: Record<string, string[]>;
}> {
  return apiRequest(`/predictions/remedies`, {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(birthData as unknown as Record<string, unknown>)),
  });
}

