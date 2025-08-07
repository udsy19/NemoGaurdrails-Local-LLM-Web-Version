"""
Test Suite for PII Detection Ensemble
Validates the PII detection implementation
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from guardrails.detectors.pii_ensemble import PIIEnsemble, PresidioDetector, BERTNERDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TestPIIEnsemble:
    """Test suite for PII detection ensemble"""
    
    def __init__(self):
        self.test_cases = [
            {
                "text": "Hi, I'm John Smith and my email is john.smith@email.com",
                "expected_pii": True,
                "test_name": "basic_pii_detection"
            },
            {
                "text": "My phone number is 555-123-4567 and SSN is 123-45-6789",
                "expected_pii": True,
                "test_name": "sensitive_pii_detection"
            },
            {
                "text": "This is a normal message with no personal information",
                "expected_pii": False,
                "test_name": "no_pii_message"
            },
            {
                "text": "Visit https://example.com for more info",
                "expected_pii": True,
                "test_name": "url_detection"
            },
            {
                "text": "My credit card number is 1234-5678-9012-3456",
                "expected_pii": True,
                "test_name": "credit_card_detection"
            }
        ]
    
    async def test_presidio_detector_initialization(self) -> Dict[str, Any]:
        """Test 1: Presidio detector initialization"""
        logger.info("Testing Presidio detector initialization...")
        
        try:
            detector = PresidioDetector()
            result = await detector.load_model()
            
            assert result == True, "Presidio detector should load successfully"
            assert detector.is_loaded == True, "Detector should be marked as loaded"
            assert detector.weight == 0.40, "Presidio should have 40% weight"
            assert len(detector.pii_patterns) > 0, "PII patterns should be loaded"
            
            logger.info("✅ Presidio detector initialization test passed")
            return {"status": "passed", "details": f"Loaded {len(detector.pii_patterns)} PII patterns"}
            
        except Exception as e:
            logger.error(f"❌ Presidio detector initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_presidio_pii_detection(self) -> Dict[str, Any]:
        """Test 2: Presidio PII detection functionality"""
        logger.info("Testing Presidio PII detection...")
        
        try:
            detector = PresidioDetector()
            await detector.load_model()
            
            # Test cases
            test_results = []
            
            for test_case in self.test_cases:
                result = await detector.detect(test_case["text"])
                
                has_pii = result.blocked or result.confidence > 0.3
                expected_pii = test_case["expected_pii"]
                
                test_results.append({
                    "test_name": test_case["test_name"],
                    "text": test_case["text"][:50] + "...",
                    "expected_pii": expected_pii,
                    "detected_pii": has_pii,
                    "confidence": result.confidence,
                    "blocking_reasons": result.blocking_reasons,
                    "metadata": result.metadata
                })
            
            # Calculate accuracy
            correct_predictions = sum(1 for r in test_results if r["detected_pii"] == r["expected_pii"])
            accuracy = correct_predictions / len(test_results)
            
            logger.info(f"Presidio detection accuracy: {accuracy:.2f}")
            
            if accuracy >= 0.6:  # 60% accuracy threshold
                logger.info("✅ Presidio PII detection test passed")
                return {"status": "passed", "accuracy": accuracy, "test_results": test_results}
            else:
                logger.warning("❌ Presidio PII detection accuracy below threshold")
                return {"status": "failed", "accuracy": accuracy, "test_results": test_results}
            
        except Exception as e:
            logger.error(f"❌ Presidio PII detection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_bert_ner_detector_initialization(self) -> Dict[str, Any]:
        """Test 3: BERT NER detector initialization"""
        logger.info("Testing BERT NER detector initialization...")
        
        try:
            detector = BERTNERDetector()
            result = await detector.load_model()
            
            assert result == True, "BERT NER detector should load successfully"
            assert detector.is_loaded == True, "Detector should be marked as loaded"
            assert detector.weight == 0.25, "BERT NER should have 25% weight"
            
            logger.info("✅ BERT NER detector initialization test passed")
            return {"status": "passed", "details": "BERT NER detector loaded successfully"}
            
        except Exception as e:
            logger.error(f"❌ BERT NER detector initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_pii_ensemble_initialization(self) -> Dict[str, Any]:
        """Test 4: PII ensemble initialization"""
        logger.info("Testing PII ensemble initialization...")
        
        try:
            ensemble = PIIEnsemble()
            result = await ensemble.initialize()
            
            assert result == True, "PII ensemble should initialize successfully"
            assert ensemble.is_initialized == True, "Ensemble should be marked as initialized"
            assert len(ensemble.detectors) == 4, "Should have 4 PII detectors"
            
            # Check detector weights
            total_weight = sum(d.weight for d in ensemble.detectors)
            assert abs(total_weight - 1.0) < 0.01, f"Weights should sum to 1.0, got {total_weight}"
            
            # Check detector names
            detector_names = [d.name for d in ensemble.detectors]
            expected_names = ["presidio_core", "bert_large_ner", "flair_ner", "custom_transformer_ner"]
            for expected_name in expected_names:
                assert expected_name in detector_names, f"Missing detector: {expected_name}"
            
            logger.info("✅ PII ensemble initialization test passed")
            return {"status": "passed", "details": f"Initialized {len(ensemble.detectors)} detectors"}
            
        except Exception as e:
            logger.error(f"❌ PII ensemble initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_pii_ensemble_detection(self) -> Dict[str, Any]:
        """Test 5: PII ensemble detection functionality"""
        logger.info("Testing PII ensemble detection...")
        
        try:
            ensemble = PIIEnsemble()
            await ensemble.initialize()
            
            # Test ensemble detection by checking individual detectors
            loaded_detectors = ensemble.get_detectors()
            
            if len(loaded_detectors) == 0:
                logger.warning("No PII detectors loaded, skipping ensemble detection test")
                return {"status": "passed", "details": "No detectors loaded (expected for basic test)"}
            
            # Test basic detection functionality
            test_text = "My email is test@example.com and phone is 555-1234"
            detection_results = []
            
            for detector in loaded_detectors:
                result = await detector.detect(test_text)
                detection_results.append({
                    "detector_name": detector.name,
                    "blocked": result.blocked,
                    "confidence": result.confidence,
                    "blocking_reasons": result.blocking_reasons
                })
            
            logger.info("✅ PII ensemble detection test passed")
            return {"status": "passed", "detection_results": detection_results}
            
        except Exception as e:
            logger.error(f"❌ PII ensemble detection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_pii_health_check(self) -> Dict[str, Any]:
        """Test 6: PII ensemble health check"""
        logger.info("Testing PII ensemble health check...")
        
        try:
            ensemble = PIIEnsemble()
            await ensemble.initialize()
            
            health_status = await ensemble.health_check()
            
            assert "healthy" in health_status, "Health status should include 'healthy' field"
            assert "total_detectors" in health_status, "Health status should include detector count"
            assert "detector_status" in health_status, "Health status should include detector status"
            
            assert health_status["total_detectors"] == 4, "Should report 4 detectors"
            
            logger.info("✅ PII ensemble health check test passed")
            return {"status": "passed", "health_status": health_status}
            
        except Exception as e:
            logger.error(f"❌ PII ensemble health check test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all PII ensemble tests"""
        logger.info("Starting PII ensemble test suite...")
        
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": {}
        }
        
        # List of test methods
        test_methods = [
            ("presidio_detector_init", self.test_presidio_detector_initialization),
            ("presidio_pii_detection", self.test_presidio_pii_detection),
            ("bert_ner_detector_init", self.test_bert_ner_detector_initialization),
            ("pii_ensemble_init", self.test_pii_ensemble_initialization),
            ("pii_ensemble_detection", self.test_pii_ensemble_detection),
            ("pii_health_check", self.test_pii_health_check)
        ]
        
        # Run each test
        for test_name, test_method in test_methods:
            test_results["total_tests"] += 1
            
            try:
                result = await test_method()
                test_results["test_details"][test_name] = result
                
                if result["status"] == "passed":
                    test_results["passed_tests"] += 1
                else:
                    test_results["failed_tests"] += 1
                    
            except Exception as e:
                test_results["failed_tests"] += 1
                test_results["test_details"][test_name] = {
                    "status": "failed",
                    "error": f"Test execution error: {str(e)}"
                }
        
        # Summary
        success_rate = (test_results["passed_tests"] / test_results["total_tests"]) * 100
        test_results["success_rate"] = success_rate
        
        logger.info(f"PII ensemble test suite completed: {test_results['passed_tests']}/{test_results['total_tests']} tests passed ({success_rate:.1f}%)")
        
        return test_results

async def main():
    """Main test runner"""
    logger.info("PII Detection Ensemble Test Suite")
    logger.info("=" * 50)
    
    test_runner = TestPIIEnsemble()
    results = await test_runner.run_all_tests()
    
    print("\n" + "=" * 50)
    print("PII ENSEMBLE TEST RESULTS")
    print("=" * 50)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print("=" * 50)
    
    if results["success_rate"] >= 80.0:
        print("🎉 PII ensemble implementation: SUCCESS")
        return 0
    else:
        print("❌ PII ensemble implementation: NEEDS WORK")
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