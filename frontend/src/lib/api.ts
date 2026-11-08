/**
 * API client library for RE-THREAD backend communication.
 */

import {
  AnalyzeResponse,
  HealthResponse,
  RecommendResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function checkBackendHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    method: "GET",
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Health check failed with status ${res.status}`);
  }
  return res.json();
}

export async function analyzeGarment(formData: FormData): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text();
    let message = "Garment analysis failed.";
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.detail || message;
    } catch {
      // fallback
    }
    throw new Error(message);
  }

  return res.json();
}

export async function getRecommendations(
  analysis: AnalyzeResponse,
  userLatitude: number,
  userLongitude: number,
  garmentWeightKg: number = 0.5
): Promise<RecommendResponse> {
  const payload = {
    analysis,
    user_latitude: userLatitude,
    user_longitude: userLongitude,
    garment_weight_kg: garmentWeightKg,
  };

  const res = await fetch(`${API_BASE_URL}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorText = await res.text();
    let message = "Generating recommendations failed.";
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.detail || message;
    } catch {
      // fallback
    }
    throw new Error(message);
  }

  return res.json();
}

export async function confirmOutcome(
  qrId: string,
  partnerFacilityId: number,
  confirmedPathway: string,
  notes?: string
): Promise<{ status: string; qr_id: string; message: string }> {
  const payload = {
    qr_id: qrId,
    partner_facility_id: partnerFacilityId,
    confirmed_pathway: confirmedPathway,
    notes: notes || "Scanned via drop-off confirmation interface",
  };

  const res = await fetch(`${API_BASE_URL}/outcome/confirm`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorText = await res.text();
    let message = "Outcome confirmation failed.";
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.detail || message;
    } catch {
      // fallback
    }
    throw new Error(message);
  }

  return res.json();
}

export async function identifyFabric(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("garment_images", file);

  try {
    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      body: formData,
    });
    if (res.ok) {
      const data = await res.json();
      if (data.material) {
        return {
          fabric: data.material.label,
          confidence: data.material.confidence,
          top: [
            { label: data.material.label, confidence: data.material.confidence }
          ]
        };
      }
      return data;
    }
  } catch {
    // try fallback
  }

  const res = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Fabric identification failed");
  }
  const data = await res.json();
  if (data.material) {
    return {
      fabric: data.material.label,
      confidence: data.material.confidence,
      top: [
        { label: data.material.label, confidence: data.material.confidence }
      ]
    };
  }
  return data;
}

