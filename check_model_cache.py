
import os
from transformers import CLIPModel, CLIPProcessor

model_name = "openai/clip-vit-base-patch32"

print(f"Checking cache for {model_name}...")

try:
    # Try loading with local_files_only=True
    model = CLIPModel.from_pretrained(model_name, local_files_only=True)
    processor = CLIPProcessor.from_pretrained(model_name, local_files_only=True)
    print("✅ Model found in local cache.")
except Exception as e:
    print(f"❌ Model NOT found in local cache (or error): {e}")

try:
    # Check if checking for safetensors specifically fails or is needed
    print("Checking loading with use_safetensors=False...")
    model = CLIPModel.from_pretrained(model_name, local_files_only=True, use_safetensors=False)
    print("✅ Model loaded with use_safetensors=False.")
except Exception as e:
    print(f"⚠️ Could not load with use_safetensors=False: {e}")
