# RE-THREAD: Project Documentation

*AI-Powered Circular Fashion Decision Platform · Team Circular Transformation · International Grand Challenge 2026 (theme: AI for Climate Change), PCCOE Pune · Mentor: Harsha Talele · Written as shared context for AI agents and new collaborators.*

## 1. How to use this document

This is the single source of truth for what RE-THREAD is, why it exists, how it is designed, and what has been decided. Items are labelled:

- **[DECIDED]**: settled design choice. Do not change without asking the team.

- **[PLANNED]**: intended but not yet built.

- **[UNVERIFIED]**: believed true but not yet checked. Verify before relying on it.

The team has already started building. The backend/frontend skeleton exists; trained ML models are being integrated. The team members are not ML specialists, so explanations, code and guidance should be simple, step by step, and favour well-supported libraries over custom research.

## 2. One-paragraph summary

RE-THREAD is a web app that helps a person decide what to do with an unwanted garment. The user photographs the garment (and optionally its care tag). The system analyses material, condition and visible damage with computer vision, reads the tag for brand and composition, then a hybrid decision engine (hard business rules plus a machine-learning ranker) recommends the best next life: **Reuse/Resell, Repair, Donate, Recycle, or Brand Take-back**. Every recommendation comes with a plain-language explanation, a quantified water/CO₂ saving, and the nearest eligible drop-off point. A QR scan at the drop-off point confirms the real outcome, which feeds model retraining. Tagline: *"Your Clothes. Your Stories. Their Next Chapter."*

## 3. The problem

The textile industry causes heavy environmental impact through water use, carbon emissions, chemical processing, microfibre shedding and waste. Consumers lack simple information to understand this or decide what to do with a garment at the end of its use. Clothes are also used less than expected before being discarded.

Figures used on the team's slides (India; sources should be re-verified before external citation):

| Impact | Figure |
| --- | --- |
| Water use of textile industry | about 1.92 billion m³ per year |
| CO₂ emissions of textile sector | about 42–67 million tonnes per year |
| Dye production | about 200,000 tonnes per year |
| Microfibres from washing machines | about 123 billion per year |
| Textile waste | about 7.07 million tonnes per year |

Lifecycle: raw materials → manufacturing → use (often short) → end of life (often landfill).

## 4. Purpose and goals

- Keep garments in use longer (reuse, repair).

- Recover value when garments cannot be reused (donation, brand take-back, recycling).

- Make the right choice easy: one photo gives a clear, explained recommendation.

- Make impact measurable: show water and CO₂ saved per action.

- Build real-world outcome data so the AI improves over time.

Guiding line: *"Keep garments in use longer. Recover their value when they can't be reused. Nothing goes to waste."*

## 5. Users and stakeholders

| Stakeholder | Value they get |
| --- | --- |
| Consumers | Simple disposal decisions, rewards, resale value, personal impact tracking |
| Fashion brands | Smarter take-back and garment recovery programmes, brand coupons/rewards channel |
| Collection centres | Automated sorting into reuse, repair and recycling pathways |
| Recyclers and sorting centres | Faster, more accurate textile classification before intake |
| Repair shops and donation partners | Pre-qualified, relevant garments |

## 6. Main features

- **Photo and tag input**: multi-angle photos (full garment, texture close-up, damage close-up) plus garment tag.

- **Tag analysis**: finds the tag, reads it with OCR, extracts brand and composition.

- **Garment analysis**: material classification, condition classification, damage detection with damaged-area %.

- **Hybrid decision engine**: editable rules (eligibility) plus ML ranking (best option among eligible ones).

- **Ranked pathway output**: all five pathways with confidence, not a single forced answer.

- **Explainable AI**: SHAP for the ranking decision, Grad-CAM heatmaps for vision predictions, plus a plain-language explanation.

- **Climate impact scoring**: estimated water and CO₂ savings for each recommended pathway.

- **Geography-aware ranking**: pathways are re-ranked by distance to the nearest eligible drop-off point.

- **QR-confirmed lifecycle loop**: scan at drop-off confirms the action and produces real labelled outcomes.

- **Brand reward system**: sincere, confirmed actions can earn brand coupons, discounts and awards.

- **Measurable impact dashboard**: tracks wears, repairs, reuse, donations and estimated environmental impact over time.

## 7. System architecture

