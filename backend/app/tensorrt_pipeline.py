"""
TensorRT Optimization for Face Recognition Pipeline
Converts PyTorch → ONNX → TensorRT

Requires: NVIDIA GPU, CUDA, cuDNN, TensorRT 8.6+
Fixed for dynamic batch sizes with optimization profile
"""

import platform
import sys
from typing import Optional, Tuple
import numpy as np
import torch
import cv2
from PIL import Image
from deepface import DeepFace
from facenet_pytorch import MTCNN, InceptionResnetV1
import onnx


class ModelConverter:
    """Convert PyTorch models to TensorRT for 30-40% speedup"""

    @staticmethod
    def pytorch_to_onnx(
        model_name: str = "embedder",
        output_dir: str = "./models"
    ) -> str:
        """
        Convert InceptionResnetV1 PyTorch model to ONNX format
        
        Args:
            model_name: "embedder" (InceptionResnetV1)
            output_dir: Directory to save ONNX file
            
        Returns:
            Path to ONNX file
        """
        print(f"\n🔄 Converting {model_name} PyTorch → ONNX...")
        
        # Step 1: Load PyTorch model
        if model_name == "embedder":
            model = InceptionResnetV1(pretrained="vggface2").eval()
            dummy_input = torch.randn(1, 3, 160, 160)
            onnx_path = f"{output_dir}/embedder.onnx"
            input_names = ["input"]
            output_names = ["output"]
            
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        # Step 2: Export to ONNX
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=input_names,
            output_names=output_names,
            dynamic_axes={
                input_names[0]: {0: "batch_size"},
                output_names[0]: {0: "batch_size"}
            },
            opset_version=13,
            do_constant_folding=True,
            verbose=False
        )
        
        print(f"✅ ONNX exported: {onnx_path}")
        
        # Step 3: Verify ONNX model
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        print(f"✅ ONNX model verified")
        
        return onnx_path

    @staticmethod
    def onnx_to_tensorrt(
        onnx_path: str,
        output_dir: str = "./models",
        fp16: bool = True,
        int8: bool = False,
        max_workspace_size: int = 1 << 30  # 1GB
    ) -> str:
        """
        Convert ONNX model to TensorRT engine (TensorRT 8.6+ compatible)
        Includes optimization profile for dynamic batch sizes
        
        Args:
            onnx_path: Path to ONNX model
            output_dir: Directory to save TensorRT engine
            fp16: Enable FP16 precision (40% speedup, minimal accuracy loss)
            int8: Enable INT8 quantization (60% speedup, more accuracy loss)
            max_workspace_size: GPU memory for optimization (bytes)
            
        Returns:
            Path to TensorRT engine file (.trt)
        """
        print(f"\n🔄 Converting ONNX → TensorRT...")
        
        try:
            import tensorrt as trt
        except ImportError:
            print("❌ TensorRT not installed. Install with:")
            print("   pip install tensorrt")
            return None
        
        # Step 1: Create logger
        logger = trt.Logger(trt.Logger.WARNING)
        
        # Step 2: Create builder
        builder = trt.Builder(logger)
        network = builder.create_network(
            1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
        )
        parser = trt.OnnxParser(network, logger)
        
        # Step 3: Parse ONNX
        print(f"📖 Parsing ONNX: {onnx_path}")
        with open(onnx_path, "rb") as f:
            if not parser.parse(f.read()):
                print("❌ ONNX parsing failed")
                for error in range(parser.num_errors):
                    print(f"   Error {error}: {parser.get_error(error)}")
                return None
        
        print(f"✅ ONNX parsed successfully")
        
        # Step 4: Create builder config
        config = builder.create_builder_config()
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, max_workspace_size)
        
        # CRITICAL: Create optimization profile for dynamic batch sizes
        profile = builder.create_optimization_profile()
        
        # Get input tensor
        input_tensor = network.get_input(0)
        input_name = input_tensor.name
        
        # Define min, opt, max batch sizes for the input
        # Format: (batch_size, 3, 160, 160)
        profile.set_shape(
            input_name,
            min=(1, 3, 160, 160),      # Minimum batch size = 1
            opt=(1, 3, 160, 160),      # Optimal batch size = 1
            max=(16, 3, 160, 160)      # Maximum batch size = 16
        )
        config.add_optimization_profile(profile)
        
        print(f"📊 Optimization profile: batch size 1-16")
        
        # Step 5: Enable optimizations
        if fp16 and builder.platform_has_fast_fp16:
            config.set_flag(trt.BuilderFlag.FP16)
            print("⚡ FP16 enabled (40% speedup)")
        
        if int8 and builder.platform_has_fast_int8:
            config.set_flag(trt.BuilderFlag.INT8)
            print("⚡ INT8 enabled (60% speedup)")
        
        # Step 6: Build engine (TensorRT 8.6+ compatible)
        print("🔨 Building TensorRT engine (may take 1-5 minutes)...")
        
        try:
            # TensorRT 8.6+ API
            serialized_network = builder.build_serialized_network(network, config)
            
            if serialized_network is None:
                print("❌ Engine serialization failed")
                return None
            
            runtime = trt.Runtime(logger)
            engine = runtime.deserialize_cuda_engine(serialized_network)
            
        except AttributeError:
            # Fallback for older TensorRT versions
            print("⚠️  Using TensorRT 8.5 compatibility mode...")
            engine = builder.build_engine(network, config)
            
            if engine is None:
                print("❌ Engine build failed")
                return None
        
        if engine is None:
            print("❌ Engine creation failed")
            return None
        
        # Step 7: Serialize engine
        engine_path = onnx_path.replace(".onnx", "_fp16.trt" if fp16 else ".trt")
        if int8:
            engine_path = onnx_path.replace(".onnx", "_int8.trt")
        
        with open(engine_path, "wb") as f:
            f.write(engine.serialize())
        
        print(f"✅ TensorRT engine saved: {engine_path}")
        
        return engine_path

    @staticmethod
    def full_conversion_pipeline(
        output_dir: str = "./models",
        fp16: bool = True,
        int8: bool = False
    ) -> dict:
        """
        Complete conversion: PyTorch → ONNX → TensorRT
        
        Returns:
            {"embedder_trt": "/path/to/embedder_fp16.trt"}
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"TENSORRT CONVERSION PIPELINE")
        print(f"{'='*60}")
        
        # Step 1: PyTorch → ONNX
        onnx_path = ModelConverter.pytorch_to_onnx("embedder", output_dir)
        
        # Step 2: ONNX → TensorRT
        trt_path = ModelConverter.onnx_to_tensorrt(
            onnx_path,
            output_dir,
            fp16=fp16,
            int8=int8
        )
        
        if trt_path:
            print(f"\n✅ CONVERSION COMPLETE")
            print(f"📦 TensorRT engine: {trt_path}")
            return {"embedder_trt": trt_path}
        else:
            print(f"\n❌ CONVERSION FAILED")
            return None
