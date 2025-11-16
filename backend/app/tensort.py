from tensorrt_pipeline import ModelConverter
import os

# Create models directory
os.makedirs("./models", exist_ok=True)

print("\n" + "="*60)
print("CONVERTING PYTORCH -> TENSORRT")
print("="*60)

# Convert (takes 3-5 minutes)
result = ModelConverter.full_conversion_pipeline(
    output_dir="./models",
    fp16=True,
    int8=False
)

if result:
    print("\n✅ CONVERSION SUCCESSFUL!")
    print(f"📦 Your files:")
    print(f"   - ./models/embedder.onnx (90MB)")
    print(f"   - ./models/embedder_fp16.trt (30MB)")
else:
    print("\n❌ Conversion failed. Check errors above.")
