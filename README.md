# RE-THREAD: Circular Fashion Decision Platform

*AI-Powered Circular Garment Decision System · Computer Vision · OCR · XGBoost & SHAP Explainability · Lifecycle Tracking*

> **Tagline:** *"Your Clothes. Your Stories. Their Next Chapter."*  
> **Repository:** [https://github.com/AvantikaPawar2008/Re-Thread](https://github.com/AvantikaPawar2008/Re-Thread)

---

## 1. Project Overview & Problem Statement

The fashion and textile industry is one of the world's most resource-intensive sectors, responsible for over 10% of global carbon emissions and 20% of industrial wastewater. Millions of tonnes of post-consumer garments are discarded into landfills annually because consumers lack accessible, transparent guidance on how to circularize their clothing.

**RE-THREAD** is an end-to-end circular fashion intelligence platform designed to divert post-consumer garments from landfills into their highest-value circular pathways:

1. **Reuse / Resell**: High-condition, branded, or lightly worn garments routed to thrift platforms and second-hand marketplaces.
2. **Repair & Mending**: Garments with repairable defects ($< 20\%$ surface area damage) routed to local tailoring and alteration services.
3. **Community Donation**: Clean, wearable everyday clothing routed to verified charitable shelters and clothing banks.
4. **Fiber Recycling**: Unrepairable or heavily worn textiles directed to mechanical fiber-shredding and chemical recycling facilities.
5. **Brand Take-Back**: Garments from partner brands (e.g., H&M, Levi's, Zara, Decathlon) directed to in-store circular trade-in kiosks in exchange for vouchers.

---

## 2. Core Architectural Principles

1. **Frozen API Contract**: The API schemas between the Next.js frontend and FastAPI backend are strictly defined and validated with Pydantic V2.
2. **Honest Optical AI Limits**: Consumer smartphone RGB cameras cannot reliably resolve fine blend ratios (e.g. 60/40 vs 80/20 cotton-poly). The system classifies coarse fabric families (*natural*, *synthetic*, *blend*, or *uncertain*) and treats tag OCR as an optional secondary confirmation.
3. **Pluggable Perception Hierarchy**: Perception supports multimodal Vision-Language Models (Google Gemini / OpenAI) for comprehensive zero-shot visual diagnosis. Dedicated local models (fine-tuned YOLOv8 and ResNet-18) take precedence when `.pt` weights exist on disk (`weights/`), falling back to VLM if `VLM_API_KEY` is set, and finally to typed stubs.
4. **Confidence Threshold Gating**: If visual prediction confidence falls below the calibrated threshold ($0.60$), the model returns `"uncertain"` rather than hallucinating.
5. **Hybrid Decision Engine**: Hard deterministic business rules always execute first (Layer A), followed by scoring and ranking (Layer B), and geographical routing with LCA impact calculations (Layer C).
6. **Startup Model Loading**: All heavy neural networks and VLM clients initialize once into memory at application startup via a singleton `ModelRegistry`.
7. **Graceful Degradation**: If an image is blurry, a tag is missing, or network requests time out, the platform never crashes—it gracefully degrades to typed fallbacks.
8. **Verified Physical Verification Loop**: AI recommendations represent user intention; only when a physical drop-off partner scans the unique **QR Passport** does the transaction count as verified environmental data.
9. **Localized Drop-off Infrastructure**: Pre-configured with a localized drop-off network of 15 verified facilities across municipal zones.

---

## 3. System Architecture & Information Flow

```
[Garment & Care Tag Photos]
             │
     [Perception Router]
             ├─► 1. Local Models (when weights/*.pt exist on disk)
             │      ├── YOLOv8 Defect Segmentation + YOLOv8 Tag Detection
             │      ├── ResNet-18 Material & Condition Classifiers + Grad-CAM Heatmaps
             │      └── OpenCV Deskew + PaddleOCR + RapidFuzz
             │
             ├─► 2. VLM Perception API (Active when VLM_API_KEY is configured in .env)
             │      ├── Single multimodal call (Google Gemini / OpenAI)
             │      ├── Strict Pydantic JSON validation + 1-attempt retry + 35s timeout
             │      ├── Material, condition, damage area %, defect boxes & tag composition
             │      └── One-sentence visual reasoning explanations returned to frontend
             │
             └─► 3. Typed Stub Fallback (Deterministic, safe demonstration mode)
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
| **Backend & Database** | FastAPI + SQLAlchemy | RESTful endpoints (`/health`, `/health/models`, `/analyze`, `/recommend`, `/outcome/confirm`), SQLite/PostgreSQL support, Alembic schema migrations, and seeded drop-off facilities. |
| **Frontend Web App** | Next.js 16 (React 19) | Mobile-first upload interface (3 garment photo slots + 1 tag slot), AI diagnosis cards, confidence score meters, uncertain state banners, interactive maps, and impact analytics. |
| **Damage Segmentation** | YOLOv8-seg | Neural defect detection identifying tears, holes, and stains with bounding boxes and garment surface area percentage calculations. |
| **Wear & Fabric Classifiers** | Dual ResNet-18 | Wear classification (*new*, *gently_used*, *worn*, *heavily_worn*) and fabric family identification (*natural*, *synthetic*, *blend*) trained with garment-level grouping to prevent multi-angle data leakage. |
| **Visual Explainability** | PyTorch Grad-CAM & SHAP | Grad-CAM convolutional heatmaps (`layer4[-1]`) for visual attention, and real `shap.TreeExplainer` feature attribution on XGBoost ranking decisions. |
| **Care Tag Pipeline** | YOLOv8 + OpenCV + OCR | Tag localization, minimum-area-rectangle deskewing, CLAHE contrast enhancement, Otsu binarization, PaddleOCR line extraction, RapidFuzz brand matching, and fiber vocabulary validation. |
| **Decision Engine** | Layered Hybrid Ranker | Layer A SQL constraints, Layer B pluggable Ranker interface (`WeightedFormulaRanker` and `XGBoostRanker`), and Layer C Haversine geo-routing with cited WRAP/EMF LCA factors. |
| **Lifecycle Verification** | QR Intake Portal | Generates cryptographic QR tracking passports and provides a partner-facing scan portal to confirm physical drop-offs and certify real-world circular outcomes. |

---

## 5. Technology Stack

### Backend & Machine Learning
- **Framework**: FastAPI (Python 3.11/3.12), Pydantic V2, Uvicorn (ASGI)
- **Database & ORM**: SQLite (zero-config local dev) / PostgreSQL 16 via SQLAlchemy 2.0 & Alembic
- **Deep Learning**: PyTorch 2.x, Torchvision, Ultralytics YOLOv8 (segmentation & detection)
- **Visual Explainability**: `pytorch-grad-cam` (Grad-CAM on ResNet-18 `layer4[-1]`), SHAP (`shap.TreeExplainer`)
- **Ranking & Analytics**: XGBoost Regressor, Scikit-learn
- **Computer Vision & OCR**: OpenCV (CLAHE, minAreaRect deskew, Otsu), Pillow, PaddleOCR, RapidFuzz
- **Multimodal VLM**: Google Gemini API (`gemini-3-flash-preview` / `gemini-3.6-flash`), OpenAI API (`gpt-4o`)
- **Testing**: Pytest, Pytest-Asyncio, HTTPX TestClient

### Frontend
- **Framework**: Next.js 16 (React 19, Turbopack, App Router)
- **Styling**: Tailwind CSS 4, Lucide React Icons
- **Language**: TypeScript (strict mode)

---

## 6. Repository Layout

```
rethread/
├── backend/                        # FastAPI Application:
│   ├── alembic/                    # Database migrations
│   ├── app/
│   │   ├── api/                    # API Endpoints:
│   │   │   ├── analyze.py            # POST /analyze (Vision & Tag pipeline)
│   │   │   ├── recommend.py          # POST /recommend (Decision Engine)
│   │   │   └── outcome.py            # POST /outcome/confirm (Intake verification)
│   │   ├── config.py               # Pydantic Settings (.env configuration)
│   │   ├── db.py                   # SQLAlchemy engine & session factory
│   │   ├── main.py                 # FastAPI application & lifespan
│   │   ├── models_db.py            # Database tables
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   ├── ml/                     # ML Inference Modules:
│   │   │   ├── condition.py          # ResNet-18 wear classifier
│   │   │   ├── damage.py             # YOLOv8 damage segmentation
│   │   │   ├── gradcam.py            # Grad-CAM heatmap generator
│   │   │   ├── loader.py             # Startup ModelRegistry
│   │   │   ├── material.py           # ResNet-18 material classifier
│   │   │   ├── vlm.py                # Multimodal VLM perception client
│   │   │   └── tag/                  # Tag OCR pipeline
│   │   ├── engine/                 # Decision Engine:
│   │   │   ├── explanation.py        # Plain-language explanation builder
│   │   │   ├── geography.py          # Haversine distance ranking
│   │   │   ├── impact.py             # Cited LCA impact calculator
│   │   │   ├── qr.py                 # Cryptographic QR generator
│   │   │   ├── ranking.py            # BaseRanker interface & Formula ranker
│   │   │   ├── rules.py              # Layer A SQL eligibility constraints
│   │   │   └── xgb_ranker.py         # Layer B XGBoost ranker + SHAP
│   │   └── seed/                   # Seed CSVs (facilities, brands, rules, impact)
│   ├── tests/                      # Automated test suite (60 unit & integration tests)
│   └── requirements.txt            # Python dependencies
├── frontend/                       # Next.js Application:
│   ├── src/
│   │   ├── app/                    # Next.js App Router (page.tsx, layout.tsx)
│   │   ├── components/             # React UI components
│   │   ├── lib/                    # API client (api.ts)
│   │   └── types/                  # TypeScript interface contracts
│   ├── package.json
│   └── tsconfig.json
├── ml/                             # Offline model training scripts & notebooks
├── samples/                        # Sample garment test images
├── scripts/                        # Utility scripts (try_vlm.py CLI diagnostic)
├── weights/                        # Model weights directory (optional local .pt files)
├── .env.example                    # Environment variables template
├── docker-compose.yml              # Optional container deployment
└── README.md                       # Project documentation
```

---

## 7. Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### Backend Setup
```powershell
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Configure environment (copy template and optionally add VLM_API_KEY)
cp .env.example .env

# 3. Seed database (15 facilities, 8 partner brands, LCA impact factors)
python -m backend.app.seed.seed_data

# 4. Start the backend API server (Port 8000)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **API Documentation (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Model Health Status:** [http://127.0.0.1:8000/health/models](http://127.0.0.1:8000/health/models)

### Frontend Setup
```powershell
# In a separate terminal:
cd frontend
npm install
npm run dev
```
- **Web Application:** [http://localhost:3000](http://localhost:3000)

### Testing
Run the automated test suite (60 unit & integration tests covering VLM perception, decision engine, OCR, and API contracts):
```powershell
python -m pytest backend/tests -v
```

---

## 8. API Contract Overview

### `POST /analyze` (Multipart Form-Data)
Uploads garment photographs and optional care tag photo. Returns material classification, wear condition, defect percentage, and parsed care label.
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "garment_images=@garment_front.jpg" \
  -F "tag_image=@care_tag.jpg"
```

### `POST /recommend` (JSON Body)
Evaluates eligibility rules, scores pathways using XGBoost + SHAP, ranks by geographical proximity to facilities, and generates a QR tracking passport.
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

### `POST /outcome/confirm` (JSON Body)
Partner intake portal endpoint to confirm physical drop-off and certify real-world circular outcomes.
```bash
curl -X POST http://127.0.0.1:8000/outcome/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "qr_id": "qr_4b7f92e10c",
    "partner_facility_id": 1,
    "confirmed_pathway": "repair"
  }'
```

---

## 9. Verified Drop-off Network Directory

The platform includes 15 calibrated municipal drop-off facilities:

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

## 10. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
