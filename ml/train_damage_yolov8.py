"""RE-THREAD: Standalone Script for YOLOv8 Garment Damage Segmentation Training.

Can be run in Google Colab or on a GPU workstation:
    python ml/train_damage_yolov8.py --data /path/to/data.yaml --epochs 50 --batch 16
"""

import argparse
import os
import shutil
from ultralytics import YOLO


def train_damage_model(
    data_yaml: str,
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 16,
    output_dir: str = "weights",
):
    print("=" * 60)
    print("RE-THREAD: Training YOLOv8 Garment Defect Segmentation")
    print(f"Data configuration: {data_yaml}")
    print(f"Epochs: {epochs} | Image size: {imgsz} | Batch size: {batch}")
    print("=" * 60)

    # 1. Load pretrained nano segmentation model
    model = YOLO("yolov8n-seg.pt")

    # 2. Train on defect dataset
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project="rethread_training",
        name="damage_yolov8_seg",
        save=True,
    )

    # 3. Locate best trained weights
    best_weights = "rethread_training/damage_yolov8_seg/weights/best.pt"
    if os.path.exists(best_weights):
        os.makedirs(output_dir, exist_ok=True)
        target_path = os.path.join(output_dir, "damage.pt")
        shutil.copy(best_weights, target_path)
        print("\n" + "=" * 60)
        print(f"SUCCESS: Best weights saved to: {target_path}")
        print("Move this file to re-thread/weights/damage.pt to enable in backend.")
        print("=" * 60)
    else:
        print(f"Warning: Could not find best.pt at {best_weights}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8-seg garment damage model")
    parser.add_argument("--data", type=str, required=True, help="Path to Roboflow data.yaml")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--output-dir", type=str, default="weights", help="Directory to save damage.pt")
    args = parser.parse_args()

    train_damage_model(
        data_yaml=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        output_dir=args.output_dir,
    )
