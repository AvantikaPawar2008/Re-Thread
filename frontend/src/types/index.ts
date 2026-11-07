/**
 * TypeScript type definitions matching RE-THREAD API contract schemas.
 */

export type MaterialLabel = "natural" | "synthetic" | "blend" | "uncertain";
export type ConditionLabel = "new" | "gently_used" | "worn" | "heavily_worn";
export type CompositionStatus = "confident" | "uncertain";
export type PathwayType = "reuse_resell" | "repair" | "donate" | "recycle" | "brand_takeback";

export interface DamageBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  label?: string;
  confidence?: number;
}

export interface MaterialAnalysis {
  label: MaterialLabel;
  confidence: number;
  heatmap_base64?: string | null;
}

export interface ConditionAnalysis {
  label: ConditionLabel;
  confidence: number;
  heatmap_base64?: string | null;
}

export interface DamageAnalysis {
  detected: boolean;
  area_percent: number;
  boxes: DamageBox[];
}

export interface TagAnalysis {
  brand: string | null;
  composition: Record<string, number>;
  ocr_confidence: number;
  agrees_with_vision: boolean;
}

export interface AnalyzeResponse {
  material: MaterialAnalysis;
  condition: ConditionAnalysis;
  damage: DamageAnalysis;
  tag: TagAnalysis;
  composition_status: CompositionStatus;
}

export interface PartnerDropoff {
  name: string;
  distance_km: number;
  address?: string | null;
  contact_phone?: string | null;
}

export interface ImpactEstimate {
  water_litres_saved: number;
  co2_kg_saved: number;
}

export interface RankedPathway {
  pathway: string;
  score: number;
  eligible: boolean;
  nearest_partner?: PartnerDropoff | null;
  impact: ImpactEstimate;
}

export interface RecommendResponse {
  ranked_pathways: RankedPathway[];
  explanation: string;
  shap: Record<string, number>;
  qr_id: string;
}

export interface OutcomeConfirmRequest {
  qr_id: string;
  partner_facility_id: number;
  confirmed_pathway: string;
  notes?: string;
}

export interface OutcomeConfirmResponse {
  status: string;
  qr_id: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  database: string;
}