Pipeline: **Input → Analyse Garment → Decision Engine → Pathway → Lifecycle Loop**, with an Explainability layer across the stages.

### 7.1 Stage 1: Input

- User uploads or captures several photos and, where available, a photo of the care tag.

- Images are preprocessed with OpenCV (resize, normalise, crop).

### 7.2 Tag analysis [DECIDED]

Six steps:

- **Detect**: a fine-tuned YOLOv8 model finds the tag region in the garment photo and crops it.

- **Clean**: OpenCV deskew, rotate, contrast enhancement and binarisation (care labels are small and low contrast).

- **Extract**: PaddleOCR reads the text.

- **Parse**: regex plus a fixed fibre vocabulary pulls composition percentages (e.g. 60% cotton, 40% polyester); fuzzy string matching (e.g. Levenshtein) matches the brand against a known brand list, because OCR makes small errors.

- **Score confidence**: use OCR confidence; check that composition percentages sum to about 100; if not, mark as parse failed.

- **Route**: brand goes to the Stage 3 rule layer; composition goes to Stage 2 as a cross-check; if the tag is missing or unreadable, rely on vision only.

**Role of the tag (important):** the tag is a *supporting* signal for two purposes only: (a) brand identification for take-back eligibility, and (b) secondary verification of the vision-based material estimate. It is **not** ground truth and does **not** override the vision model, because tags can be missing, faded, or mislabelled by manufacturers. If tag and vision disagree significantly, flag the garment as "composition uncertain".

### 7.3 Stage 2: Analyse garment [DECIDED]

Garment type was deliberately removed from the analysis scope. The focus is material, condition and damage.

**Material classifier**

- Model: ResNet-18, ImageNet-pretrained, fine-tuned on fabric/fibre images.

- Output: a **coarse** class with confidence: natural, synthetic, blend, or uncertain. It does **not** claim precise blend percentages, because RGB photos cannot reliably resolve ratios like 60/40 vs 80/20 (that needs NIR/HSI spectral hardware).

- Below a confidence threshold (start around 0.6, tune later), return "uncertain" instead of a label.

**Condition classifier**

- Model: ResNet-18, ImageNet-pretrained, fine-tuned.

- Output: new, gently_used, worn, heavily_worn, with confidence.

- Plain softmax classification for the MVP. Ordinal loss (CORAL) is a possible future improvement, since condition is an ordered scale.

- No public pretrained "garment condition" model exists. The plan is to build one using the dataset in section 9.

**Damage detection**

- Model: YOLOv8 (small, segmentation variant if the dataset supports masks).

- Output: damage detected yes/no, location, type if labelled, and damaged-area percentage of the garment.

**Architecture note:** an earlier design used one shared backbone with several heads. For simplicity and easier debugging, the current build trains **separate small models** for material and condition. A shared backbone is an optional later optimisation.

**NIR/HSI [PLANNED, roadmap]:** when composition is uncertain, the system can route to a partner facility's existing NIR/HSI scanner through a defined API (for example /scan/nir). The platform is designed to accept spectral input but does not build hardware. Real industrial sorting already uses NIR, so RE-THREAD is positioned as the AI decision layer on top of such infrastructure.

### 7.4 Stage 3: Decision engine (hybrid) [DECIDED]

**Layer A: rule/constraint layer (deterministic, editable tables in PostgreSQL)**

- Brand take-back eligibility (which brands accept which items).

- Material recyclability by facility (which facility accepts which material).

- Repairability rules (damage type and size versus repairable or not).

- Partner facility list with locations.

- Why rules and not ML: these are operational facts that change independently (new partner, new policy). A table updates instantly with no retraining and stays auditable.

**Layer B: ML ranking (XGBoost)**

- Input features: material class, condition, damage %, brand, plus confidence values.

- Output: scores per eligible pathway (resale/reuse desirability, repair worthiness, recycling suitability).

- Why XGBoost: strong on small structured tabular data, needs little data, built-in feature importance, cheap to retrain, works well with SHAP.

**Layer C: post-ranking adjustments**

- **Geography:** re-rank using distance to the nearest eligible drop-off point, so a theoretically best but unreachable option does not win.

- **Climate impact:** attach estimated water and CO₂ savings per pathway from published per-kg lifecycle factors multiplied by garment weight. This is a lookup table, not a model. Factors must come from cited sources.

