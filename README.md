# RE-THREAD: Circular Fashion Decision Platform

*AI-Powered Circular Garment Decision System · Computer Vision · OCR · XGBoost & SHAP Explainability · Lifecycle Tracking*

> **Tagline:** *"Your Clothes. Your Stories. Their Next Chapter."*  
> **Repository:** [https://github.com/AvantikaPawar2008/Re-Thread](https://github.com/AvantikaPawar2008/Re-Thread)

---

## 1. Executive Summary & Problem Statement

The fashion and textile industry is one of the world's most resource-intensive sectors, responsible for over 10% of global carbon emissions and 20% of industrial wastewater. Globally, millions of tonnes of post-consumer garments are discarded into landfills every year because consumers lack accessible, transparent guidance on how to circularize their clothing.

**RE-THREAD** is an end-to-end, AI-powered circular fashion intelligence platform designed to divert post-consumer textiles from landfills into their highest-value circular pathways:

1. **Reuse / Resell**: High-condition, branded, or lightly worn garments routed to thrift platforms and second-hand marketplaces.
2. **Repair & Mending**: Garments with repairable defects ($< 20\%$ surface area damage) routed to local tailoring and alteration services.
3. **Community Donation**: Clean, wearable everyday clothing routed to verified charitable shelters and clothing banks.
4. **Fiber Recycling**: Unrepairable or heavily worn textiles directed to mechanical fiber-shredding and chemical recycling facilities.
5. **Brand Take-Back**: Garments from partner brands (e.g., H&M, Levi's, Zara, Decathlon) directed to in-store circular trade-in kiosks in exchange for vouchers.

---

## 2. Core Architectural Principles

1. **Frozen API Contract**: The API schemas between the Next.js frontend and FastAPI backend are strictly defined and validated with Pydantic V2.
2. **Honest Optical AI Limits**: Consumer smartphone RGB cameras cannot reliably resolve fine blend ratios (e.g. 60/40 vs 80/20 cotton-poly). The system classifies coarse fabric families (*natural*, *synthetic*, *blend*, or *uncertain*) and treats tag OCR as an optional secondary confirmation.
3. **Confidence Threshold Gating**: If visual prediction confidence falls below the calibrated threshold ($0.60$), the model returns `"uncertain"` rather than hallucinating.
4. **Hybrid Decision Engine**: Hard deterministic business rules always execute first (Layer A), followed by scoring and ranking (Layer B), and geographical routing with LCA impact calculations (Layer C).
5. **Startup Model Loading**: All heavy neural networks (YOLOv8, ResNet-18, XGBoost) load once into memory at application startup via a singleton registry.
6. **Graceful Degradation**: If an image is blurry, a tag is missing, or machine learning model weights are absent, the platform never crashes—it gracefully degrades to typed fallbacks.
7. **Verified Physical Verification Loop**: AI recommendations represent user intention; only when a physical drop-off partner scans the unique **QR Passport** does the transaction count as verified environmental data.
8. **Localized Drop-off Infrastructure**: Pre-configured with a localized drop-off network of 15 verified facilities across municipal zones.

---

## 3. System Architecture & Information Flow

```
[Garment & Care Tag Photos]
             │
             ├──► YOLOv8 Damage Segmentation (Detects defect boxes & calculates % damaged area)
             ├──► ResNet-18 Material Classifier (Natural / Synthetic / Blend / Uncertain) ──► Grad-CAM Heatmap
             ├──► ResNet-18 Wear Classifier (New / Gently Used / Worn / Heavily Worn)   ──► Grad-CAM Heatmap
             └──► Care Tag OCR Pipeline (YOLOv8 crop ──► OpenCV CLAHE/Deskew ──► PaddleOCR ──► RapidFuzz + Vocab)
             │
      [POST /analyze]
             ▼
     [Analysis Profile]
             │
      [POST /recommend]
             ▼
[Hybrid Circular Decision Engine]
  ├── Layer A (SQL Rules): Evaluates eligibility (Brand take-back, repair threshold, facility recyclability)
  ├── Layer B (Ranker): XGBoost multi-output model + real shap.TreeExplainer feature attributions
  ├── Layer C (Geo & LCA): Haversine distance to drop-off hubs + Cited WRAP/EMF LCA water & CO2 factors
  └── Explainability: Plain-language generator + Cryptographic QR Lifecycle Passport
             │
      [POST /outcome/confirm]
             ▼
[Partner Drop-Off Portal] ──► Confirms real physical intake, logs DB record, and issues verification certificate
```

---

## 4. Platform Capabilities & Implemented Modules

| Module | Component | Description |
| :--- | :--- | :--- |
| **Backend & Database** | FastAPI + SQLAlchemy | RESTful endpoints (`/health`, `/analyze`, `/recommend`, `/outcome/confirm`), SQLite/PostgreSQL support, Alembic schema migrations, and seeded drop-off facilities. |
| **Frontend Web App** | Next.js 16 (React 19) | Mobile-first upload interface (3 garment photo slots + 1 tag slot), AI diagnosis cards, confidence score meters, uncertain state banners, interactive maps, and impact analytics. |
| **Damage Segmentation** | YOLOv8-seg | Neural defect detection identifying tears, holes, and stains with precise bounding boxes and garment surface area percentage calculations. |
| **Wear & Fabric Classifiers** | Dual ResNet-18 | Wear classification (*new*, *gently_used*, *worn*, *heavily_worn*) and fabric family identification (*natural*, *synthetic*, *blend*) trained with garment-level grouping to prevent multi-angle data leakage. |
| **Visual Explainability** | PyTorch Grad-CAM | Convolutional activation heatmaps (`layer4[-1]`) superimposed over garment photos and rendered in the UI to explain what visual textures guided the model's prediction. |
| **Care Tag Pipeline** | YOLOv8 + OpenCV + OCR | Tag localization, minimum-area-rectangle deskewing, CLAHE contrast enhancement, Otsu binarization, PaddleOCR line extraction, RapidFuzz brand alias matching, and 10-fiber vocabulary validation. |
| **Decision Engine** | Layered Hybrid Ranker | Layer A SQL constraints, Layer B pluggable Ranker interface (`WeightedFormulaRanker` and `XGBoostRanker`) with real `shap.TreeExplainer` feature attribution, and Layer C Haversine geo-routing. |
| **Lifecycle Verification** | QR Intake Portal | Generates cryptographic QR tracking passports and provides a partner-facing scan portal to confirm physical drop-offs and certify real-world circular outcomes. |

---

## 5. Technology Stack

### Backend & Machine Learning
- **Framework**: FastAPI (Python 3.11/3.12), Pydantic V2, Uvicorn (ASGI)
- **Database & ORM**: SQLite (zero-config local dev) / PostgreSQL 16 via SQLAlchemy 2.0 & Alembic
- **Deep Learning**: PyTorch 2.x, Torchvision, Ultralytics YOLOv8 (segmentation & detection)
- **Visual Explainability**: `pytorch-grad-cam` (Grad-CAM on ResNet-18 `layer4[-1]`)
- **Ranking & Attribution**: XGBoost Regressor, SHAP (`shap.TreeExplainer`)
- **Computer Vision & OCR**: OpenCV (CLAHE, minAreaRect deskew, Otsu), Pillow, PaddleOCR, RapidFuzz
- **Testing**: Pytest, Pytest-Asyncio, HTTPX TestClient (39 automated tests)

### Frontend
- **Framework**: Next.js 16 (React 19, Turbopack, App Router)
- **Styling**: Tailwind CSS 4, Lucide React Icons
- **Language**: TypeScript (strict mode, zero build errors)

---

## 6. Repository Layout

```text
re-thread/
├── docs/
│   └── PROJECT.md                  # Comprehensive project specification
├── frontend/                       # Next.js 16 web application
│   ├── src/
│   │   ├── app/                    # App Router pages (Home, layout, styles)
│   │   ├── components/             # Reusable UI modules:
│   │   │   ├── Navbar.tsx            # Header with status indicator and navigation tabs
│   │   │   ├── UploadSection.tsx     # 3 garment photo slots + 1 care tag slot
│   │   │   ├── AnalysisResultsSection.tsx # AI diagnosis cards with Grad-CAM toggles
│   │   │   ├── RecommendationsSection.tsx # Ranked circular pathways & QR passport
│   │   │   ├── PartnerScanPage.tsx   # Drop-off partner QR scanner & intake form
│   │   │   ├── ImpactDashboard.tsx   # Municipal ward impact metrics
│   │   │   └── FacilitiesView.tsx    # Interactive drop-off facility directory
│   │   ├── lib/api.ts              # Type-safe API client
│   │   └── types/index.ts          # TypeScript interfaces matching API schemas
│   ├── package.json
│   └── tsconfig.json
├── backend/
│   ├── alembic/                    # Database migration scripts
│   ├── app/
│   │   ├── main.py                 # FastAPI application, lifespan handler & latency middleware
│   │   ├── config.py               # Pydantic BaseSettings & environment variables
│   │   ├── db.py                   # SQLAlchemy engine and session dependency
│   │   ├── models_db.py            # ORM models (Brand, Facility, PathwayRule, ImpactFactor, Recommendation, Outcome)
│   │   ├── schemas.py              # Pydantic contract schemas
│   │   ├── api/                    # API endpoints:
│   │   │   ├── analyze.py            # POST /analyze (multipart upload & CV pipeline)
│   │   │   ├── recommend.py          # POST /recommend (hybrid decision engine)
│   │   │   └── outcome.py            # POST /outcome/confirm (partner intake loop)
│   │   ├── ml/                     # Machine learning inference modules:
│   │   │   ├── loader.py             # Startup singleton model manager
│   │   │   ├── damage.py             # YOLOv8 defect segmentation
│   │   │   ├── condition.py          # ResNet-18 wear classifier with Grad-CAM
│   │   │   ├── material.py           # ResNet-18 coarse fabric classifier with Grad-CAM
│   │   │   ├── gradcam.py            # PyTorch Grad-CAM heatmap generator
│   │   │   └── tag/                  # Care tag sub-pipeline:
│   │   │       ├── detect.py           # YOLOv8 tag detector & cropper
│   │   │       ├── clean.py            # OpenCV deskew, CLAHE & binarization
│   │   │       ├── ocr.py              # PaddleOCR wrapper
│   │   │       └── parse.py            # RapidFuzz brand matching & fiber vocab parser
│   │   ├── engine/                 # Circular decision engine:
│   │   │   ├── rules.py              # Layer A: Hard SQL eligibility constraints
│   │   │   ├── ranking.py            # Layer B: Ranker interface & dispatch
│   │   │   ├── xgb_ranker.py         # Layer B: XGBoost ranker with real SHAP TreeExplainer
│   │   │   ├── geography.py          # Layer C: Haversine distance calculator
│   │   │   ├── impact.py             # Layer C: Cited WRAP/EMF LCA savings calculator
│   │   │   ├── explanation.py        # Plain-language natural explanation generator
│   │   │   └── qr.py                 # Cryptographic QR code image generator
│   │   └── seed/                   # Seed data:
│   │       ├── brands.csv            # 8 brands with take-back policies
│   │       ├── facilities.csv        # 15 regional municipal facilities
│   │       ├── impact_factors.csv    # Cited LCA water/CO2 factors
│   │       ├── rules.csv             # 5 pathway rules
│   │       └── seed_data.py          # Seed loader script
│   ├── tests/                      # Automated pytest suite (39 tests):
│   │   ├── conftest.py               # Shared in-memory test database fixture
│   │   ├── test_health.py            # Health probe tests
│   │   ├── test_analyze.py           # Multipart upload tests
│   │   ├── test_recommend.py         # Recommendation endpoint tests
│   │   ├── test_outcome.py           # QR intake confirmation tests
│   │   ├── test_decision_engine.py   # SQL rules, rankings, and edge cases
│   │   ├── test_damage.py            # Damage detection tests
│   │   ├── test_vision_models.py     # ResNet-18 wear/material tests
│   │   ├── test_tag_pipeline.py      # Deskew, OCR, fiber vocab, and brand tests
│   │   ├── test_e2e_pipeline.py      # End-to-end lifecycle & latency checks
│   │   └── test_db_and_seed.py       # Seed data validation
│   └── requirements.txt            # Python dependencies
├── ml/                             # Training Scripts & Notebooks:
│   ├── train_damage_yolov8.ipynb   # YOLOv8 segmentation training
│   ├── train_resnet18_classifier.ipynb # ResNet-18 with GroupShuffleSplit
│   └── train_tag_yolov8.ipynb      # YOLOv8 care tag detection training
├── weights/                        # Model weights directory (damage.pt, condition.pt, etc.)
├── docker-compose.yml              # Optional PostgreSQL container configuration
└── README.md                       # Main project documentation
```

---

## 7. Quickstart Guide: Local Setup & Running

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### Step 1: Set Up and Run the Backend

```powershell
# Navigate to the project root
cd "c:\ai project\rethread"

# Install backend dependencies
pip install -r backend/requirements.txt

# Seed the database with drop-off facilities, brands, and LCA impact factors
python -m backend.app.seed.seed_data

# Start the FastAPI server (Port 8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive API Documentation (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Step 2: Set Up and Run the Frontend

```powershell
# In a separate terminal window:
cd "c:\ai project\rethread\frontend"

# Install frontend dependencies
npm install

# Start the Next.js development server (Port 3000)
npm run dev
```

- **Web Application:** [http://localhost:3000](http://localhost:3000)

---

## 8. Running the Automated Test Suite

Run the full pytest suite across all 39 tests:

```powershell
python -m pytest backend/tests -v
```

**Test Coverage Summary:**
- **`test_e2e_pipeline.py`**: Full lifecycle flow from multipart photo upload $\rightarrow$ `/analyze` $\rightarrow$ `/recommend` $\rightarrow$ `/outcome/confirm`, latency checks ($< 100\text{ms}$ health, $< 350\text{ms}$ recommendation), and Ranker interface validation.
- **`test_vision_models.py`**: Validates ResNet-18 condition and coarse material inference, confidence threshold gating ($0.60$), and stub fallbacks.
- **`test_damage.py`**: Validates YOLOv8 defect detection, surface area percentage calculation, and bounding boxes.
- **`test_tag_pipeline.py`**: Validates image deskewing, CLAHE binarization, regex fiber extraction against fixed vocabulary, RapidFuzz brand matching with aliases, $\sim 100\%$ check, and vision cross-check.
- **`test_decision_engine.py`**: Validates Layer A SQL rules, distance weighting, cited LCA savings, close-score transparent explanations, and SHAP feature attributions.

---

## 9. Walkthrough Demo: 3 Sample Garments

You can test these 3 scenarios directly in the web app ([http://localhost:3000](http://localhost:3000)) or via `curl`:

### Sample 1: Repair Pathway (Mendable Torn Seam)
- **Garment Profile:** Navy Cotton Chino Trousers.
- **Diagnostic Findings:**
  - Material: `natural` (Cotton, confidence 0.88).
  - Condition: `gently_used` (confidence 0.82).
  - Damage: Detected, area = 4.2% (torn pocket seam, well below 20% limit).
  - Brand: Tailored / Unbranded.
- **Decision Engine Output:**
  - **Top Recommended Pathway:** `repair` (Suitability Score: 0.84).
  - **Plain-Language Explanation:** *"Visible damage is limited to 4.2% of the garment, well within the 20% repairability threshold. The fabric condition is gently used, making professional mending the most resource-efficient choice."*
  - **SHAP Feature Attributions:** `damage_percent: +0.28`, `condition: +0.20`, `material: +0.12`.
  - **Nearest Partner:** FC Road Master Tailors & Alterations ($0.8\text{ km}$ away).
  - **LCA Environmental Savings:** 3,120 Litres of Water · 9.4 kg $\text{CO}_2$ avoided.

### Sample 2: Reuse / Resell Pathway (Branded, Pristine Garment)
- **Garment Profile:** Levi's Denim Trucker Jacket.
- **Diagnostic Findings:**
  - Material: `natural` (100% Cotton denim, confidence 0.94).
  - Condition: `new` / `gently_used` (confidence 0.91).
  - Damage: None detected (0% area).
  - Tag OCR: Brand `"Levi's"`, Composition `{"cotton": 100.0}` (`agrees_with_vision: true`).
- **Decision Engine Output:**
  - **Top Recommended Pathway:** `reuse_resell` / `brand_takeback` (Suitability Score: 0.92).
  - **Plain-Language Explanation:** *"Garment is in excellent, undamaged condition with recognized brand value. Resale or brand trade-in delivers the highest circular utility and rewards the owner."*
  - **SHAP Feature Attributions:** `condition: +0.35`, `brand: +0.25`, `damage_percent: 0.0`.
  - **Nearest Partner:** SwapStyle Pune Camp ($1.4\text{ km}$) or Levi's Pavillion Store.
  - **LCA Environmental Savings:** 4,800 Litres of Water · 14.8 kg $\text{CO}_2$ avoided.

### Sample 3: Recycle Pathway (Unrepairable Synthetic Wear)
- **Garment Profile:** Heavily Worn Polyester Sports Jersey.
- **Diagnostic Findings:**
  - Material: `synthetic` (Polyester, confidence 0.85).
  - Condition: `heavily_worn` (confidence 0.89).
  - Damage: Detected, area = 28.5% (large burn hole and shredding, exceeds repair limit).
  - Tag OCR: Unreadable / Cut.
- **Decision Engine Output:**
  - **Top Recommended Pathway:** `recycle` (Suitability Score: 0.88).
  - **Plain-Language Explanation:** *"Garment exhibits severe structural wear and 28.5% damage exceeding the repair threshold. Direct mechanical fiber shredding and chemical recycling prevents landfill disposal."*
  - **SHAP Feature Attributions:** `damage_percent: +0.38`, `condition: -0.25`.
  - **Nearest Partner:** EcoReclaim Pune - FC Road ($1.2\text{ km}$).
  - **LCA Environmental Savings:** 850 Litres of Water · 5.2 kg $\text{CO}_2$ avoided.

---

## 10. Partner QR Intake & Outcome Verification Loop

1. Complete a recommendation in the web app to generate the circular QR passport (e.g. `qr_4b7f92e10c`).
2. Navigate to the **Partner Scan** tab in the top navigation.
3. Select an intake facility from the regional partner locations.
4. Enter or simulate-scan the QR ID and select the verified physical outcome (`reuse_resell`, `repair`, `donate`, `recycle`, or `brand_takeback`).
5. Click **Record Real Circular Outcome**.
6. The system commits the transaction to the database via `POST /outcome/confirm` and issues an official Circular Verification Certificate.

---

## 11. API Contract Examples

### 1. Analyze Garment
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "garment_images=@garment_front.jpg" \
  -F "garment_images=@garment_texture.jpg" \
  -F "tag_image=@care_tag.jpg"
```

### 2. Generate Recommendations
```bash
curl -X POST http://127.0.0.1:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "analysis": {
      "material": {"label": "natural", "confidence": 0.88},
      "condition": {"label": "gently_used", "confidence": 0.82},
      "damage": {"detected": true, "area_percent": 4.2, "boxes": []},
      "tag": {"brand": "Levi'\''s", "composition": {"cotton": 100.0}, "ocr_confidence": 0.92, "agrees_with_vision": true},
      "composition_status": "confident"
    },
    "user_latitude": 18.5204,
    "user_longitude": 73.8567,
    "garment_weight_kg": 0.35
  }'
```

### 3. Confirm Lifecycle Outcome
```bash
curl -X POST http://127.0.0.1:8000/outcome/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "qr_id": "qr_4b7f92e10c",
    "partner_facility_id": 1,
    "confirmed_pathway": "repair",
    "notes": "Seam mending completed at FC Road hub"
  }'
```

---

## 12. Verified Drop-off Network Directory

The platform includes 15 calibrated drop-off locations:

| ID | Facility Name | Neighborhood | Coordinates | Supported Pathways |
| :-: | :--- | :--- | :-: | :--- |
| **1** | EcoReclaim Pune - FC Road | Shivajinagar | 18.5204, 73.8415 | Recycle, Brand Take-Back |
| **2** | Rethread Hub Kothrud | Kothrud Depot | 18.5074, 73.8077 | Reuse/Resell, Repair, Donate |
| **3** | SwapStyle Pune Camp | MG Road, Camp | 18.5158, 73.8786 | Reuse/Resell, Donate |
| **4** | Deccan Fabric Upcyclers | Deccan Gymkhana | 18.5167, 73.8417 | Repair, Upcycling |
| **5** | Viman Nagar Textile Bank | Viman Nagar | 18.5679, 73.9143 | Donate, Reuse |
| **6** | Hadapsar Circular Mending | Hadapsar | 18.5089, 73.9259 | Repair, Tailoring |
| **7** | PCMC Green Threads Pimpri | Pimpri-Chinchwad | 18.6298, 73.7997 | Recycle, Donate |
| **8** | Aundh Eco-Stitch Collective | Aundh | 18.5580, 73.8074 | Repair, Upcycling |
| **9** | Baner Zero-Waste Closet | Baner | 18.5590, 73.7868 | Reuse/Resell, Donate |
| **10** | Swargate Community Closet | Swargate | 18.5018, 73.8586 | Donate |
| **11** | Koregaon Park Vintage Exchange | Koregaon Park | 18.5362, 73.8940 | Reuse/Resell |
| **12** | Katraj Fiber Recovery Hub | Katraj | 18.4575, 73.8677 | Recycle |
| **13** | Hinjawadi IT Eco-Drop | Hinjawadi Phase 1 | 18.5913, 73.7389 | Donate, Brand Take-Back |
| **14** | Magarpatta Circular Station | Magarpatta City | 18.5143, 73.9317 | Reuse, Repair |
| **15** | Pune Station Care & Repair | Railway Station | 18.5284, 73.8744 | Repair, Alterations |

---

## 13. License

This project is licensed under the MIT License - see the LICENSE file for details.