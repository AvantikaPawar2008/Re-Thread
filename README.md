# RE-THREAD: Circular Fashion Decision Platform

*AI-Powered Circular Garment Decision System · Computer Vision · OCR · XGBoost & SHAP Explainability · Lifecycle Tracking*

> **Tagline:** *"Your Clothes. Your Stories. Their Next Chapter."*
> **Initiative:** PCCOE Pune · International Grand Challenge 2026 (AI for Climate Change)

---

## 1. Executive Summary & Architecture

**RE-THREAD** transforms how people dispose of unwanted clothing. Instead of sending garments to municipal landfills (e.g., Pune's Urali Devachi depot), users photograph their garment (and optional care tag) to trigger an automated circular diagnosis:

```
[Uploaded Photos] 
       │
       ├──► YOLOv8 Damage Detector (Defect bounding boxes & % area)
       ├──► ResNet-18 Fabric Classifier (Natural / Synthetic / Blend / Uncertain) ──► Grad-CAM Heatmap
       ├──► ResNet-18 Wear Classifier (New / Gently Used / Worn / Heavily Worn)   ──► Grad-CAM Heatmap
       └──► Care Tag Pipeline (YOLOv8 crop ──► OpenCV CLAHE/Deskew ──► OCR ──► RapidFuzz Brand + Regex Fibers)
       │
[Diagnostic Profile]
       ▼
[Hybrid Decision Engine]
       ├──► Layer A: Deterministic SQL Rules (Brand take-back, recyclability, repair threshold)
       ├──► Layer B: XGBoost Multi-Target Ranker with real shap.TreeExplainer Feature Attributions
       ├──► Layer C: Pune Haversine Geo-Routing (15 facilities) + Cited WRAP/EMF LCA Impact Metrics
       └──► Plain-Language Explanation & Cryptographic QR Passport
       │
[Partner Confirmation Loop]
       ▼
[Drop-off Partner Intake Scan (POST /outcome/confirm)] ──► Real Verified Outcome & Certificate
```

---

## 2. Core Features & Phase 7 Highlights

1. **Grad-CAM Visual Heatmap Explainability**:
   - ResNet-18 convolutional activations from `layer4[-1]` are extracted using `pytorch-grad-cam`.
   - Superimposed as color-graded heatmaps (red = high fabric weave/wear attention) and returned as base64 overlays for interactive frontend inspection.
2. **XGBoost Decision Ranker & SHAP TreeExplainer**:
   - Pluggable behind the `BaseRanker` interface (`RANKER_TYPE="xgboost"` in `config.py`).
   - Trained on circular fashion lifecycle decision patterns.
   - Calculates exact feature-level SHAP values (`condition`, `material`, `damage_percent`, `brand`) for the winning pathway.
3. **Automated Care Tag Extraction & Cross-Checking**:
   - YOLOv8 tag detection, OpenCV deskew/CLAHE binarization, PaddleOCR, RapidFuzz brand alias matching, and $\sim 100\%$ fiber percentage validation.
   - Automatically cross-checks OCR composition against visual prediction (`agrees_with_vision`).
4. **Partner QR Scan Intake Portal**:
   - Dedicated interface for authorized Pune drop-off hubs to scan QR passports and confirm real outcomes via `POST /outcome/confirm`.
5. **Municipal Impact Dashboard**:
   - Tracks garments diverted, water conserved (litres), $\text{CO}_2$ avoided (kg), and ward-level circular progress across Pune (FC Road, Kothrud, Camp, Viman Nagar, Hadapsar, PCMC).

---

## 3. Quickstart & Local Setup

### Step 1: Backend Setup (Python 3.11+)

```powershell
# Navigate to repo root
cd "c:\ai project\rethread"

# Install backend dependencies
pip install -r backend/requirements.txt
pip install grad-cam xgboost shap

# Seed SQLite database with 15 Pune hubs, 8 brands, and cited LCA factors
python -m backend.app.seed.seed_data

# Start FastAPI server on port 8000
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Step 2: Frontend Setup (Next.js 16)

```powershell
cd frontend
npm install
npm run dev
```

- Web App: [http://localhost:3000](http://localhost:3000)

---

## 4. Running the Automated Test Suite

Run the full pytest suite (39 automated unit, integration, and E2E latency tests):

```powershell
python -m pytest backend/tests -v
```

**Test Coverage Highlights:**
- `test_e2e_pipeline.py`: Full end-to-end `/analyze` $\rightarrow$ `/recommend` $\rightarrow$ `/outcome/confirm` lifecycle flow + latency checks.
- `test_vision_models.py`: ResNet-18 inference, confidence gating (0.60 threshold), and stub fallbacks.
- `test_tag_pipeline.py`: Deskewing, CLAHE, fiber parsing, fuzzy brand aliases, and ~100% check.
- `test_decision_engine.py`: SQL rules, close-score transparent explanations, and SHAP attributions.

---

## 5. Walkthrough Demo: 3 Sample Garments

Follow these 3 representative scenarios in the web app ([http://localhost:3000](http://localhost:3000)) or via `curl`:

### Sample 1: Repair Pathway (Mendable Torn Seam)
- **Garment Profile:** Navy Cotton Chino Trousers.
- **Diagnostics:**
  - Material: `natural` (Cotton, confidence 0.88).
  - Condition: `gently_used` (confidence 0.82).
  - Damage: Detected, area = 4.2% (torn pocket seam, $< 20\%$ repair threshold).
  - Brand: Unknown / Local Tailored.
- **Decision Engine Output:**
  - **Top Pathway:** `repair` (Suitability Score $\sim 0.84$).
  - **Explanation:** *"Visible damage is limited to 4.2% of the garment, well within the 20% repairability threshold. The fabric condition is gently used, making professional mending the most resource-efficient choice."*
  - **Top SHAP Contributor:** `damage_percent: +0.28`, `condition: +0.20`.
  - **Nearest Partner:** FC Road Master Tailors & Alterations (0.8 km).
  - **LCA Impact Saved:** 3,120 Litres of Water · 9.4 kg $\text{CO}_2$ avoided.

### Sample 2: Reuse / Resell Pathway (Branded, Pristine Wear)
- **Garment Profile:** Levi's Denim Trucker Jacket.
- **Diagnostics:**
  - Material: `natural` (100% Cotton denim, confidence 0.94).
  - Condition: `new` / `gently_used` (confidence 0.91).
  - Damage: Intact (0% area, 0 boxes).
  - Tag OCR: Brand `"Levi's"`, Composition `{"cotton": 100.0}` (`agrees_with_vision: true`).
- **Decision Engine Output:**
  - **Top Pathway:** `reuse_resell` / `brand_takeback` (Suitability Score $\sim 0.92$).
  - **Explanation:** *"Garment is in excellent, undamaged condition with recognized brand value. Resale or brand trade-in delivers the highest circular utility and rewards the owner."*
  - **Top SHAP Contributor:** `condition: +0.35`, `brand: +0.25`, `damage_percent: 0.0`.
  - **Nearest Partner:** SwapStyle Pune Camp (1.4 km) or Levi's Pavillion Store.
  - **LCA Impact Saved:** 4,800 Litres of Water · 14.8 kg $\text{CO}_2$ avoided.

### Sample 3: Recycle Pathway (Unrepairable Synthetic Wear)
- **Garment Profile:** Heavily Worn Polyester Sports Jersey.
- **Diagnostics:**
  - Material: `synthetic` (Polyester, confidence 0.85).
  - Condition: `heavily_worn` (confidence 0.89).
  - Damage: Detected, area = 28.5% (large burn hole and shredding, exceeds repair limit).
  - Tag OCR: Unreadable / Cut.
- **Decision Engine Output:**
  - **Top Pathway:** `recycle` (Suitability Score $\sim 0.88$).
  - **Explanation:** *"Garment exhibits severe structural wear and 28.5% damage exceeding the repair threshold. Direct mechanical fiber shredding and chemical recycling prevents landfill disposal."*
  - **Top SHAP Contributor:** `damage_percent: +0.38`, `condition: -0.25`.
  - **Nearest Partner:** EcoReclaim Pune - FC Road (1.2 km).
  - **LCA Impact Saved:** 850 Litres of Water · 5.2 kg $\text{CO}_2$ avoided.

---

## 6. Testing the Partner QR Intake Loop

1. Complete any garment recommendation to generate a unique QR code (e.g., `qr_7f83a21b`).
2. Click the **Partner Scan** tab in the top navigation.
3. Select the drop-off facility (e.g. *EcoReclaim Pune - FC Road*).
4. Paste the QR ID and choose the confirmed physical outcome.
5. Click **Record Real Circular Outcome**.
6. The system records the verified transaction in the database and generates an official Circular Outcome Certificate.

---

## 7. Machine Learning Training Artifacts in `ml/`

Each neural model has a dedicated Google Colab training notebook:
- [`ml/train_damage_yolov8.ipynb`](file:///c:/ai project/rethread/ml/train_damage_yolov8.ipynb): YOLOv8 segmentation on Roboflow garment damage.
- [`ml/train_resnet18_classifier.ipynb`](file:///c:/ai project/rethread/ml/train_resnet18_classifier.ipynb): ResNet-18 with GroupShuffleSplit (preventing multi-angle garment data leakage) for condition and material.
- [`ml/train_tag_yolov8.ipynb`](file:///c:/ai project/rethread/ml/train_tag_yolov8.ipynb): Single-class YOLOv8 tag localization.
- [`backend/app/engine/xgb_ranker.py`](file:///c:/ai project/rethread/backend/app/engine/xgb_ranker.py): XGBoost multi-output ranker with SHAP TreeExplainer.

---

## 8. API Contract Summary (`POST /analyze` & `POST /recommend`)

All schemas strictly enforce the project contract:

```bash
# 1. Analyze Garment
curl -X POST http://127.0.0.1:8000/analyze \
  -F "garment_images=@garment_front.jpg" \
  -F "garment_images=@garment_texture.jpg" \
  -F "tag_image=@care_tag.jpg"

# 2. Recommend Pathways
curl -X POST http://127.0.0.1:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "analysis": { ... },
    "user_latitude": 18.5204,
    "user_longitude": 73.8567,
    "garment_weight_kg": 0.35
  }'

# 3. Confirm Lifecycle Outcome
curl -X POST http://127.0.0.1:8000/outcome/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "qr_id": "qr_4b7f92e10c",
    "partner_facility_id": 1,
    "confirmed_pathway": "reuse_resell",
    "notes": "Verified at drop-off center"
  }'
```
#   R e - T h r e a d  
 