- Objective idea: ranking combines desirability score and environmental impact, so a lower-value but higher-impact option (e.g. recycle for a low-demand item) can outrank a purely value-driven one.

**Combine:** rules decide *which pathways are eligible*; ML ranks *the best eligible pathway*; adjustments account for distance and impact.

### 7.5 Stage 4: Pathway output

Ranked output across five pathways: **Reuse/Resell, Repair, Donation, Recycle, Brand Take-back**, each with a score/confidence. When composition is uncertain or scores are close, show primary recommendation plus alternatives. Include uncertainty honestly.

### 7.6 Explainable AI [DECIDED]

- **SHAP** on XGBoost: which factors (material, condition, damage %, brand) drove the pathway choice. Very easy to implement: shap.TreeExplainer supports XGBoost natively.

- **Grad-CAM** on ResNet-18 heads: heatmap of where on the garment the model looked. Use the pytorch-grad-cam library.

- **YOLOv8 explainability** (EigenCAM variants) is a stretch goal. Damage boxes/masks are already visually interpretable.

- **Plain-language trace**, for example: *"Recommended: Repair. Small tear detected (see highlighted area), natural fibre, gently used, nearest repair partner 2 km away, est. water saving X litres."*

- Implementation priority: SHAP first, then Grad-CAM on material/condition, then YOLO explainability.

### 7.7 Stage 5: Lifecycle loop (flywheel) [DECIDED]

- Each recommendation generates a unique **QR code**.

- Partner locations (donation bins, repair shops, recyclers, brand stores) scan it on intake.

- Each confirmed record stores: photo, predictions, recommended pathway, actual outcome.

- Unscanned recommendations are **not** counted as outcomes, so no fake data enters training.

- Confirmed outcomes periodically retrain the material and condition models and provide labels for the XGBoost ranker.

- Rescanning the same garment ID over time can track condition drift.

- Confirmed actions also drive the reward system and the impact dashboard.

## 8. Models and why

| Task | Model | Why it fits |
| --- | --- | --- |
| Tag localisation | YOLOv8 (fine-tuned, class "tag") | Fast, pretrained, easy to fine-tune; crops tag so OCR is accurate |
| Tag text | PaddleOCR | Better than Tesseract on small, low-contrast, rotated label text; open source, no per-scan cost |
| Material | ResNet-18 (PyTorch, ImageNet-pretrained) | Light, fast to fine-tune on limited data, strong on texture |
| Condition | ResNet-18 (same approach) | Wear patterns (fading, pilling, fraying) are visual texture cues |
| Damage | YOLOv8 (seg if possible) | Gives location and area %, directly usable by the decision engine |
| Ranking | XGBoost (LightGBM is an acceptable alternative) | Best fit for small tabular data, interpretable |
| Explanation | SHAP, Grad-CAM | Standard libraries, minimal custom code |

## 9. Datasets

| Model | Dataset | Notes |
| --- | --- | --- |
| Material | ImageNet (pretraining) plus TextileNet-style fabric/fibre images (fine-tuning) | **[UNVERIFIED]** TextileNet is best treated as a fine-tuning dataset/taxonomy, not a ready pretrained checkpoint. Confirm availability and licence. Any fabric-texture dataset from Kaggle or Roboflow is an acceptable first version. |
| Condition | "Clothing Dataset for Second-Hand Fashion" (Zenodo), from RISE Research Institutes of Sweden, Wargön Innovation and Myrorna, supported by the EU CISUTAC project | About 31,638 garments from real sorting facilities, multiple images per item, labelled by sorting destination (reuse, export, recycle, repair, remake, thermal waste). It is a **proxy** for condition, not a direct new/worn label. **[UNVERIFIED]** Check licence and the exact annotation fields before deciding the label mapping. Likely need to map outcomes to condition levels and/or hand-label a few hundred images. |
| Damage | Roboflow Universe fabric/clothing defect datasets, FabricSpotDefect (spot defects, YOLOv8/COCO formats on Roboflow), plus self-annotated garment photos | Prefer datasets exportable in YOLOv8 format. FabricSpotDefect covers spots only, so add tear/hole data. |
| Tag detection | Self-collected and annotated care-label photos | Small set is enough to fine-tune YOLOv8 for one class. |
| XGBoost ranker | Structured feature logs from the app and QR-confirmed outcomes | Needs a bootstrap before real outcomes exist (see section 17). |

