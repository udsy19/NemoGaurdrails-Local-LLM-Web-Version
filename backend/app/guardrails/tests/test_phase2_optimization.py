"""
Test Suite for Phase 2 Optimization Components
Validates model optimization, caching, memory management, and performance monitoring
"""

import asyncio
import logging
import sys
import os
import time
import tempfile
from typing import Dict, Any
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from guardrails.optimization.model_optimizer import ModelOptimizer
from guardrails.optimization.cache_manager import IntelligentCacheManager
from guardrails.optimization.memory_manager import MemoryManager
from guardrails.optimization.performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TestPhase2Optimization:
    """Test suite for Phase 2 optimization components"""
    
    def __init__(self):
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": {}
        }
        
        # Test data
        self.test_text_samples = [
            "This is a normal message with no issues.",
            "My email is test@example.com and phone is 555-1234.",
            "Visit https://example.com for more information.",
            "Hello, this is a test message for performance benchmarking.",
            "Let's see how well the caching system works with repeated content."
        ]
    
    async def test_model_optimizer_initialization(self) -> Dict[str, Any]:
        """Test 1: Model optimizer initialization"""
        logger.info("Testing model optimizer initialization...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                optimizer = ModelOptimizer(cache_dir=temp_dir)
                
                assert optimizer.cache_dir.exists(), "Cache directory should exist"
                assert optimizer.optimization_stats["models_optimized"] == 0, "Initial stats should be zero"
                
                # Test statistics retrieval
                stats = optimizer.get_optimization_stats()
                assert "models_optimized" in stats, "Stats should contain models_optimized"
                assert "average_size_reduction" in stats, "Stats should contain average_size_reduction"
                
                logger.info("✅ Model optimizer initialization test passed")
                return {"status": "passed", "details": "Model optimizer initialized successfully"}
                
        except Exception as e:
            logger.error(f"❌ Model optimizer initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_cache_manager_basic_operations(self) -> Dict[str, Any]:
        """Test 2: Cache manager basic operations"""
        logger.info("Testing cache manager basic operations...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                cache_manager = IntelligentCacheManager(cache_dir=temp_dir)
                
                # Test basic set/get operations
                test_key = "test_key_1"
                test_value = {"result": "blocked", "confidence": 0.95}
                
                # Set cache entry
                success = await cache_manager.set(test_key, test_value, "response")
                assert success, "Cache set should succeed"
                
                # Get cache entry
                retrieved_value = await cache_manager.get(test_key, "response")
                assert retrieved_value == test_value, "Retrieved value should match original"
                
                # Test cache miss
                missing_value = await cache_manager.get("nonexistent_key", "response", "default")
                assert missing_value == "default", "Missing key should return default"
                
                # Test cache deletion
                deleted = await cache_manager.delete(test_key, "response")
                assert deleted, "Cache deletion should succeed"
                
                # Verify deletion
                deleted_value = await cache_manager.get(test_key, "response")
                assert deleted_value is None, "Deleted key should return None"
                
                logger.info("✅ Cache manager basic operations test passed")
                return {"status": "passed", "details": "All cache operations successful"}
                
        except Exception as e:
            logger.error(f"❌ Cache manager basic operations test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_cache_manager_response_caching(self) -> Dict[str, Any]:
        """Test 3: Cache manager response caching"""
        logger.info("Testing cache manager response caching...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                cache_manager = IntelligentCacheManager(cache_dir=temp_dir)
                
                # Test response caching
                test_text = "This is a test message for caching"
                test_result = {
                    "blocked": False,
                    "confidence": 0.85,
                    "blocking_reasons": [],
                    "model_name": "test_ensemble"
                }
                
                # Cache response
                cached = await cache_manager.cache_response(test_text, test_result, "test_model")
                assert cached, "Response caching should succeed"
                
                # Retrieve cached response
                retrieved_result = await cache_manager.get_cached_response(test_text, "test_model")
                assert retrieved_result == test_result, "Retrieved response should match original"
                
                # Test cache miss with different text
                missing_result = await cache_manager.get_cached_response("different text", "test_model")
                assert missing_result is None, "Different text should not have cached result"
                
                logger.info("✅ Cache manager response caching test passed")
                return {"status": "passed", "details": "Response caching working correctly"}
                
        except Exception as e:
            logger.error(f"❌ Cache manager response caching test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_memory_manager_initialization(self) -> Dict[str, Any]:
        """Test 4: Memory manager initialization"""
        logger.info("Testing memory manager initialization...")
        
        try:
            memory_manager = MemoryManager(max_memory_mb=2048)
            
            # Test memory stats retrieval
            stats = memory_manager.get_memory_stats()
            assert stats.total_memory_mb > 0, "Total memory should be positive"
            assert stats.process_memory_mb > 0, "Process memory should be positive"
            assert stats.timestamp > 0, "Timestamp should be set"
            
            # Test memory report
            report = memory_manager.get_memory_report()
            assert "current_memory" in report, "Report should contain current memory"
            assert "statistics" in report, "Report should contain statistics"
            assert "configuration" in report, "Report should contain configuration"
            
            logger.info("✅ Memory manager initialization test passed")
            return {"status": "passed", "details": "Memory manager initialized successfully"}
            
        except Exception as e:
            logger.error(f"❌ Memory manager initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_memory_manager_cleanup(self) -> Dict[str, Any]:
        """Test 5: Memory manager cleanup"""
        logger.info("Testing memory manager cleanup...")
        
        try:
            memory_manager = MemoryManager()
            
            # Test cleanup without force (should not trigger)
            cleanup_result = await memory_manager.cleanup_memory(force=False)
            assert "cleanup_triggered" in cleanup_result, "Cleanup result should indicate if triggered"
            
            # Test forced cleanup
            force_cleanup_result = await memory_manager.cleanup_memory(force=True)
            assert force_cleanup_result["cleanup_triggered"], "Forced cleanup should trigger"
            assert "actions_taken" in force_cleanup_result, "Should list actions taken"
            
            # Test GC optimization
            gc_result = memory_manager.optimize_gc()
            assert "optimization_applied" in gc_result, "GC optimization should report if applied"
            
            logger.info("✅ Memory manager cleanup test passed")
            return {"status": "passed", "details": "Memory cleanup working correctly"}
            
        except Exception as e:
            logger.error(f"❌ Memory manager cleanup test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_performance_monitor_initialization(self) -> Dict[str, Any]:
        """Test 6: Performance monitor initialization"""
        logger.info("Testing performance monitor initialization...")
        
        try:
            performance_monitor = PerformanceMonitor()
            
            # Test metric recording
            performance_monitor.record_metric("test_metric", 42.5, "ms")
            
            # Test request result recording
            performance_monitor.record_request_result(True, 100.0, 50.0)
            
            # Test performance summary
            summary = performance_monitor.get_performance_summary()
            assert "counters" in summary, "Summary should contain counters"
            assert "recent_metrics" in summary, "Summary should contain recent metrics"
            assert summary["counters"]["total_requests"] > 0, "Should have recorded requests"
            
            logger.info("✅ Performance monitor initialization test passed")
            return {"status": "passed", "details": "Performance monitor working correctly"}
            
        except Exception as e:
            logger.error(f"❌ Performance monitor initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_performance_monitor_benchmarking(self) -> Dict[str, Any]:
        """Test 7: Performance monitor benchmarking"""
        logger.info("Testing performance monitor benchmarking...")
        
        try:
            performance_monitor = PerformanceMonitor()
            
            # Define a simple benchmark function
            async def sample_benchmark(duration_ms: int = 10):
                """Sample benchmark function"""
                await asyncio.sleep(duration_ms / 1000.0)
                return {"result": "success"}
            
            # Run benchmark
            benchmark_result = await performance_monitor.run_benchmark(
                "sample_benchmark",
                sample_benchmark,
                num_iterations=5,
                warmup_iterations=2,
                duration_ms=10
            )
            
            # Validate benchmark result
            assert benchmark_result.benchmark_name == "sample_benchmark"
            assert benchmark_result.success_rate > 0.8, "Success rate should be high"
            assert benchmark_result.throughput_ops_per_second > 0, "Throughput should be positive"
            assert len(benchmark_result.metrics) > 0, "Should have detailed metrics"
            
            logger.info("✅ Performance monitor benchmarking test passed")
            return {"status": "passed", "details": "Benchmarking working correctly"}
            
        except Exception as e:
            logger.error(f"❌ Performance monitor benchmarking test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_performance_monitor_context_manager(self) -> Dict[str, Any]:
        """Test 8: Performance monitor context manager"""
        logger.info("Testing performance monitor context manager...")
        
        try:
            performance_monitor = PerformanceMonitor()
            
            # Test successful operation measurement
            with performance_monitor.measure_performance("test_operation"):
                # Simulate some work
                await asyncio.sleep(0.01)
            
            # Test failed operation measurement
            try:
                with performance_monitor.measure_performance("failing_operation"):
                    # Simulate some work then fail
                    await asyncio.sleep(0.01)
                    raise ValueError("Test error")
            except ValueError:
                pass  # Expected
            
            # Check that metrics were recorded
            summary = performance_monitor.get_performance_summary()
            assert summary["counters"]["total_requests"] >= 2, "Should have recorded both operations"
            assert summary["counters"]["failed_requests"] >= 1, "Should have recorded failed operation"
            
            logger.info("✅ Performance monitor context manager test passed")
            return {"status": "passed", "details": "Context manager working correctly"}
            
        except Exception as e:
            logger.error(f"❌ Performance monitor context manager test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_integrated_optimization_workflow(self) -> Dict[str, Any]:
        """Test 9: Integrated optimization workflow"""
        logger.info("Testing integrated optimization workflow...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Initialize all components
                cache_manager = IntelligentCacheManager(cache_dir=temp_dir)
                memory_manager = MemoryManager()
                performance_monitor = PerformanceMonitor()
                
                # Simulate a detection workflow with optimization
                for i, text in enumerate(self.test_text_samples):
                    with performance_monitor.measure_performance(f"detection_{i}"):
                        # Check cache first
                        cached_result = await cache_manager.get_cached_response(text, "test_ensemble")
                        
                        if cached_result:
                            # Cache hit
                            result = cached_result
                        else:
                            # Cache miss - simulate detection
                            await asyncio.sleep(0.005)  # Simulate processing time
                            result = {
                                "blocked": False,
                                "confidence": 0.8,
                                "blocking_reasons": [],
                                "model_name": "test_ensemble"
                            }
                            
                            # Cache the result
                            await cache_manager.cache_response(text, result, "test_ensemble")
                        
                        # Record successful processing
                        performance_monitor.record_request_result(True, 5.0, 10.0)
                
                # Test repeated requests (should hit cache)
                for text in self.test_text_samples[:2]:
                    cached_result = await cache_manager.get_cached_response(text, "test_ensemble")
                    assert cached_result is not None, "Should hit cache on repeated request"
                
                # Get performance summary
                summary = performance_monitor.get_performance_summary()
                assert summary["counters"]["total_requests"] >= len(self.test_text_samples), "Should have processed all samples"
                
                # Get cache statistics
                cache_stats = await cache_manager.get_cache_stats()
                assert cache_stats["hit_rate"] > 0, "Should have some cache hits"
                
                # Test memory cleanup
                cleanup_result = await memory_manager.cleanup_memory(force=True)
                assert cleanup_result["cleanup_triggered"], "Should trigger cleanup"
                
                logger.info("✅ Integrated optimization workflow test passed")
                return {"status": "passed", "details": "Integrated workflow working correctly"}
                
        except Exception as e:
            logger.error(f"❌ Integrated optimization workflow test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_cache_performance_under_load(self) -> Dict[str, Any]:
        """Test 10: Cache performance under load"""
        logger.info("Testing cache performance under load...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                cache_manager = IntelligentCacheManager(cache_dir=temp_dir, max_memory_mb=64)
                
                # Generate test data
                test_data = []
                for i in range(100):
                    test_data.append({
                        "key": f"test_key_{i}",
                        "value": {"result": "blocked" if i % 2 == 0 else "allowed", "confidence": 0.8 + (i % 20) / 100}
                    })
                
                # Cache all data
                start_time = time.time()
                for data in test_data:
                    await cache_manager.set(data["key"], data["value"], "response")
                cache_time = time.time() - start_time
                
                # Retrieve all data
                start_time = time.time()
                retrieved_count = 0
                for data in test_data:
                    retrieved_value = await cache_manager.get(data["key"], "response")
                    if retrieved_value == data["value"]:
                        retrieved_count += 1
                retrieval_time = time.time() - start_time
                
                # Validate results
                assert retrieved_count == len(test_data), "Should retrieve all cached data"
                assert cache_time < 1.0, "Caching should be fast"
                assert retrieval_time < 0.5, "Retrieval should be fast"
                
                # Test cache statistics
                stats = await cache_manager.get_cache_stats()
                assert stats["hit_rate"] > 99.0, "Hit rate should be very high"
                
                logger.info("✅ Cache performance under load test passed")
                return {"status": "passed", "details": f"Cached {len(test_data)} items in {cache_time:.3f}s, retrieved in {retrieval_time:.3f}s"}
                
        except Exception as e:
            logger.error(f"❌ Cache performance under load test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 2 optimization tests"""
        logger.info("Starting Phase 2 optimization test suite...")
        
        # List of test methods
        test_methods = [
            ("model_optimizer_init", self.test_model_optimizer_initialization),
            ("cache_basic_operations", self.test_cache_manager_basic_operations),
            ("cache_response_caching", self.test_cache_manager_response_caching),
            ("memory_manager_init", self.test_memory_manager_initialization),
            ("memory_manager_cleanup", self.test_memory_manager_cleanup),
            ("performance_monitor_init", self.test_performance_monitor_initialization),
            ("performance_monitor_benchmarking", self.test_performance_monitor_benchmarking),
            ("performance_monitor_context", self.test_performance_monitor_context_manager),
            ("integrated_workflow", self.test_integrated_optimization_workflow),
            ("cache_performance_load", self.test_cache_performance_under_load)
        ]
        
        # Run each test
        for test_name, test_method in test_methods:
            self.test_results["total_tests"] += 1
            
            try:
                result = await test_method()
                self.test_results["test_details"][test_name] = result
                
                if result["status"] == "passed":
                    self.test_results["passed_tests"] += 1
                else:
                    self.test_results["failed_tests"] += 1
                    
            except Exception as e:
                self.test_results["failed_tests"] += 1
                self.test_results["test_details"][test_name] = {
                    "status": "failed",
                    "error": f"Test execution error: {str(e)}"
                }
        
        # Summary
        success_rate = (self.test_results["passed_tests"] / self.test_results["total_tests"]) * 100
        self.test_results["success_rate"] = success_rate
        
        logger.info(f"Phase 2 optimization test suite completed: {self.test_results['passed_tests']}/{self.test_results['total_tests']} tests passed ({success_rate:.1f}%)")
        
        return self.test_results

async def main():
    """Main test runner"""
    logger.info("Phase 2 Optimization Test Suite")
    logger.info("=" * 50)
    
    test_runner = TestPhase2Optimization()
    results = await test_runner.run_all_tests()
    
    print("\n" + "=" * 50)
    print("PHASE 2 OPTIMIZATION TEST RESULTS")
    print("=" * 50)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print("=" * 50)
    
    # Print detailed results
    for test_name, test_result in results["test_details"].items():
        status_symbol = "✅" if test_result["status"] == "passed" else "❌"
        print(f"{status_symbol} {test_name}: {test_result['status']}")
        if "details" in test_result:
            print(f"   {test_result['details']}")
        if "error" in test_result:
            print(f"   Error: {test_result['error']}")
    
    print("\n" + "=" * 50)
    
    if results["success_rate"] >= 80.0:
        print("🎉 Phase 2 optimization implementation: SUCCESS")
        return 0
    else:
        print("❌ Phase 2 optimization implementation: NEEDS WORK")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test suite error: {e}")
        sys.exit(1)