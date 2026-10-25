# RE-THREAD: Circular Fashion Decision Platform

*AI-Powered Circular Garment Decision System · Computer Vision · OCR · XGBoost & SHAP Explainability · Lifecycle Tracking*

> **Tagline:** *"Your Clothes. Your Stories. Their Next Chapter."*  
> **Initiative:** PCCOE Pune · International Grand Challenge 2026 (AI for Climate Change)  
> **Repository:** [https://github.com/AvantikaPawar2008/Re-Thread](https://github.com/AvantikaPawar2008/Re-Thread)

---

## 1. Executive Summary & Architecture

**RE-THREAD** is an end-to-end circular fashion intelligence system engineered to divert post-consumer textiles from landfills (such as Pune's Urali Devachi depot) into verifiable circular lifecycles. Users capture photos of an unwanted garment and its care tag to trigger multi-modal visual diagnostics and hybrid decision ranking:

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

## 2. Core Features & Technology Stack

- **Multi-Modal Computer Vision**:
  - **Damage Detection**: Fine-tuned YOLOv8 segmentation for defects (tears, holes, stains) with bounding boxes and surface area percentage calculation.
  - **Condition & Material Classification**: Dual ResNet-18 classifiers using `GroupShuffleSplit` (garment-level splitting to prevent multi-angle data leakage).
  - **Grad-CAM Visual Heatmaps**: `pytorch-grad-cam` overlays on `layer4[-1]` highlighting fabric weave and wear focal points.
  - **Care Tag OCR & Parsing**: YOLOv8 tag localization, OpenCV deskewing & CLAHE binarization, PaddleOCR line extraction, RapidFuzz brand alias matching, and $\sim 100\%$ fiber percentage validation.
- **Hybrid Decision Engine**:
  - **Layer A**: Deterministic SQL business rules (brand eligibility, damage repair limits, material recyclability).
  - **Layer B**: Pluggable Ranker interface (`WeightedFormulaRanker` and `XGBoostRanker`) with real `shap.TreeExplainer` feature attribution.
  - **Layer C**: Haversine geographical distance ranking across 15 Pune partner facilities and cited WRAP/Ellen MacArthur Foundation LCA impact factors (water litres and $\text{CO}_2$ kg saved).
- **Frontend & Verification Loop**:
  - **Next.js 16 (React 19, Tailwind CSS 4, TypeScript)**: Mobile-first interface with photo uploads, AI diagnosis cards, interactive Grad-CAM heatmap inspection, ranked pathways, QR code passport, Pune municipal ward dashboard, and partner intake scanner.

---

## 3. Quickstart: Local Setup & Running

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### Step 1: Backend Setup

```powershell
# Navigate to the repository root
cd "c:\ai project\rethread"

# Install Python backend dependencies
pip install -r backend/requirements.txt

# Seed the SQLite database with 15 Pune facilities, 8 brand policies, and LCA factors
python -m backend.app.seed.seed_data

# Start the FastAPI server (Port 8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Probe:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Step 2: Frontend Setup

```powershell
# In a new terminal window
cd "c:\ai project\rethread\frontend"

# Install frontend dependencies
npm install

# Start the Next.js development server (Port 3000)
npm run dev
```

- **Web Application:** [http://localhost:3000](http://localhost:3000)

---

## 4. Automated Test Suite

Run the full pytest suite (39 automated unit, integration, and E2E latency tests):

```powershell
python -m pytest backend/tests -v
```

All 39 tests validate:
- **E2E Lifecycle Flow**: `/analyze` $\rightarrow$ `/recommend` $\rightarrow$ `/outcome/confirm`.
- **Latency Performance**: `/health` $< 100\text{ms}$ and `/recommend` $< 350\text{ms}$.
- **Vision & Tag Models**: YOLOv8 fallback, ResNet-18 confidence threshold gating ($0.60$), and OCR fiber parsing.
- **Decision Engine**: Layer A SQL rules, close-score transparency, and SHAP tree explainability.

---

## 5. Walkthrough Demo: 3 Sample Garments

Test these 3 representative circular pathways in the UI ([http://localhost:3000](http://localhost:3000)) or via API:

### Sample 1: Repair Pathway (Mendable Torn Seam)
- **Garment Profile:** Navy Cotton Chino Trousers.
- **Diagnostics:**
  - Material: `natural` (Cotton, confidence 0.88).
  - Condition: `gently_used` (confidence 0.82).
  - Damage: Detected, area = 4.2% (torn pocket seam, $< 20\%$ repair threshold).
  - Brand: Unknown / Local Tailored.
- **Decision Engine Recommendation:**
  - **Top Pathway:** `repair` (Suitability Score $\sim 0.84$).
  - **Explanation:** *"Visible damage is limited to 4.2% of the garment, well within the 20% repairability threshold. Fabric condition is gently used, making mending the most resource-efficient choice."*
  - **Top SHAP Contributor:** `damage_percent: +0.28`, `condition: +0.20`.
  - **Nearest Partner:** FC Road Master Tailors & Alterations ($0.8\text{ km}$).
  - **Impact Saved:** 3,120 Litres of Water · 9.4 kg $\text{CO}_2$ avoided.

### Sample 2: Reuse / Resell Pathway (Branded, Pristine Wear)
- **Garment Profile:** Levi's Denim Trucker Jacket.
- **Diagnostics:**
  - Material: `natural` (100% Cotton denim, confidence 0.94).
  - Condition: `new` / `gently_used` (confidence 0.91).
  - Damage: Intact (0% area, 0 boxes).
  - Tag OCR: Brand `"Levi's"`, Composition `{"cotton": 100.0}` (`agrees_with_vision: true`).
- **Decision Engine Recommendation:**
  - **Top Pathway:** `reuse_resell` / `brand_takeback` (Suitability Score $\sim 0.92$).
  - **Explanation:** *"Garment is in excellent, undamaged condition with recognized brand value. Resale or brand trade-in delivers the highest circular utility and rewards the owner."*
  - **Top SHAP Contributor:** `condition: +0.35`, `brand: +0.25`, `damage_percent: 0.0`.
  - **Nearest Partner:** SwapStyle Pune Camp ($1.4\text{ km}$) or Levi's Pavillion Store.
  - **Impact Saved:** 4,800 Litres of Water · 14.8 kg $\text{CO}_2$ avoided.

### Sample 3: Recycle Pathway (Unrepairable Synthetic Wear)
- **Garment Profile:** Heavily Worn Polyester Sports Jersey.
- **Diagnostics:**
  - Material: `synthetic` (Polyester, confidence 0.85).
  - Condition: `heavily_worn` (confidence 0.89).
  - Damage: Detected, area = 28.5% (large burn hole and shredding, exceeds repair limit).
  - Tag OCR: Unreadable / Missing.
- **Decision Engine Recommendation:**
  - **Top Pathway:** `recycle` (Suitability Score $\sim 0.88$).
  - **Explanation:** *"Garment exhibits severe structural wear and 28.5% damage exceeding the repair threshold. Mechanical fiber recovery prevents landfill disposal."*
  - **Top SHAP Contributor:** `damage_percent: +0.38`, `condition: -0.25`.
  - **Nearest Partner:** EcoReclaim Pune - FC Road ($1.2\text{ km}$).
  - **Impact Saved:** 850 Litres of Water · 5.2 kg $\text{CO}_2$ avoided.

---

## 6. Testing the Partner QR Intake Loop

1. Run an analysis on any garment to generate a unique QR code passport (e.g. `qr_7f83a21b`).
2. Click the **Partner Scan** tab in the navigation bar.
3. Select an authorized facility (e.g. *EcoReclaim Pune - FC Road*).
4. Enter or paste the QR ID and choose the confirmed physical pathway.
5. Click **Record Real Circular Outcome**.
6. The system commits the transaction to the database and generates a verified circular outcome certificate.

---

## 7. Machine Learning Training Notebooks in `ml/`

Self-contained Google Colab training notebooks for all models:
- [`ml/train_damage_yolov8.ipynb`](file:///c:/ai project/rethread/ml/train_damage_yolov8.ipynb): YOLOv8 segmentation on Roboflow garment damage datasets.
- [`ml/train_resnet18_classifier.ipynb`](file:///c:/ai project/rethread/ml/train_resnet18_classifier.ipynb): ResNet-18 with GroupShuffleSplit for condition and material classification.
- [`ml/train_tag_yolov8.ipynb`](file:///c:/ai project/rethread/ml/train_tag_yolov8.ipynb): Single-class YOLOv8 care tag localization.
- [`backend/app/engine/xgb_ranker.py`](file:///c:/ai project/rethread/backend/app/engine/xgb_ranker.py): XGBoost multi-output regressor with real SHAP TreeExplainer attributions.

---

## 8. API Contract Examples

```bash
# 1. Analyze Garment Photos & Care Tag
curl -X POST http://127.0.0.1:8000/analyze \
  -F "garment_images=@garment_front.jpg" \
  -F "garment_images=@garment_texture.jpg" \
  -F "tag_image=@care_tag.jpg"

# 2. Generate Ranked Circular Recommendations
curl -X POST http://127.0.0.1:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "analysis": { ... },
    "user_latitude": 18.5204,
    "user_longitude": 73.8567,
    "garment_weight_kg": 0.35
  }'

# 3. Confirm Lifecycle Outcome at Partner Drop-off
curl -X POST http://127.0.0.1:8000/outcome/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "qr_id": "qr_4b7f92e10c",
    "partner_facility_id": 1,
    "confirmed_pathway": "reuse_resell",
    "notes": "Drop-off intake inspection confirmed"
  }'
```

---

## 9. License & Attribution

Developed for the **International Grand Challenge 2026** (Theme: AI for Climate Change) at **Pimpri Chinchwad College of Engineering (PCCOE), Pune**.  
Mentor: **Harsha Talele** · Team: **Circular Transformation**.