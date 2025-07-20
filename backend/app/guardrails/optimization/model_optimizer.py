"""
Model Optimizer for Phase 2
Implements quantization, ONNX conversion, and model optimization
Target: 75% size reduction with <2% accuracy loss
"""

import os
import logging
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Import optional dependencies with fallbacks
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("PyTorch not available, model optimization will be limited")

try:
    import onnx
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("ONNX not available, ONNX conversion will be disabled")

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Transformers not available, model optimization will be limited")

try:
    from optimum.onnxruntime import ORTModelForSequenceClassification
    OPTIMUM_AVAILABLE = True
except ImportError:
    OPTIMUM_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Optimum not available, advanced ONNX optimization will be disabled")

logger = logging.getLogger(__name__)

class ModelOptimizer:
    """
    Model optimization framework implementing Phase 2 objectives:
    - Model quantization (75% size reduction)
    - ONNX conversion (2-3x inference speedup)
    - Memory optimization
    """
    
    def __init__(self, cache_dir: str = "model_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Optimization tracking
        self.optimization_stats = {
            "models_optimized": 0,
            "total_size_reduction": 0.0,
            "average_speedup": 0.0,
            "optimization_history": []
        }
        
        logger.info(f"ModelOptimizer initialized with cache dir: {cache_dir}")
    
    def quantize_model(self, 
                      model_path: str, 
                      model_name: str,
                      quantization_type: str = "dynamic") -> Dict[str, Any]:
        """
        Quantize a model to reduce size by ~75%
        
        Args:
            model_path: Path to the original model
            model_name: Name identifier for the model
            quantization_type: Type of quantization ('dynamic', 'static', 'qat')
            
        Returns:
            Dict with optimization results
        """
        try:
            if not TORCH_AVAILABLE or not TRANSFORMERS_AVAILABLE:
                return {
                    "error": "PyTorch and Transformers required for quantization",
                    "model_name": model_name,
                    "dependencies_missing": True
                }
            
            logger.info(f"Starting quantization for {model_name}...")
            start_time = time.time()
            
            # Load original model
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSequenceClassification.from_pretrained(model_path)
            
            # Get original model size
            original_size = self._get_model_size(model)
            logger.info(f"Original model size: {original_size:.2f} MB")
            
            # Quantize model
            if quantization_type == "dynamic":
                from torch.quantization import quantize_dynamic
                quantized_model = quantize_dynamic(
                    model,
                    {torch.nn.Linear},  # Quantize linear layers
                    dtype=torch.qint8
                )
            else:
                # For future implementation of static/QAT quantization
                quantized_model = model
                logger.warning(f"Quantization type {quantization_type} not implemented, using original model")
            
            # Get quantized model size
            quantized_size = self._get_model_size(quantized_model)
            size_reduction = (1 - quantized_size / original_size) * 100
            
            # Save quantized model
            quantized_path = self.cache_dir / f"{model_name}_quantized"
            quantized_path.mkdir(exist_ok=True)
            
            torch.save(quantized_model.state_dict(), quantized_path / "model.pth")
            tokenizer.save_pretrained(quantized_path)
            
            # Save optimization metadata
            optimization_metadata = {
                "model_name": model_name,
                "optimization_type": "quantization",
                "quantization_type": quantization_type,
                "original_size_mb": original_size,
                "optimized_size_mb": quantized_size,
                "size_reduction_percent": size_reduction,
                "optimization_time_seconds": time.time() - start_time,
                "optimized_path": str(quantized_path)
            }
            
            self._save_optimization_metadata(model_name, optimization_metadata)
            self._update_optimization_stats(optimization_metadata)
            
            logger.info(f"Quantization completed: {size_reduction:.1f}% size reduction")
            return optimization_metadata
            
        except Exception as e:
            logger.error(f"Quantization failed for {model_name}: {e}")
            return {"error": str(e), "model_name": model_name}
    
    def convert_to_onnx(self, 
                       model_path: str, 
                       model_name: str,
                       optimize_for_inference: bool = True) -> Dict[str, Any]:
        """
        Convert model to ONNX format for 2-3x inference speedup
        
        Args:
            model_path: Path to the model
            model_name: Name identifier for the model
            optimize_for_inference: Whether to optimize for inference
            
        Returns:
            Dict with conversion results
        """
        try:
            if not ONNX_AVAILABLE or not TORCH_AVAILABLE or not TRANSFORMERS_AVAILABLE:
                return {
                    "error": "ONNX, PyTorch, and Transformers required for ONNX conversion",
                    "model_name": model_name,
                    "dependencies_missing": True
                }
            
            logger.info(f"Starting ONNX conversion for {model_name}...")
            start_time = time.time()
            
            # Load model
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSequenceClassification.from_pretrained(model_path)
            
            # Prepare dummy input for ONNX export
            dummy_input = tokenizer(
                "This is a test sentence for ONNX conversion",
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            # ONNX export path
            onnx_path = self.cache_dir / f"{model_name}_onnx"
            onnx_path.mkdir(exist_ok=True)
            onnx_file = onnx_path / "model.onnx"
            
            # Export to ONNX
            torch.onnx.export(
                model,
                tuple(dummy_input.values()),
                str(onnx_file),
                export_params=True,
                opset_version=11,
                do_constant_folding=True,
                input_names=['input_ids', 'attention_mask'],
                output_names=['output'],
                dynamic_axes={
                    'input_ids': {0: 'batch_size', 1: 'sequence'},
                    'attention_mask': {0: 'batch_size', 1: 'sequence'},
                    'output': {0: 'batch_size'}
                }
            )
            
            # Optimize ONNX model if requested
            if optimize_for_inference and OPTIMUM_AVAILABLE:
                try:
                    # Use optimum library for optimization
                    optimized_model = ORTModelForSequenceClassification.from_pretrained(
                        model_path,
                        export=True,
                        provider="CPUExecutionProvider"
                    )
                    optimized_model.save_pretrained(onnx_path)
                    logger.info("ONNX model optimized for inference")
                except Exception as e:
                    logger.warning(f"ONNX optimization failed, using basic conversion: {e}")
            elif optimize_for_inference:
                logger.warning("Optimum not available, using basic ONNX conversion")
            
            # Save tokenizer
            tokenizer.save_pretrained(onnx_path)
            
            # Test inference speed
            pytorch_speed = self._benchmark_pytorch_inference(model, tokenizer)
            onnx_speed = self._benchmark_onnx_inference(str(onnx_file), tokenizer)
            
            speedup = pytorch_speed / onnx_speed if onnx_speed > 0 else 1.0
            
            # Get file sizes
            original_size = self._get_model_file_size(model_path)
            onnx_size = self._get_file_size(onnx_file)
            
            conversion_metadata = {
                "model_name": model_name,
                "optimization_type": "onnx_conversion",
                "original_size_mb": original_size,
                "onnx_size_mb": onnx_size,
                "pytorch_inference_time_ms": pytorch_speed,
                "onnx_inference_time_ms": onnx_speed,
                "speedup_factor": speedup,
                "conversion_time_seconds": time.time() - start_time,
                "onnx_path": str(onnx_path),
                "optimized_for_inference": optimize_for_inference
            }
            
            self._save_optimization_metadata(model_name, conversion_metadata)
            self._update_optimization_stats(conversion_metadata)
            
            logger.info(f"ONNX conversion completed: {speedup:.2f}x speedup")
            return conversion_metadata
            
        except Exception as e:
            logger.error(f"ONNX conversion failed for {model_name}: {e}")
            return {"error": str(e), "model_name": model_name}
    
    def optimize_model_complete(self, 
                              model_path: str, 
                              model_name: str) -> Dict[str, Any]:
        """
        Complete optimization pipeline: quantization + ONNX conversion
        
        Args:
            model_path: Path to the original model
            model_name: Name identifier for the model
            
        Returns:
            Dict with complete optimization results
        """
        logger.info(f"Starting complete optimization for {model_name}...")
        
        results = {
            "model_name": model_name,
            "quantization_results": {},
            "onnx_conversion_results": {},
            "combined_optimization": {}
        }
        
        try:
            # Step 1: Quantization
            quantization_results = self.quantize_model(model_path, model_name)
            results["quantization_results"] = quantization_results
            
            if "error" in quantization_results:
                logger.error(f"Quantization failed, skipping ONNX conversion")
                return results
            
            # Step 2: ONNX conversion on quantized model
            quantized_path = quantization_results["optimized_path"]
            onnx_results = self.convert_to_onnx(quantized_path, f"{model_name}_quantized")
            results["onnx_conversion_results"] = onnx_results
            
            if "error" in onnx_results:
                logger.error(f"ONNX conversion failed")
                return results
            
            # Combined optimization statistics
            original_size = quantization_results["original_size_mb"]
            final_size = onnx_results["onnx_size_mb"]
            total_size_reduction = (1 - final_size / original_size) * 100
            
            results["combined_optimization"] = {
                "original_size_mb": original_size,
                "final_size_mb": final_size,
                "total_size_reduction_percent": total_size_reduction,
                "quantization_reduction_percent": quantization_results["size_reduction_percent"],
                "inference_speedup_factor": onnx_results["speedup_factor"],
                "optimization_successful": True
            }
            
            logger.info(f"Complete optimization successful: {total_size_reduction:.1f}% size reduction, {onnx_results['speedup_factor']:.2f}x speedup")
            
        except Exception as e:
            logger.error(f"Complete optimization failed for {model_name}: {e}")
            results["combined_optimization"] = {"error": str(e)}
        
        return results
    
    def _get_model_size(self, model) -> float:
        """Get model size in MB"""
        param_size = 0
        buffer_size = 0
        
        for param in model.parameters():
            param_size += param.nelement() * param.element_size()
        
        for buffer in model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        
        size_mb = (param_size + buffer_size) / 1024 / 1024
        return size_mb
    
    def _get_model_file_size(self, model_path: str) -> float:
        """Get model file size in MB"""
        try:
            # This is a simplified approach - in practice would need to handle
            # different model formats and multiple files
            total_size = 0
            model_path = Path(model_path)
            
            if model_path.is_file():
                total_size = model_path.stat().st_size
            elif model_path.is_dir():
                for file_path in model_path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception as e:
            logger.warning(f"Could not get model file size: {e}")
            return 0.0
    
    def _get_file_size(self, file_path: Path) -> float:
        """Get file size in MB"""
        try:
            return file_path.stat().st_size / (1024 * 1024)
        except Exception as e:
            logger.warning(f"Could not get file size: {e}")
            return 0.0
    
    def _benchmark_pytorch_inference(self, model, tokenizer, num_samples: int = 10) -> float:
        """Benchmark PyTorch model inference time"""
        try:
            model.eval()
            test_texts = [f"This is test sentence {i} for benchmarking." for i in range(num_samples)]
            
            start_time = time.time()
            
            with torch.no_grad():
                for text in test_texts:
                    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
                    outputs = model(**inputs)
            
            total_time = time.time() - start_time
            avg_time_ms = (total_time / num_samples) * 1000
            
            return avg_time_ms
            
        except Exception as e:
            logger.warning(f"PyTorch benchmarking failed: {e}")
            return 100.0  # Default fallback
    
    def _benchmark_onnx_inference(self, onnx_path: str, tokenizer, num_samples: int = 10) -> float:
        """Benchmark ONNX model inference time"""
        try:
            # Create ONNX runtime session
            session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
            test_texts = [f"This is test sentence {i} for benchmarking." for i in range(num_samples)]
            
            start_time = time.time()
            
            for text in test_texts:
                inputs = tokenizer(text, return_tensors="np", padding=True, truncation=True)
                
                # Run inference
                ort_inputs = {
                    'input_ids': inputs['input_ids'],
                    'attention_mask': inputs['attention_mask']
                }
                outputs = session.run(None, ort_inputs)
            
            total_time = time.time() - start_time
            avg_time_ms = (total_time / num_samples) * 1000
            
            return avg_time_ms
            
        except Exception as e:
            logger.warning(f"ONNX benchmarking failed: {e}")
            return 100.0  # Default fallback
    
    def _save_optimization_metadata(self, model_name: str, metadata: Dict[str, Any]) -> None:
        """Save optimization metadata to file"""
        try:
            metadata_path = self.cache_dir / f"{model_name}_optimization_metadata.json"
            
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Optimization metadata saved to {metadata_path}")
            
        except Exception as e:
            logger.warning(f"Could not save optimization metadata: {e}")
    
    def _update_optimization_stats(self, metadata: Dict[str, Any]) -> None:
        """Update global optimization statistics"""
        try:
            self.optimization_stats["models_optimized"] += 1
            
            if "size_reduction_percent" in metadata:
                self.optimization_stats["total_size_reduction"] += metadata["size_reduction_percent"]
            
            if "speedup_factor" in metadata:
                current_avg = self.optimization_stats["average_speedup"]
                new_speedup = metadata["speedup_factor"]
                models_count = self.optimization_stats["models_optimized"]
                
                # Update running average
                self.optimization_stats["average_speedup"] = (
                    (current_avg * (models_count - 1) + new_speedup) / models_count
                )
            
            self.optimization_stats["optimization_history"].append(metadata)
            
        except Exception as e:
            logger.warning(f"Could not update optimization stats: {e}")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get current optimization statistics"""
        stats = self.optimization_stats.copy()
        
        if stats["models_optimized"] > 0:
            stats["average_size_reduction"] = stats["total_size_reduction"] / stats["models_optimized"]
        else:
            stats["average_size_reduction"] = 0.0
        
        return stats
    
    def list_optimized_models(self) -> Dict[str, Any]:
        """List all optimized models with their statistics"""
        optimized_models = {}
        
        try:
            for metadata_file in self.cache_dir.glob("*_optimization_metadata.json"):
                try:
                    import json
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    model_name = metadata.get("model_name", "unknown")
                    optimized_models[model_name] = metadata
                    
                except Exception as e:
                    logger.warning(f"Could not load metadata from {metadata_file}: {e}")
        
        except Exception as e:
            logger.error(f"Could not list optimized models: {e}")
        
        return optimized_models
    
    def cleanup_cache(self, keep_recent: int = 5) -> Dict[str, Any]:
        """Clean up optimization cache, keeping only recent models"""
        try:
            logger.info(f"Cleaning up optimization cache, keeping {keep_recent} recent models...")
            
            # Get all optimization metadata files
            metadata_files = list(self.cache_dir.glob("*_optimization_metadata.json"))
            
            if len(metadata_files) <= keep_recent:
                logger.info(f"Only {len(metadata_files)} models found, no cleanup needed")
                return {"cleaned": 0, "kept": len(metadata_files)}
            
            # Sort by modification time (most recent first)
            metadata_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep recent files, remove old ones
            files_to_remove = metadata_files[keep_recent:]
            cleaned_count = 0
            
            for metadata_file in files_to_remove:
                try:
                    # Load metadata to get associated model paths
                    import json
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Remove associated model files
                    if "optimized_path" in metadata:
                        optimized_path = Path(metadata["optimized_path"])
                        if optimized_path.exists():
                            import shutil
                            shutil.rmtree(optimized_path)
                    
                    if "onnx_path" in metadata:
                        onnx_path = Path(metadata["onnx_path"])
                        if onnx_path.exists():
                            import shutil
                            shutil.rmtree(onnx_path)
                    
                    # Remove metadata file
                    metadata_file.unlink()
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.warning(f"Could not clean up {metadata_file}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old optimized models")
            return {"cleaned": cleaned_count, "kept": keep_recent}
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            return {"error": str(e)}