Optional supplement: resale-platform listing photos and condition tags as weak labels. Respect licensing and terms of use; do not scrape indiscriminately.

## 10. Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React / Next.js (photo upload, results, impact dashboard) |
| Backend | FastAPI (Python, hosts ML models); Node.js optionally for auth/API layer |
| OCR | PaddleOCR |
| Vision models | PyTorch (ResNet-18), Ultralytics YOLOv8 |
| Image processing | OpenCV |
| Ranking | XGBoost |
| Explainability | SHAP, pytorch-grad-cam |
| Database | PostgreSQL (rules tables, facilities, users, outcomes) |
| Training environment | Google Colab (free GPU) |
| Confirmation | QR codes (generation and scan flow) |

## 11. API contract (keep stable)

The frontend and decision engine depend on this JSON shape. Replace stub internals with real models without changing the shape.

`POST /analyze` (multipart images, optional tag image):

```json
{
  "material": {"label": "natural", "confidence": 0.82},
  "condition": {"label": "gently_used", "confidence": 0.74},
  "damage": {"detected": true, "area_percent": 6.5, "boxes": []},
  "tag": {
    "brand": "example-brand",
    "composition": {"cotton": 60, "polyester": 40},
    "ocr_confidence": 0.88,
    "agrees_with_vision": true
  },
  "composition_status": "confident | uncertain"
}
```

`POST /recommend` (takes the analysis plus user location):

```json
{
  "ranked_pathways": [
    {"pathway": "repair", "score": 0.71, "eligible": true,
     "nearest_partner": {"name": "...", "distance_km": 2.1},
     "impact": {"water_litres_saved": 0, "co2_kg_saved": 0}}
  ],
  "explanation": "plain-language trace",
  "shap": {"material": 0.0, "condition": 0.0, "damage_percent": 0.0, "brand": 0.0},
  "qr_id": "unique-id"
}
```

Planned: POST /outcome/confirm (QR scan by partner), POST /scan/nir (future spectral input). Impact numbers above are placeholders; real values come from a cited lifecycle-factor table.

## 12. Model integration process (for the team)

A trained model is a file of learned weights plus a few lines of loading code. Integration means loading that file in the backend and returning predictions in the agreed JSON.

- **Stub first:** build /analyze returning fake values in the final JSON shape so frontend and decision engine can be built and tested now.

- **Train in Colab:**
  - Damage: export a YOLOv8-format dataset from Roboflow, then `YOLO("yolov8n-seg.pt").train(data="data.yaml", epochs=50, imgsz=640)`; result is best.pt.
  - Material/condition: put images in folders by label, load pretrained ResNet-18, replace the final layer (model.fc) with the number of classes, train, save with torch.save(...).

- **Load once at backend startup**, not per request.

- **Swap stubs for real models one at a time**, keeping the JSON shape.

- **Connect frontend** (send photos via FormData; display returned results) and feed outputs to the decision engine.

Suggested order: stub and frontend wiring, damage model (easiest and most visual), condition model, material model, tag pipeline, decision engine, SHAP/Grad-CAM, QR loop.

**Fallback [PLANNED if training slips]:** a vision-capable LLM API can produce a first version of material/condition/damage as structured JSON. Cost, latency and not being a self-trained model are the trade-offs. If used, state this honestly in the pitch and describe trained models as the scaled version.

## 13. Key design decisions and rationale (do not undo)

- Vision is the primary source for material and condition; the tag is a secondary cross-check and brand-routing signal.

- Material output is coarse with confidence, not precise percentages. Uncertainty is surfaced and routed, never hidden.

- Rules for hard constraints (explicit, editable, auditable); ML only for soft ranking.

- Ranked pathways with explanation, not a single opaque answer.

- Simplicity over novelty: ImageNet-pretrained ResNet-18 and YOLOv8 rather than exotic architectures.

- Garment type removed from scope.

- Outcomes count only when confirmed by QR scan.

- No hardware is built; NIR/HSI is an integration point through partners.

## 14. Known weaknesses and mitigations

