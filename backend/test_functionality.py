#!/usr/bin/env python3
"""
Standalone functionality test for Phase 1 and Phase 2 components
Tests core functionality without complex imports
"""

import sys
import os
import asyncio
import tempfile
import time
import logging

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_phase1_basic():
    """Test basic Phase 1 functionality"""
    print("🔍 Testing Phase 1 - Core Ensemble Framework")
    
    try:
        # Test 1: Base ensemble framework
        from guardrails.ensemble.base_ensemble import EnsembleFramework, DetectionResult, DetectionStage
        
        framework = EnsembleFramework()
        assert framework.high_confidence_threshold == 0.92
        assert framework.medium_confidence_threshold == 0.75
        print("✅ Base ensemble framework initialized")
        
        # Test 2: Detection result creation
        result = DetectionResult(
            blocked=False,
            confidence=0.85,
            blocking_reasons=[],
            model_name="test_model",
            processing_time_ms=10.5,
            metadata={"test": "data"},
            stage=DetectionStage.PRIMARY_ENSEMBLE
        )
        assert result.confidence == 0.85
        assert result.stage == DetectionStage.PRIMARY_ENSEMBLE
        print("✅ Detection result creation working")
        
        # Test 3: PII ensemble basic functionality
        from guardrails.detectors.pii_ensemble import PresidioDetector
        
        pii_detector = PresidioDetector()
        assert pii_detector.name == "presidio_core"
        assert pii_detector.weight == 0.40
        print("✅ PII detector initialization working")
        
        # Test 4: Load PII detector
        loaded = await pii_detector.load_model()
        assert loaded == True
        assert pii_detector.is_loaded == True
        print("✅ PII detector model loading working")
        
        # Test 5: PII detection
        test_text = "My email is john@example.com and phone is 555-1234"
        detection_result = await pii_detector.detect(test_text)
        assert detection_result.model_name == "presidio_core"
        assert detection_result.confidence > 0.0
        print("✅ PII detection working")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 1 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_phase2_basic():
    """Test basic Phase 2 functionality"""
    print("\n🔍 Testing Phase 2 - Optimization Framework")
    
    try:
        # Test 1: Cache Manager
        from guardrails.optimization.cache_manager import IntelligentCacheManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = IntelligentCacheManager(cache_dir=temp_dir)
            
            # Test cache operations
            success = await cache_manager.set("test_key", {"result": "success"}, "response")
            assert success == True
            
            retrieved = await cache_manager.get("test_key", "response")
            assert retrieved == {"result": "success"}
            print("✅ Cache manager working")
        
        # Test 2: Memory Manager
        from guardrails.optimization.memory_manager import MemoryManager
        
        memory_manager = MemoryManager()
        stats = memory_manager.get_memory_stats()
        assert stats.total_memory_mb > 0
        assert stats.process_memory_mb > 0
        print("✅ Memory manager working")
        
        # Test 3: Performance Monitor
        from guardrails.optimization.performance_monitor import PerformanceMonitor
        
        perf_monitor = PerformanceMonitor()
        perf_monitor.record_metric("test_metric", 42.5, "ms")
        
        summary = perf_monitor.get_performance_summary()
        assert "recent_metrics" in summary
        print("✅ Performance monitor working")
        
        # Test 4: Model Optimizer (basic)
        from guardrails.optimization.model_optimizer import ModelOptimizer
        
        optimizer = ModelOptimizer()
        stats = optimizer.get_optimization_stats()
        assert "models_optimized" in stats
        print("✅ Model optimizer working")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 2 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration():
    """Test integration between Phase 1 and Phase 2"""
    print("\n🔍 Testing Integration - Phase 1 + Phase 2")
    
    try:
        # Test integrated workflow
        from guardrails.optimization.cache_manager import IntelligentCacheManager
        from guardrails.optimization.performance_monitor import PerformanceMonitor
        from guardrails.detectors.pii_ensemble import PresidioDetector
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize components
            cache_manager = IntelligentCacheManager(cache_dir=temp_dir)
            perf_monitor = PerformanceMonitor()
            pii_detector = PresidioDetector()
            
            # Load detector
            await pii_detector.load_model()
            
            # Test workflow
            test_text = "Contact me at user@example.com"
            
            # Check cache first
            cached_result = await cache_manager.get_cached_response(test_text, "pii_detector")
            
            if cached_result is None:
                # Cache miss - run detection
                with perf_monitor.measure_performance("pii_detection"):
                    detection_result = await pii_detector.detect(test_text)
                
                # Cache the result
                await cache_manager.cache_response(test_text, {
                    "blocked": detection_result.blocked,
                    "confidence": detection_result.confidence,
                    "blocking_reasons": detection_result.blocking_reasons
                }, "pii_detector")
                
                result = detection_result
            else:
                # Cache hit
                result = cached_result
            
            # Verify results
            assert result is not None
            
            # Test cache hit on second request
            cached_result = await cache_manager.get_cached_response(test_text, "pii_detector")
            assert cached_result is not None
            
            # Check performance stats
            summary = perf_monitor.get_performance_summary()
            assert summary["counters"]["total_requests"] > 0
            
            print("✅ Integration working - Phase 1 + Phase 2 components work together")
            
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all functionality tests"""
    print("🚀 Enterprise AI Safety System - Functionality Test")
    print("=" * 60)
    
    start_time = time.time()
    
    # Test Phase 1
    phase1_result = await test_phase1_basic()
    
    # Test Phase 2
    phase2_result = await test_phase2_basic()
    
    # Test Integration
    integration_result = await test_integration()
    
    # Results
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📊 FUNCTIONALITY TEST RESULTS")
    print("=" * 60)
    
    print(f"Phase 1 (Core Framework): {'✅ PASS' if phase1_result else '❌ FAIL'}")
    print(f"Phase 2 (Optimization): {'✅ PASS' if phase2_result else '❌ FAIL'}")
    print(f"Integration Test: {'✅ PASS' if integration_result else '❌ FAIL'}")
    
    overall_success = phase1_result and phase2_result and integration_result
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    print(f"Total Test Time: {total_time:.2f} seconds")
    
    if overall_success:
        print("\n🎉 Enterprise AI Safety System is fully functional!")
        print("✅ Phase 1: Core ensemble framework operational")
        print("✅ Phase 2: Optimization framework operational")
        print("✅ Integration: Components work together seamlessly")
    else:
        print("\n⚠️  Some components need attention")
    
    print("=" * 60)
    return 0 if overall_success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest suite error: {e}")
        sys.exit(1)