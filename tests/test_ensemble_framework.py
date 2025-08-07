"""
Test Suite for Ensemble Framework
Phase 1 testing infrastructure as per implementation plan
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from guardrails.ensemble import EnterpriseGuardrailsManager, EnsembleFramework
from guardrails.detectors.toxicity_ensemble import ToxicityEnsemble

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TestEnsembleFramework:
    """Test suite for the ensemble framework"""
    
    def __init__(self):
        self.test_cases = [
            {
                "text": "This is a normal, safe message.",
                "expected_blocked": False,
                "test_name": "safe_message"
            },
            {
                "text": "You are stupid and I hate you!",
                "expected_blocked": True,
                "test_name": "toxic_message"
            },
            {
                "text": "Hello, how are you today?",
                "expected_blocked": False,
                "test_name": "polite_greeting"
            },
            {
                "text": "What a beautiful day it is!",
                "expected_blocked": False,
                "test_name": "positive_message"
            }
        ]
    
    async def test_ensemble_framework_initialization(self) -> Dict[str, Any]:
        """Test 1: Framework initialization"""
        logger.info("Testing ensemble framework initialization...")
        
        try:
            framework = EnsembleFramework()
            
            # Test configuration
            assert framework.high_confidence_threshold == 0.92
            assert framework.medium_confidence_threshold == 0.75
            assert framework.enable_parallel_processing == True
            
            logger.info("✅ Ensemble framework initialization test passed")
            return {"status": "passed", "details": "Framework initialized correctly"}
            
        except Exception as e:
            logger.error(f"❌ Ensemble framework initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_toxicity_ensemble_loading(self) -> Dict[str, Any]:
        """Test 2: Toxicity ensemble loading (without actual model loading)"""
        logger.info("Testing toxicity ensemble initialization...")
        
        try:
            toxicity_ensemble = ToxicityEnsemble()
            
            # Initialize (will create detector objects but not load actual models)
            result = await toxicity_ensemble.initialize()
            
            # Check structure
            assert toxicity_ensemble.is_initialized == True
            assert len(toxicity_ensemble.detectors) == 4  # 4 toxicity detectors
            
            # Check detector names and weights
            detector_names = [d.name for d in toxicity_ensemble.detectors]
            expected_names = ["toxic_bert", "martin_ha_toxic", "nicholas_kluge_toxic", "custom_distilbert"]
            
            for expected_name in expected_names:
                assert expected_name in detector_names, f"Missing detector: {expected_name}"
            
            # Check weights sum approximately to 1.0 (35% + 30% + 25% + 10% = 100%)
            total_weight = sum(d.weight for d in toxicity_ensemble.detectors)
            assert abs(total_weight - 1.0) < 0.01, f"Weights don't sum to 1.0: {total_weight}"
            
            logger.info("✅ Toxicity ensemble initialization test passed")
            return {"status": "passed", "details": f"Initialized {len(toxicity_ensemble.detectors)} detectors"}
            
        except Exception as e:
            logger.error(f"❌ Toxicity ensemble initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_enterprise_manager_initialization(self) -> Dict[str, Any]:
        """Test 3: Enterprise manager initialization"""
        logger.info("Testing enterprise guardrails manager initialization...")
        
        try:
            manager = EnterpriseGuardrailsManager()
            
            # Test initialization (without loading actual models)
            # This will create the structure but model loading will fail gracefully
            result = await manager.initialize()
            
            # Check basic structure
            assert manager.is_initialized == True
            assert len(manager.get_available_guardrails()) > 0
            
            # Check available guardrails
            available = manager.get_available_guardrails()
            expected_guardrails = ["toxicity", "pii", "spam", "topic", "fact_check", "prompt_injection"]
            
            for guardrail in expected_guardrails:
                assert guardrail in available, f"Missing guardrail: {guardrail}"
            
            logger.info("✅ Enterprise manager initialization test passed")
            return {"status": "passed", "details": f"Available guardrails: {available}"}
            
        except Exception as e:
            logger.error(f"❌ Enterprise manager initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_confidence_routing_logic(self) -> Dict[str, Any]:
        """Test 4: Confidence-based routing logic"""
        logger.info("Testing confidence-based routing logic...")
        
        try:
            framework = EnsembleFramework()
            
            # Test confidence level determination
            high_conf = framework._determine_confidence_level(0.95)
            medium_conf = framework._determine_confidence_level(0.80)
            low_conf = framework._determine_confidence_level(0.60)
            
            assert high_conf.value == "high"
            assert medium_conf.value == "medium" 
            assert low_conf.value == "low"
            
            logger.info("✅ Confidence routing logic test passed")
            return {"status": "passed", "details": "Confidence thresholds working correctly"}
            
        except Exception as e:
            logger.error(f"❌ Confidence routing logic test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_character_attack_detection(self) -> Dict[str, Any]:
        """Test 5: Character-level attack detection"""
        logger.info("Testing character-level attack detection...")
        
        try:
            framework = EnsembleFramework()
            
            # Test various character attacks
            test_cases = [
                ("Normal text", False),
                ("Text with invisible\u200bchar", True),
                ("Text with many \\u0041\\u0042\\u0043 escapes", True),
                ("Text with Cyrillic а е о", True),  # Cyrillic that look like Latin
                ("Normal unicode: café résumé", False)
            ]
            
            for text, should_detect in test_cases:
                detected = framework._check_character_attacks(text)
                assert detected == should_detect, f"Character attack detection failed for: {text}"
            
            logger.info("✅ Character attack detection test passed")
            return {"status": "passed", "details": "Character attack detection working correctly"}
            
        except Exception as e:
            logger.error(f"❌ Character attack detection test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_input_format_validation(self) -> Dict[str, Any]:
        """Test 6: Input format validation"""
        logger.info("Testing input format validation...")
        
        try:
            framework = EnsembleFramework()
            
            # Test format validation
            test_cases = [
                ("Normal text", True),
                ("Text with null\x00byte", False),
                ("Short text", True),
                ("A" * 11000, False),  # Too long
                ("\n" * 101, False),   # Too many newlines
                ("Text with\nnormal\nlines", True)
            ]
            
            for text, should_be_valid in test_cases:
                is_valid = framework._validate_input_format(text)
                assert is_valid == should_be_valid, f"Format validation failed for text length {len(text)}"
            
            logger.info("✅ Input format validation test passed")
            return {"status": "passed", "details": "Input format validation working correctly"}
            
        except Exception as e:
            logger.error(f"❌ Input format validation test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_performance_metrics_tracking(self) -> Dict[str, Any]:
        """Test 7: Performance metrics tracking"""
        logger.info("Testing performance metrics tracking...")
        
        try:
            framework = EnsembleFramework()
            
            # Check initial state
            initial_stats = framework.get_performance_stats()
            assert initial_stats["total_requests"] == 0
            
            # Reset and check
            framework.reset_performance_stats()
            reset_stats = framework.get_performance_stats()
            assert reset_stats["total_requests"] == 0
            assert "stage_usage" in reset_stats
            assert "consensus_rates" in reset_stats
            
            logger.info("✅ Performance metrics tracking test passed")
            return {"status": "passed", "details": "Performance metrics working correctly"}
            
        except Exception as e:
            logger.error(f"❌ Performance metrics tracking test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("Starting comprehensive ensemble framework test suite...")
        
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": {}
        }
        
        # List of test methods
        test_methods = [
            ("ensemble_framework_init", self.test_ensemble_framework_initialization),
            ("toxicity_ensemble_loading", self.test_toxicity_ensemble_loading),
            ("enterprise_manager_init", self.test_enterprise_manager_initialization),
            ("confidence_routing", self.test_confidence_routing_logic),
            ("character_attack_detection", self.test_character_attack_detection),
            ("input_format_validation", self.test_input_format_validation),
            ("performance_metrics", self.test_performance_metrics_tracking)
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
        
        logger.info(f"Test suite completed: {test_results['passed_tests']}/{test_results['total_tests']} tests passed ({success_rate:.1f}%)")
        
        if test_results["failed_tests"] > 0:
            logger.warning(f"{test_results['failed_tests']} tests failed")
            for test_name, result in test_results["test_details"].items():
                if result["status"] == "failed":
                    logger.error(f"Failed test: {test_name} - {result.get('error', 'Unknown error')}")
        
        return test_results

async def main():
    """Main test runner"""
    logger.info("Phase 1 Ensemble Framework Test Suite")
    logger.info("=" * 50)
    
    test_runner = TestEnsembleFramework()
    results = await test_runner.run_all_tests()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print("=" * 50)
    
    if results["success_rate"] >= 80.0:
        print("🎉 Phase 1 ensemble framework implementation: SUCCESS")
        return 0
    else:
        print("❌ Phase 1 ensemble framework implementation: NEEDS WORK")
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