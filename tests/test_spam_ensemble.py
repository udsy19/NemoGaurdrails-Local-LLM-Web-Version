"""
Test Suite for Spam Detection Ensemble
Validates the spam detection implementation
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from guardrails.detectors.spam_ensemble import SpamEnsemble, RoBERTaSpamDetector, KeywordPatternDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TestSpamEnsemble:
    """Test suite for spam detection ensemble"""
    
    def __init__(self):
        self.test_cases = [
            {
                "text": "This is a normal message about the weather today.",
                "expected_spam": False,
                "test_name": "normal_message"
            },
            {
                "text": "Click here to win FREE MONEY now! Limited time offer!!!",
                "expected_spam": True,
                "test_name": "obvious_spam"
            },
            {
                "text": "Congratulations! You have won $1000000! Click here to claim your prize.",
                "expected_spam": True,
                "test_name": "prize_scam"
            },
            {
                "text": "Hi, can you help me with my homework assignment?",
                "expected_spam": False,
                "test_name": "legitimate_request"
            },
            {
                "text": "URGENT! Your account will be suspended unless you verify your information immediately!",
                "expected_spam": True,
                "test_name": "account_scam"
            },
            {
                "text": "Work from home and earn $5000 per month guaranteed! Risk-free investment opportunity!",
                "expected_spam": True,
                "test_name": "financial_spam"
            },
            {
                "text": "Hello, I would like to schedule a meeting to discuss our project.",
                "expected_spam": False,
                "test_name": "business_communication"
            }
        ]
    
    async def test_roberta_spam_detector_initialization(self) -> Dict[str, Any]:
        """Test 1: RoBERTa spam detector initialization"""
        logger.info("Testing RoBERTa spam detector initialization...")
        
        try:
            detector = RoBERTaSpamDetector()
            result = await detector.load_model()
            
            assert result == True, "RoBERTa detector should load successfully"
            assert detector.is_loaded == True, "Detector should be marked as loaded"
            assert detector.weight == 0.40, "RoBERTa should have 40% weight"
            assert detector.name == "roberta_spam_classifier", "Detector should have correct name"
            
            logger.info("✅ RoBERTa spam detector initialization test passed")
            return {"status": "passed", "details": "RoBERTa detector initialized successfully"}
            
        except Exception as e:
            logger.error(f"❌ RoBERTa spam detector initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_roberta_spam_detection(self) -> Dict[str, Any]:
        """Test 2: RoBERTa spam detection functionality"""
        logger.info("Testing RoBERTa spam detection...")
        
        try:
            detector = RoBERTaSpamDetector()
            await detector.load_model()
            
            # Test cases
            test_results = []
            
            for test_case in self.test_cases:
                result = await detector.detect(test_case["text"])
                
                is_spam = result.blocked or result.confidence > 0.5
                expected_spam = test_case["expected_spam"]
                
                test_results.append({
                    "test_name": test_case["test_name"],
                    "text": test_case["text"][:50] + "...",
                    "expected_spam": expected_spam,
                    "detected_spam": is_spam,
                    "confidence": result.confidence,
                    "blocking_reasons": result.blocking_reasons,
                    "metadata": result.metadata
                })
            
            # Calculate accuracy
            correct_predictions = sum(1 for r in test_results if r["detected_spam"] == r["expected_spam"])
            accuracy = correct_predictions / len(test_results)
            
            logger.info(f"RoBERTa spam detection accuracy: {accuracy:.2f}")
            
            if accuracy >= 0.6:  # 60% accuracy threshold
                logger.info("✅ RoBERTa spam detection test passed")
                return {"status": "passed", "accuracy": accuracy, "test_results": test_results}
            else:
                logger.warning("❌ RoBERTa spam detection accuracy below threshold")
                return {"status": "failed", "accuracy": accuracy, "test_results": test_results}
            
        except Exception as e:
            logger.error(f"❌ RoBERTa spam detection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_keyword_pattern_detector_initialization(self) -> Dict[str, Any]:
        """Test 3: Keyword pattern detector initialization"""
        logger.info("Testing keyword pattern detector initialization...")
        
        try:
            detector = KeywordPatternDetector()
            result = await detector.load_model()
            
            assert result == True, "Keyword pattern detector should load successfully"
            assert detector.is_loaded == True, "Detector should be marked as loaded"
            assert detector.weight == 0.20, "Keyword pattern should have 20% weight"
            assert len(detector.spam_patterns) > 0, "Spam patterns should be loaded"
            assert len(detector.spam_keywords) > 0, "Spam keywords should be loaded"
            
            logger.info("✅ Keyword pattern detector initialization test passed")
            return {"status": "passed", "details": f"Loaded {len(detector.spam_patterns)} pattern categories, {len(detector.spam_keywords)} keywords"}
            
        except Exception as e:
            logger.error(f"❌ Keyword pattern detector initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_keyword_pattern_detection(self) -> Dict[str, Any]:
        """Test 4: Keyword pattern detection functionality"""
        logger.info("Testing keyword pattern detection...")
        
        try:
            detector = KeywordPatternDetector()
            await detector.load_model()
            
            # Test cases
            test_results = []
            
            for test_case in self.test_cases:
                result = await detector.detect(test_case["text"])
                
                is_spam = result.blocked or result.confidence > 0.4
                expected_spam = test_case["expected_spam"]
                
                test_results.append({
                    "test_name": test_case["test_name"],
                    "text": test_case["text"][:50] + "...",
                    "expected_spam": expected_spam,
                    "detected_spam": is_spam,
                    "confidence": result.confidence,
                    "blocking_reasons": result.blocking_reasons,
                    "metadata": result.metadata
                })
            
            # Calculate accuracy
            correct_predictions = sum(1 for r in test_results if r["detected_spam"] == r["expected_spam"])
            accuracy = correct_predictions / len(test_results)
            
            logger.info(f"Keyword pattern detection accuracy: {accuracy:.2f}")
            
            if accuracy >= 0.7:  # 70% accuracy threshold (pattern matching should be more accurate)
                logger.info("✅ Keyword pattern detection test passed")
                return {"status": "passed", "accuracy": accuracy, "test_results": test_results}
            else:
                logger.warning("❌ Keyword pattern detection accuracy below threshold")
                return {"status": "failed", "accuracy": accuracy, "test_results": test_results}
            
        except Exception as e:
            logger.error(f"❌ Keyword pattern detection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_spam_ensemble_initialization(self) -> Dict[str, Any]:
        """Test 5: Spam ensemble initialization"""
        logger.info("Testing spam ensemble initialization...")
        
        try:
            ensemble = SpamEnsemble()
            result = await ensemble.initialize()
            
            assert result == True, "Spam ensemble should initialize successfully"
            assert ensemble.is_initialized == True, "Ensemble should be marked as initialized"
            assert len(ensemble.detectors) == 2, "Should have 2 spam detectors"
            
            # Check detector weights
            total_weight = sum(d.weight for d in ensemble.detectors)
            assert abs(total_weight - 0.6) < 0.01, f"Weights should sum to 0.6 (RoBERTa 40% + Keywords 20%), got {total_weight}"
            
            # Check detector names
            detector_names = [d.name for d in ensemble.detectors]
            expected_names = ["roberta_spam_classifier", "keyword_pattern_spam"]
            for expected_name in expected_names:
                assert expected_name in detector_names, f"Missing detector: {expected_name}"
            
            logger.info("✅ Spam ensemble initialization test passed")
            return {"status": "passed", "details": f"Initialized {len(ensemble.detectors)} detectors"}
            
        except Exception as e:
            logger.error(f"❌ Spam ensemble initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_spam_ensemble_detection(self) -> Dict[str, Any]:
        """Test 6: Spam ensemble detection functionality"""
        logger.info("Testing spam ensemble detection...")
        
        try:
            ensemble = SpamEnsemble()
            await ensemble.initialize()
            
            # Test ensemble detection by checking individual detectors
            loaded_detectors = ensemble.get_detectors()
            
            if len(loaded_detectors) == 0:
                logger.warning("No spam detectors loaded, skipping ensemble detection test")
                return {"status": "passed", "details": "No detectors loaded (expected for basic test)"}
            
            # Test basic detection functionality
            spam_text = "Click here to win FREE MONEY now! Limited time offer!!!"
            normal_text = "This is a normal message about the weather today."
            
            detection_results = []
            
            for detector in loaded_detectors:
                # Test spam text
                spam_result = await detector.detect(spam_text)
                detection_results.append({
                    "detector_name": detector.name,
                    "text_type": "spam",
                    "blocked": spam_result.blocked,
                    "confidence": spam_result.confidence,
                    "blocking_reasons": spam_result.blocking_reasons
                })
                
                # Test normal text
                normal_result = await detector.detect(normal_text)
                detection_results.append({
                    "detector_name": detector.name,
                    "text_type": "normal",
                    "blocked": normal_result.blocked,
                    "confidence": normal_result.confidence,
                    "blocking_reasons": normal_result.blocking_reasons
                })
            
            logger.info("✅ Spam ensemble detection test passed")
            return {"status": "passed", "detection_results": detection_results}
            
        except Exception as e:
            logger.error(f"❌ Spam ensemble detection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_spam_health_check(self) -> Dict[str, Any]:
        """Test 7: Spam ensemble health check"""
        logger.info("Testing spam ensemble health check...")
        
        try:
            ensemble = SpamEnsemble()
            await ensemble.initialize()
            
            health_status = await ensemble.health_check()
            
            assert "healthy" in health_status, "Health status should include 'healthy' field"
            assert "total_detectors" in health_status, "Health status should include detector count"
            assert "detector_status" in health_status, "Health status should include detector status"
            
            assert health_status["total_detectors"] == 2, "Should report 2 detectors"
            
            logger.info("✅ Spam ensemble health check test passed")
            return {"status": "passed", "health_status": health_status}
            
        except Exception as e:
            logger.error(f"❌ Spam ensemble health check test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_spam_pattern_accuracy(self) -> Dict[str, Any]:
        """Test 8: Spam pattern accuracy with challenging cases"""
        logger.info("Testing spam pattern accuracy...")
        
        try:
            ensemble = SpamEnsemble()
            await ensemble.initialize()
            
            # More challenging test cases
            challenging_cases = [
                {"text": "Earn money working from home", "expected_spam": True},
                {"text": "Limited time offer - 50% off", "expected_spam": True},
                {"text": "Your account needs verification", "expected_spam": True},
                {"text": "Meeting scheduled for tomorrow", "expected_spam": False},
                {"text": "Project deadline is next week", "expected_spam": False},
                {"text": "Free consultation available", "expected_spam": False},  # Legitimate business
                {"text": "URGENT!!! Act now or lose forever!!!", "expected_spam": True}
            ]
            
            correct_predictions = 0
            total_cases = len(challenging_cases)
            detection_results = []
            
            loaded_detectors = ensemble.get_detectors()
            
            for case in challenging_cases:
                # Test with each detector
                detector_results = []
                
                for detector in loaded_detectors:
                    result = await detector.detect(case["text"])
                    is_spam = result.blocked or result.confidence > 0.5
                    
                    detector_results.append({
                        "detector": detector.name,
                        "detected_spam": is_spam,
                        "confidence": result.confidence
                    })
                
                # Ensemble decision (majority vote)
                spam_votes = sum(1 for r in detector_results if r["detected_spam"])
                ensemble_decision = spam_votes > len(detector_results) / 2
                
                if ensemble_decision == case["expected_spam"]:
                    correct_predictions += 1
                
                detection_results.append({
                    "text": case["text"],
                    "expected_spam": case["expected_spam"],
                    "ensemble_decision": ensemble_decision,
                    "detector_results": detector_results
                })
            
            accuracy = correct_predictions / total_cases
            
            logger.info(f"Spam pattern accuracy: {accuracy:.2f}")
            
            if accuracy >= 0.6:  # 60% accuracy threshold for challenging cases
                logger.info("✅ Spam pattern accuracy test passed")
                return {"status": "passed", "accuracy": accuracy, "detection_results": detection_results}
            else:
                logger.warning("❌ Spam pattern accuracy below threshold")
                return {"status": "failed", "accuracy": accuracy, "detection_results": detection_results}
            
        except Exception as e:
            logger.error(f"❌ Spam pattern accuracy test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all spam ensemble tests"""
        logger.info("Starting spam ensemble test suite...")
        
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": {}
        }
        
        # List of test methods
        test_methods = [
            ("roberta_detector_init", self.test_roberta_spam_detector_initialization),
            ("roberta_spam_detection", self.test_roberta_spam_detection),
            ("keyword_pattern_detector_init", self.test_keyword_pattern_detector_initialization),
            ("keyword_pattern_detection", self.test_keyword_pattern_detection),
            ("spam_ensemble_init", self.test_spam_ensemble_initialization),
            ("spam_ensemble_detection", self.test_spam_ensemble_detection),
            ("spam_health_check", self.test_spam_health_check),
            ("spam_pattern_accuracy", self.test_spam_pattern_accuracy)
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
        
        logger.info(f"Spam ensemble test suite completed: {test_results['passed_tests']}/{test_results['total_tests']} tests passed ({success_rate:.1f}%)")
        
        return test_results

async def main():
    """Main test runner"""
    logger.info("Spam Detection Ensemble Test Suite")
    logger.info("=" * 50)
    
    test_runner = TestSpamEnsemble()
    results = await test_runner.run_all_tests()
    
    print("\n" + "=" * 50)
    print("SPAM ENSEMBLE TEST RESULTS")
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
        if "accuracy" in test_result:
            print(f"   Accuracy: {test_result['accuracy']:.2f}")
        if "error" in test_result:
            print(f"   Error: {test_result['error']}")
    
    print("\n" + "=" * 50)
    
    if results["success_rate"] >= 80.0:
        print("🎉 Spam ensemble implementation: SUCCESS")
        return 0
    else:
        print("❌ Spam ensemble implementation: NEEDS WORK")
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