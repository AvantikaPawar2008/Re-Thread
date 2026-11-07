# RE-THREAD: Frontend Application

*Next.js 16 (React 19) Circular Garment Decision Interface*

This directory houses the web user interface for **RE-THREAD**.

## Features Implemented

- **Multi-slot Photo Upload**: 3 garment photo slots (front, back, fabric detail) + 1 care label photo slot.
- **AI Vision Analysis**: Displays material classification, wear condition, defect percentage, and parsed care tag.
- **Source Badges**:
  - `AI vision analysis (estimate)` badge when running via VLM perception API.
  - `Demo mode` badge when operating on fallback stubs.
- **Defect Area Estimation**: Labeled clearly as estimated when powered by VLM analysis.
- **AI Visual Reasoning**: Shows one-sentence visual evidence statements per category directly on the analysis cards.
- **Explainability**: PyTorch Grad-CAM visual attention overlays (when running with local ResNet-18 weights) and SHAP feature attribution waterfall.
- **Circular Recommendations**: Filtered by municipal eligibility constraints, scored by XGBoost / weighted formula, and ordered by proximity to 15 regional Pune facilities.
- **Partner Intake QR Portal**: Partner facility scanner interface for physical drop-off verification.

## Running the Frontend

```powershell
# From the frontend directory:
npm install
npm run dev
```

Application runs at [http://localhost:3000](http://localhost:3000). Ensure the backend is running at [http://127.0.0.1:8000](http://127.0.0.1:8000).