| Weakness | Mitigation |
| --- | --- |
| Tags can be wrong or missing | Tag is secondary; disagreement flags "uncertain" |
| RGB cannot resolve blend ratios | Coarse classes plus confidence; NIR routing for uncertain cases |
| Condition is subjective, no public labelled data | RISE/CISUTAC proxy labels, small hand-labelled calibration set, QR outcomes over time |
| Recommendation may be unreachable | Distance-based re-ranking using partner database |
| No climate quantification | Per-pathway water/CO₂ lookup from cited lifecycle factors |
| Flywheel could be fictional | QR confirmation; unconfirmed items excluded |
| Multi-material garments (e.g. shell and lining) | MVP treats primary material only, with a caveat |
| Unknown or counterfeit brands | Take-back gate fails safe: never blocks the user; falls back to donate/recycle |
| Privacy | Process garment regions only; no personal or biometric data; check dataset licences |

## 15. Scope: MVP versus roadmap

**MVP (hackathon build):** photo and tag input, tag OCR with brand/composition parsing, material and condition classifiers, damage detection, rules table plus ranking (XGBoost or a weighted scoring formula), ranked pathways, plain-language explanation, SHAP, QR confirmation flow, basic impact estimate.

**Roadmap:** Grad-CAM across all models, YOLO explainability, NIR/HSI integration with partner scanners, ordinal condition loss, shared multi-task backbone, on-device inference (TFLite/CoreML) with cloud escalation for ambiguous cases, multi-region material estimates, active learning loop, brand reward marketplace, detailed impact dashboard.

## 16. Validation plan

| Component | Metric |
| --- | --- |
| Material and condition | Accuracy and macro-F1 on held-out data; confusion matrix; for condition also error between adjacent versus distant classes |
| Damage | mAP (box/mask) and area-% error |
| Tag OCR and parsing | Field-level accuracy for brand and composition; rate of parse failures |
| Confidence gating | Precision/recall of the "uncertain" flag |
| Decision engine | Agreement with sorting-facility outcomes (RISE data) where mappable; SHAP sanity checks |
| System | End-to-end latency; share of recommendations confirmed by QR |

Compare against baselines reported in the cited literature (Barros et al. 2020, Lee et al. 2023, Babu et al. 2025, Das et al. 2025). The contribution is combining identification with condition assessment and recovery decisions, not just image classification.

## 17. Open questions

- **XGBoost training labels before real outcomes exist.** Options: map RISE/CISUTAC sorting outcomes to pathways, or start with a transparent weighted scoring formula and introduce XGBoost once QR data accumulates.

- Exact label mapping from RISE/CISUTAC destinations to condition classes; dataset licence.

- TextileNet availability and licence, or which substitute fabric dataset to use.

- Source of lifecycle factors (water and CO₂ per kg per pathway) and how garment weight is estimated (user input, garment-type average, or a default).

- Source and coverage of the brand take-back and facility data for the demo region (Pune/India); likely a small curated table.

- Material class list (coarse vs per-fibre) and the confidence threshold values.

- Reward system details: who funds coupons and how fraud is prevented.

## 18. Glossary

- **OCR:** optical character recognition, reading text from images.

- **YOLOv8:** fast object detection/segmentation model family (Ultralytics).

- **ResNet-18:** small convolutional neural network for image classification.

- **Fine-tuning:** adapting a pretrained model to a new task with a smaller dataset.

- **XGBoost:** gradient-boosted decision trees for tabular data.

- **SHAP:** method that shows how much each input feature contributed to a prediction.

- **Grad-CAM:** heatmap showing which image regions influenced a CNN prediction.

- **NIR / HSI:** near-infrared / hyperspectral imaging; reads a fabric's chemical fingerprint to identify fibres and blends.

- **Circular fashion:** keeping garments and materials in use as long as possible.

- **Take-back:** a brand programme that accepts used garments.

## 19. Guidance for agents working on this project

- Read sections 7, 11 and 13 before changing any code or design.

- Keep explanations beginner-friendly; the team is new to ML integration.

- Prefer well-maintained libraries and pretrained models; avoid custom research code.

- Do not claim capabilities the system lacks (precise blend percentages, built hardware, verified outcomes).

- Keep the API JSON shape stable; change internals behind it.

- Mark uncertainty explicitly in outputs and in documentation.

- Verify [UNVERIFIED] items before depending on them, and report what you find.

- Cite sources for any environmental statistic or lifecycle factor.