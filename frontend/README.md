# RE-THREAD: Frontend Application

*Next.js 16 (React 19) Circular Garment Decision Interface*

This directory houses the web user interface for **RE-THREAD**.

## Features

- **Multi-angle Photo Upload**: Dedicated slots for garment views and care label photos.
- **AI Diagnostics**: Real-time display of material family, wear condition, defect area, and care tag parsing.
- **Explainability**: Convolutional visual attention overlays and SHAP feature attribution rankings.
- **Decision Engine Recommendations**: Pathway suitability scoring (Reuse, Repair, Donate, Recycle, Brand Take-Back) with distance calculations to 15 municipal facilities.
- **Partner Intake Portal**: Verification scanner interface to confirm physical drop-offs via QR tracking passports.

## Running the Frontend

```powershell
npm install
npm run dev
```

Runs on [http://localhost:3000](http://localhost:3000). Ensure the backend server is running on [http://127.0.0.1:8000](http://127.0.0.1:8000).
