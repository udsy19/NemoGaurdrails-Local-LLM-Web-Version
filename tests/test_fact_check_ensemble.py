"""
Test Suite for Fact-checking Ensemble
Validates the fact-checking implementation with comprehensive test cases
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from guardrails.detectors.fact_check_ensemble import (
    FactCheckEnsemble,
    RetrievalFactChecker,
    KnowledgeBaseChecker,
    SourceValidationChecker
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TestFactCheckEnsemble:
    """Test suite for fact-checking ensemble"""
    
    def __init__(self):
        self.test_cases = [
            # Scientific Facts
            {
                "text": "Water boils at 100 degrees Celsius at sea level.",
                "expected_factual": True,
                "test_name": "scientific_fact_water_boiling",
                "fact_type": "scientific"
            },
            {
                "text": "The speed of light is approximately 299,792,458 meters per second.",
                "expected_factual": True,
                "test_name": "scientific_fact_speed_of_light",
                "fact_type": "scientific"
            },
            {
                "text": "Water boils at 50 degrees Celsius at sea level.",
                "expected_factual": False,
                "test_name": "scientific_false_water_boiling",
                "fact_type": "scientific"
            },
            
            # Historical Facts
            {
                "text": "World War II ended in 1945.",
                "expected_factual": True,
                "test_name": "historical_fact_wwii",
                "fact_type": "historical"
            },
            {
                "text": "The Berlin Wall fell in 1989.",
                "expected_factual": True,
                "test_name": "historical_fact_berlin_wall",
                "fact_type": "historical"
            },
            {
                "text": "World War II ended in 1950.",
                "expected_factual": False,
                "test_name": "historical_false_wwii",
                "fact_type": "historical"
            },
            
            # Mathematical Facts
            {
                "text": "The square root of 16 is 4.",
                "expected_factual": True,
                "test_name": "mathematical_fact_square_root",
                "fact_type": "mathematical"
            },
            {
                "text": "Pi is approximately 3.14159.",
                "expected_factual": True,
                "test_name": "mathematical_fact_pi",
                "fact_type": "mathematical"
            },
            {
                "text": "The square root of 16 is 5.",
                "expected_factual": False,
                "test_name": "mathematical_false_square_root",
                "fact_type": "mathematical"
            },
            
            # General Knowledge
            {
                "text": "There are 7 continents on Earth.",
                "expected_factual": True,
                "test_name": "general_fact_continents",
                "fact_type": "general"
            },
            {
                "text": "Mount Everest is the highest mountain in the world.",
                "expected_factual": True,
                "test_name": "general_fact_everest",
                "fact_type": "general"
            },
            {
                "text": "There are 12 continents on Earth.",
                "expected_factual": False,
                "test_name": "general_false_continents",
                "fact_type": "general"
            },
            
            # Suspicious Claims
            {
                "text": "This miracle cure will solve all your problems instantly.",
                "expected_factual": False,
                "test_name": "suspicious_miracle_cure",
                "fact_type": "suspicious"
            },
            {
                "text": "Scientists have discovered a 100% guaranteed way to live forever.",
                "expected_factual": False,
                "test_name": "suspicious_live_forever",
                "fact_type": "suspicious"
            },
            {
                "text": "This secret method that doctors don't want you to know.",
                "expected_factual": False,
                "test_name": "suspicious_secret_method",
                "fact_type": "suspicious"
            },
            
            # Mixed Content
            {
                "text": "According to NASA, the sun is a star and it's approximately 93 million miles from Earth.",
                "expected_factual": True,
                "test_name": "mixed_content_nasa_sun",
                "fact_type": "mixed"
            },
            {
                "text": "Research shows that drinking water is important for health.",
                "expected_factual": True,
                "test_name": "mixed_content_water_health",
                "fact_type": "mixed"
            },
            {
                "text": "Studies prove that eating air will make you immortal.",
                "expected_factual": False,
                "test_name": "mixed_content_false_study",
                "fact_type": "mixed"
            },
            
            # Neutral Content
            {
                "text": "I enjoyed watching the movie yesterday.",
                "expected_factual": True,  # No factual claims to verify
                "test_name": "neutral_personal_opinion",
                "fact_type": "neutral"
            },
            {
                "text": "The weather is nice today.",
                "expected_factual": True,  # Subjective, no factual claims
                "test_name": "neutral_weather_opinion",
                "fact_type": "neutral"
            }
        ]
    
    async def test_retrieval_fact_checker_initialization(self) -> Dict[str, Any]:
        """Test 1: Retrieval fact checker initialization"""
        logger.info("Testing retrieval fact checker initialization...")
        
        try:
            checker = RetrievalFactChecker()
            result = await checker.load_model()
            
            assert result == True, "Retrieval fact checker should load successfully"
            assert checker.is_loaded == True, "Checker should be marked as loaded"
            assert checker.weight == 0.40, "Retrieval checker should have 40% weight"
            assert checker.name == "retrieval_fact_checker", "Checker should have correct name"
            
            logger.info("✅ Retrieval fact checker initialization test passed")
            return {"status": "passed", "details": "Retrieval fact checker loaded successfully"}
            
        except Exception as e:
            logger.error(f"❌ Retrieval fact checker initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_knowledge_base_checker_initialization(self) -> Dict[str, Any]:
        """Test 2: Knowledge base checker initialization"""
        logger.info("Testing knowledge base checker initialization...")
        
        try:
            checker = KnowledgeBaseChecker()
            result = await checker.load_model()
            
            assert result == True, "Knowledge base checker should load successfully"
            assert checker.is_loaded == True, "Checker should be marked as loaded"
            assert checker.weight == 0.30, "Knowledge base checker should have 30% weight"
            assert checker.name == "knowledge_base_checker", "Checker should have correct name"
            assert len(checker.knowledge_base) > 0, "Should have knowledge base loaded"
            
            logger.info("✅ Knowledge base checker initialization test passed")
            return {"status": "passed", "details": f"Knowledge base with {len(checker.knowledge_base)} categories loaded"}
            
        except Exception as e:
            logger.error(f"❌ Knowledge base checker initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_source_validation_checker_initialization(self) -> Dict[str, Any]:
        """Test 3: Source validation checker initialization"""
        logger.info("Testing source validation checker initialization...")
        
        try:
            checker = SourceValidationChecker()
            result = await checker.load_model()
            
            assert result == True, "Source validation checker should load successfully"
            assert checker.is_loaded == True, "Checker should be marked as loaded"
            assert checker.weight == 0.30, "Source validation checker should have 30% weight"
            assert checker.name == "source_validation_checker", "Checker should have correct name"
            assert len(checker.trusted_sources) > 0, "Should have trusted sources loaded"
            
            logger.info("✅ Source validation checker initialization test passed")
            return {"status": "passed", "details": f"Source validation with {len(checker.trusted_sources)} trusted source categories loaded"}
            
        except Exception as e:
            logger.error(f"❌ Source validation checker initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_fact_check_ensemble_initialization(self) -> Dict[str, Any]:
        """Test 4: Fact check ensemble initialization"""
        logger.info("Testing fact check ensemble initialization...")
        
        try:
            ensemble = FactCheckEnsemble()
            result = await ensemble.initialize()
            
            assert result == True, "Ensemble should initialize successfully"
            assert ensemble.is_initialized == True, "Ensemble should be marked as initialized"
            assert len(ensemble.detectors) == 3, "Should have 3 fact checkers"
            
            # Check detector weights sum to 1.0
            total_weight = sum(d.weight for d in ensemble.detectors)
            assert abs(total_weight - 1.0) < 0.01, f"Weights should sum to 1.0, got {total_weight}"
            
            # Check detector names
            detector_names = [d.name for d in ensemble.detectors]
            expected_names = ["retrieval_fact_checker", "knowledge_base_checker", "source_validation_checker"]
            for expected_name in expected_names:
                assert expected_name in detector_names, f"Missing checker: {expected_name}"
            
            logger.info("✅ Fact check ensemble initialization test passed")
            return {"status": "passed", "details": f"Initialized {len(ensemble.detectors)} fact checkers"}
            
        except Exception as e:
            logger.error(f"❌ Fact check ensemble initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_fact_checking_accuracy(self) -> Dict[str, Any]:
        """Test 5: Fact checking accuracy"""
        logger.info("Testing fact checking accuracy...")
        
        try:
            ensemble = FactCheckEnsemble()
            await ensemble.initialize()
            
            # Test cases
            test_results = []
            
            for test_case in self.test_cases:
                result = await ensemble.check_facts(test_case["text"])
                
                # For fact checking, we consider high confidence as factual
                factual_confidence = result.get("factual_accuracy", 0.5)
                detected_factual = factual_confidence > 0.4  # Lower threshold for fact checking
                expected_factual = test_case["expected_factual"]
                
                test_results.append({
                    "test_name": test_case["test_name"],
                    "text": test_case["text"][:50] + "...",
                    "expected_factual": expected_factual,
                    "detected_factual": detected_factual,
                    "factual_confidence": factual_confidence,
                    "fact_type": test_case["fact_type"],
                    "blocking_reasons": result.get("blocking_reasons", []),
                    "correct": detected_factual == expected_factual
                })
            
            # Calculate accuracy
            correct_predictions = sum(1 for r in test_results if r["correct"])
            accuracy = correct_predictions / len(test_results)
            
            # Calculate accuracy by type
            type_accuracy = {}
            for fact_type in set(case["fact_type"] for case in self.test_cases):
                type_cases = [r for r in test_results if r["fact_type"] == fact_type]
                type_correct = sum(1 for r in type_cases if r["correct"])
                type_accuracy[fact_type] = type_correct / len(type_cases) if type_cases else 0.0
            
            logger.info(f"Fact checking accuracy: {accuracy:.2f}")
            
            if accuracy >= 0.70:  # 70% accuracy threshold for fact checking
                logger.info("✅ Fact checking accuracy test passed")
                return {
                    "status": "passed", 
                    "accuracy": accuracy, 
                    "type_accuracy": type_accuracy,
                    "test_results": test_results
                }
            else:
                logger.warning("❌ Fact checking accuracy below threshold")
                return {
                    "status": "failed", 
                    "accuracy": accuracy, 
                    "type_accuracy": type_accuracy,
                    "test_results": test_results
                }
            
        except Exception as e:
            logger.error(f"❌ Fact checking accuracy test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_retrieval_fact_checking(self) -> Dict[str, Any]:
        """Test 6: Retrieval fact checking functionality"""
        logger.info("Testing retrieval fact checking...")
        
        try:
            checker = RetrievalFactChecker()
            await checker.load_model()
            
            # Test specific facts
            fact_tests = [
                ("Water boils at 100°C at sea level", True),
                ("The Earth is approximately 4.5 billion years old", True),
                ("Humans have 46 chromosomes", True),
                ("Water boils at 200°C at sea level", False),
                ("The Earth is 1000 years old", False),
                ("This is a general statement about nothing specific", True)  # Should pass as no claims
            ]
            
            retrieval_results = []
            for text, expected in fact_tests:
                result = await checker.detect(text)
                
                # For retrieval, we check if confidence indicates factual accuracy
                factual = result.confidence > 0.3 or not result.blocked
                
                retrieval_results.append({
                    "text": text,
                    "expected_factual": expected,
                    "detected_factual": factual,
                    "confidence": result.confidence,
                    "blocked": result.blocked,
                    "correct": factual == expected
                })
            
            correct_retrievals = sum(1 for r in retrieval_results if r["correct"])
            retrieval_accuracy = correct_retrievals / len(retrieval_results)
            
            logger.info(f"Retrieval fact checking accuracy: {retrieval_accuracy:.2f}")
            
            if retrieval_accuracy >= 0.65:  # 65% accuracy threshold
                logger.info("✅ Retrieval fact checking test passed")
                return {"status": "passed", "accuracy": retrieval_accuracy, "results": retrieval_results}
            else:
                logger.warning("❌ Retrieval fact checking accuracy below threshold")
                return {"status": "failed", "accuracy": retrieval_accuracy, "results": retrieval_results}
            
        except Exception as e:
            logger.error(f"❌ Retrieval fact checking test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_knowledge_base_checking(self) -> Dict[str, Any]:
        """Test 7: Knowledge base checking functionality"""
        logger.info("Testing knowledge base checking...")
        
        try:
            checker = KnowledgeBaseChecker()
            await checker.load_model()
            
            # Test specific knowledge base entries
            kb_tests = [
                ("Apple was founded in 1976", True),
                ("The capital of France is Paris", True),
                ("Google was founded in 1998", True),
                ("Apple was founded in 1990", False),
                ("The capital of France is London", False),
                ("Random text with no entities", True)  # Should pass as no entities
            ]
            
            kb_results = []
            for text, expected in kb_tests:
                result = await checker.detect(text)
                
                # For knowledge base, we check if confidence indicates factual accuracy
                factual = result.confidence > 0.3 or not result.blocked
                
                kb_results.append({
                    "text": text,
                    "expected_factual": expected,
                    "detected_factual": factual,
                    "confidence": result.confidence,
                    "blocked": result.blocked,
                    "correct": factual == expected
                })
            
            correct_kb = sum(1 for r in kb_results if r["correct"])
            kb_accuracy = correct_kb / len(kb_results)
            
            logger.info(f"Knowledge base checking accuracy: {kb_accuracy:.2f}")
            
            if kb_accuracy >= 0.65:  # 65% accuracy threshold
                logger.info("✅ Knowledge base checking test passed")
                return {"status": "passed", "accuracy": kb_accuracy, "results": kb_results}
            else:
                logger.warning("❌ Knowledge base checking accuracy below threshold")
                return {"status": "failed", "accuracy": kb_accuracy, "results": kb_results}
            
        except Exception as e:
            logger.error(f"❌ Knowledge base checking test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_source_validation(self) -> Dict[str, Any]:
        """Test 8: Source validation functionality"""
        logger.info("Testing source validation...")
        
        try:
            checker = SourceValidationChecker()
            await checker.load_model()
            
            # Test source validation
            source_tests = [
                ("According to NASA, the sun is a star.", True),
                ("Research from Harvard shows interesting results.", True),
                ("A study published in Nature magazine found...", True),
                ("Some anonymous source claims that...", False),
                ("This conspiracy theory suggests...", False),
                ("No sources mentioned in this text.", True)  # Should pass as no sources
            ]
            
            source_results = []
            for text, expected in source_tests:
                result = await checker.detect(text)
                
                # For source validation, we check if confidence indicates good sources
                valid_sources = result.confidence > 0.4 or not result.blocked
                
                source_results.append({
                    "text": text,
                    "expected_valid": expected,
                    "detected_valid": valid_sources,
                    "confidence": result.confidence,
                    "blocked": result.blocked,
                    "correct": valid_sources == expected
                })
            
            correct_sources = sum(1 for r in source_results if r["correct"])
            source_accuracy = correct_sources / len(source_results)
            
            logger.info(f"Source validation accuracy: {source_accuracy:.2f}")
            
            if source_accuracy >= 0.65:  # 65% accuracy threshold
                logger.info("✅ Source validation test passed")
                return {"status": "passed", "accuracy": source_accuracy, "results": source_results}
            else:
                logger.warning("❌ Source validation accuracy below threshold")
                return {"status": "failed", "accuracy": source_accuracy, "results": source_results}
            
        except Exception as e:
            logger.error(f"❌ Source validation test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_ensemble_health_check(self) -> Dict[str, Any]:
        """Test 9: Ensemble health check"""
        logger.info("Testing ensemble health check...")
        
        try:
            ensemble = FactCheckEnsemble()
            await ensemble.initialize()
            
            health_status = await ensemble.health_check()
            
            assert "healthy" in health_status, "Health status should include 'healthy' field"
            assert "total_checkers" in health_status, "Health status should include checker count"
            assert "checker_status" in health_status, "Health status should include checker status"
            
            assert health_status["total_checkers"] == 3, "Should report 3 checkers"
            assert health_status["loaded_checkers"] >= 2, "Should have at least 2 loaded checkers"
            
            logger.info("✅ Ensemble health check test passed")
            return {"status": "passed", "health_status": health_status}
            
        except Exception as e:
            logger.error(f"❌ Ensemble health check test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_suspicious_claims_detection(self) -> Dict[str, Any]:
        """Test 10: Suspicious claims detection"""
        logger.info("Testing suspicious claims detection...")
        
        try:
            ensemble = FactCheckEnsemble()
            await ensemble.initialize()
            
            # Test suspicious claims
            suspicious_tests = [
                ("This miracle cure will solve all your problems 100% guaranteed!", False),
                ("Scientists have discovered a secret that doctors don't want you to know.", False),
                ("This method is proven to work instantly with no side effects.", False),
                ("According to peer-reviewed research, regular exercise is beneficial.", True),
                ("Data from multiple studies shows correlation between diet and health.", True)
            ]
            
            suspicious_results = []
            for text, expected_credible in suspicious_tests:
                result = await ensemble.check_facts(text)
                
                factual_confidence = result.get("factual_accuracy", 0.5)
                detected_credible = factual_confidence > 0.4
                
                suspicious_results.append({
                    "text": text,
                    "expected_credible": expected_credible,
                    "detected_credible": detected_credible,
                    "confidence": factual_confidence,
                    "blocked": result.get("blocked", False),
                    "correct": detected_credible == expected_credible
                })
            
            correct_suspicious = sum(1 for r in suspicious_results if r["correct"])
            suspicious_accuracy = correct_suspicious / len(suspicious_results)
            
            logger.info(f"Suspicious claims detection accuracy: {suspicious_accuracy:.2f}")
            
            if suspicious_accuracy >= 0.60:  # 60% accuracy threshold
                logger.info("✅ Suspicious claims detection test passed")
                return {"status": "passed", "accuracy": suspicious_accuracy, "results": suspicious_results}
            else:
                logger.warning("❌ Suspicious claims detection accuracy below threshold")
                return {"status": "failed", "accuracy": suspicious_accuracy, "results": suspicious_results}
            
        except Exception as e:
            logger.error(f"❌ Suspicious claims detection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all fact-checking ensemble tests"""
        logger.info("Starting fact-checking ensemble test suite...")
        
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": {}
        }
        
        # List of test methods
        test_methods = [
            ("retrieval_fact_checker_init", self.test_retrieval_fact_checker_initialization),
            ("knowledge_base_checker_init", self.test_knowledge_base_checker_initialization),
            ("source_validation_checker_init", self.test_source_validation_checker_initialization),
            ("fact_check_ensemble_init", self.test_fact_check_ensemble_initialization),
            ("fact_checking_accuracy", self.test_fact_checking_accuracy),
            ("retrieval_fact_checking", self.test_retrieval_fact_checking),
            ("knowledge_base_checking", self.test_knowledge_base_checking),
            ("source_validation", self.test_source_validation),
            ("ensemble_health_check", self.test_ensemble_health_check),
            ("suspicious_claims_detection", self.test_suspicious_claims_detection)
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
        
        logger.info(f"Fact-checking ensemble test suite completed: {test_results['passed_tests']}/{test_results['total_tests']} tests passed ({success_rate:.1f}%)")
        
        return test_results

async def main():
    """Main test runner"""
    logger.info("Fact-checking Ensemble Test Suite")
    logger.info("=" * 50)
    
    test_runner = TestFactCheckEnsemble()
    results = await test_runner.run_all_tests()
    
    print("\n" + "=" * 50)
    print("FACT-CHECKING ENSEMBLE TEST RESULTS")
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
        print("🎉 Fact-checking ensemble implementation: SUCCESS")
        return 0
    else:
        print("❌ Fact-checking ensemble implementation: NEEDS WORK")
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