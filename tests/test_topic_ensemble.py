"""
Test Suite for Topic Classification Ensemble
Validates the topic classification implementation with comprehensive test cases
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from guardrails.detectors.topic_ensemble import (
    TopicEnsemble,
    BERTTopicClassifier,
    RuleBasedTopicClassifier
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TestTopicEnsemble:
    """Test suite for topic classification ensemble"""
    
    def __init__(self):
        self.test_cases = [
            # Business Topics
            {
                "text": "Our company needs to improve quarterly profits and marketing strategies.",
                "expected_topic": "business",
                "test_name": "business_corporate_strategy",
                "should_block": False
            },
            {
                "text": "The finance team is analyzing investment opportunities and revenue growth.",
                "expected_topic": "business",
                "test_name": "business_finance_analysis",
                "should_block": False
            },
            {
                "text": "Let's schedule a meeting to discuss our sales targets and client proposals.",
                "expected_topic": "business",
                "test_name": "business_meeting_sales",
                "should_block": False
            },
            
            # Technology Topics
            {
                "text": "We're implementing machine learning algorithms for data analysis and AI development.",
                "expected_topic": "technology",
                "test_name": "technology_ai_ml",
                "should_block": False
            },
            {
                "text": "The software development team is working on cybersecurity and programming solutions.",
                "expected_topic": "technology",
                "test_name": "technology_software_security",
                "should_block": False
            },
            {
                "text": "Our internet infrastructure needs upgrading for better computer performance.",
                "expected_topic": "technology",
                "test_name": "technology_infrastructure",
                "should_block": False
            },
            
            # Healthcare Topics
            {
                "text": "The doctor recommended new medical treatment for the patient's symptoms.",
                "expected_topic": "healthcare",
                "test_name": "healthcare_medical_treatment",
                "should_block": False
            },
            {
                "text": "Hospital wellness programs focus on health and fitness for better diagnosis.",
                "expected_topic": "healthcare",
                "test_name": "healthcare_wellness_programs",
                "should_block": False
            },
            {
                "text": "Prescription medicine and therapy sessions help with healthcare recovery.",
                "expected_topic": "healthcare",
                "test_name": "healthcare_prescription_therapy",
                "should_block": False
            },
            
            # Education Topics
            {
                "text": "University students are learning about academic curriculum and teaching methods.",
                "expected_topic": "education",
                "test_name": "education_university_learning",
                "should_block": False
            },
            {
                "text": "The school professor assigns homework and exams for course assessment.",
                "expected_topic": "education",
                "test_name": "education_school_assignments",
                "should_block": False
            },
            {
                "text": "Educational research shows that study habits improve academic performance.",
                "expected_topic": "education",
                "test_name": "education_research_study",
                "should_block": False
            },
            
            # Entertainment Topics
            {
                "text": "The movie premiere featured famous celebrities and exciting entertainment.",
                "expected_topic": "entertainment",
                "test_name": "entertainment_movie_celebrities",
                "should_block": False
            },
            {
                "text": "Music concerts and sports events provide fun leisure activities.",
                "expected_topic": "entertainment",
                "test_name": "entertainment_music_sports",
                "should_block": False
            },
            {
                "text": "Gaming tournaments and TV shows offer media entertainment for audiences.",
                "expected_topic": "entertainment",
                "test_name": "entertainment_gaming_tv",
                "should_block": False
            },
            
            # Politics Topics
            {
                "text": "Government policy and political elections influence legal regulations.",
                "expected_topic": "politics",
                "test_name": "politics_government_policy",
                "should_block": False
            },
            {
                "text": "The president announced new legislation during the campaign season.",
                "expected_topic": "politics",
                "test_name": "politics_president_legislation",
                "should_block": False
            },
            {
                "text": "Congress votes on political issues that affect governance and law.",
                "expected_topic": "politics",
                "test_name": "politics_congress_voting",
                "should_block": False
            },
            
            # Personal Topics
            {
                "text": "My family and friends enjoy personal hobbies and private lifestyle choices.",
                "expected_topic": "personal",
                "test_name": "personal_family_hobbies",
                "should_block": False
            },
            {
                "text": "Personal relationships and life experiences shape our daily home activities.",
                "expected_topic": "personal",
                "test_name": "personal_relationships_life",
                "should_block": False
            },
            {
                "text": "Private memories and personal interests define our individual lifestyle.",
                "expected_topic": "personal",
                "test_name": "personal_memories_interests",
                "should_block": False
            },
            
            # Inappropriate Content (Should be blocked)
            {
                "text": "This content contains explicit sexual material and adult themes.",
                "expected_topic": "inappropriate",
                "test_name": "inappropriate_sexual_content",
                "should_block": True
            },
            {
                "text": "Violence and harassment content with disturbing hate speech.",
                "expected_topic": "inappropriate",
                "test_name": "inappropriate_violence_hate",
                "should_block": True
            },
            {
                "text": "Threatening behavior and harmful content that promotes illegal activities.",
                "expected_topic": "inappropriate",
                "test_name": "inappropriate_threats_illegal",
                "should_block": True
            },
            
            # Mixed/Ambiguous Content
            {
                "text": "The weather is nice today and I'm feeling good.",
                "expected_topic": "personal",  # Default fallback
                "test_name": "mixed_weather_feeling",
                "should_block": False
            },
            {
                "text": "Technology education helps students learn programming in business applications.",
                "expected_topic": "technology",  # Should pick strongest signal
                "test_name": "mixed_tech_education_business",
                "should_block": False
            },
            {
                "text": "Healthcare technology advances medical education for better patient outcomes.",
                "expected_topic": "healthcare",  # Should pick strongest signal
                "test_name": "mixed_healthcare_tech_education",
                "should_block": False
            }
        ]
    
    async def test_bert_topic_classifier_initialization(self) -> Dict[str, Any]:
        """Test 1: BERT topic classifier initialization"""
        logger.info("Testing BERT topic classifier initialization...")
        
        try:
            classifier = BERTTopicClassifier()
            result = await classifier.load_model()
            
            assert result == True, "BERT topic classifier should load successfully"
            assert classifier.is_loaded == True, "Classifier should be marked as loaded"
            assert classifier.weight == 0.50, "BERT classifier should have 50% weight"
            assert classifier.name == "bert_topic_classifier", "Classifier should have correct name"
            assert len(classifier.topic_categories) > 0, "Should have topic categories loaded"
            
            logger.info("✅ BERT topic classifier initialization test passed")
            return {"status": "passed", "details": f"Loaded {len(classifier.topic_categories)} topic categories"}
            
        except Exception as e:
            logger.error(f"❌ BERT topic classifier initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_rule_based_classifier_initialization(self) -> Dict[str, Any]:
        """Test 2: Rule-based classifier initialization"""
        logger.info("Testing rule-based classifier initialization...")
        
        try:
            classifier = RuleBasedTopicClassifier()
            result = await classifier.load_model()
            
            assert result == True, "Rule-based classifier should load successfully"
            assert classifier.is_loaded == True, "Classifier should be marked as loaded"
            assert classifier.weight == 0.25, "Rule-based classifier should have 25% weight"
            assert classifier.name == "rule_based_topic", "Classifier should have correct name"
            assert len(classifier.topic_rules) > 0, "Should have topic rules loaded"
            
            logger.info("✅ Rule-based classifier initialization test passed")
            return {"status": "passed", "details": f"Loaded {len(classifier.topic_rules)} topic rule categories"}
            
        except Exception as e:
            logger.error(f"❌ Rule-based classifier initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_topic_ensemble_initialization(self) -> Dict[str, Any]:
        """Test 3: Topic ensemble initialization"""
        logger.info("Testing topic ensemble initialization...")
        
        try:
            ensemble = TopicEnsemble()
            result = await ensemble.initialize()
            
            assert result == True, "Ensemble should initialize successfully"
            assert ensemble.is_initialized == True, "Ensemble should be marked as initialized"
            assert len(ensemble.detectors) == 2, "Should have 2 classifiers"
            
            # Check detector weights
            total_weight = sum(d.weight for d in ensemble.detectors)
            assert abs(total_weight - 0.75) < 0.01, f"Weights should sum to 0.75 (BERT 50% + Rules 25%), got {total_weight}"
            
            # Check detector names
            detector_names = [d.name for d in ensemble.detectors]
            expected_names = ["bert_topic_classifier", "rule_based_topic"]
            for expected_name in expected_names:
                assert expected_name in detector_names, f"Missing classifier: {expected_name}"
            
            logger.info("✅ Topic ensemble initialization test passed")
            return {"status": "passed", "details": f"Initialized {len(ensemble.detectors)} classifiers"}
            
        except Exception as e:
            logger.error(f"❌ Topic ensemble initialization test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_topic_classification_accuracy(self) -> Dict[str, Any]:
        """Test 4: Topic classification accuracy"""
        logger.info("Testing topic classification accuracy...")
        
        try:
            ensemble = TopicEnsemble()
            await ensemble.initialize()
            
            # Test cases
            test_results = []
            
            for test_case in self.test_cases:
                result = await ensemble.classify_topic(test_case["text"])
                
                detected_topic = result.get("topic", "unknown")
                expected_topic = test_case["expected_topic"]
                
                test_results.append({
                    "test_name": test_case["test_name"],
                    "text": test_case["text"][:50] + "...",
                    "expected_topic": expected_topic,
                    "detected_topic": detected_topic,
                    "confidence": result.get("confidence", 0.0),
                    "should_block": test_case["should_block"],
                    "correct": detected_topic == expected_topic
                })
            
            # Calculate accuracy
            correct_predictions = sum(1 for r in test_results if r["correct"])
            accuracy = correct_predictions / len(test_results)
            
            # Calculate accuracy by topic
            topic_accuracy = {}
            for topic in set(case["expected_topic"] for case in self.test_cases):
                topic_cases = [r for r in test_results if r["expected_topic"] == topic]
                topic_correct = sum(1 for r in topic_cases if r["correct"])
                topic_accuracy[topic] = topic_correct / len(topic_cases) if topic_cases else 0.0
            
            logger.info(f"Topic classification accuracy: {accuracy:.2f}")
            
            if accuracy >= 0.70:  # 70% accuracy threshold
                logger.info("✅ Topic classification accuracy test passed")
                return {
                    "status": "passed", 
                    "accuracy": accuracy, 
                    "topic_accuracy": topic_accuracy,
                    "test_results": test_results
                }
            else:
                logger.warning("❌ Topic classification accuracy below threshold")
                return {
                    "status": "failed", 
                    "accuracy": accuracy, 
                    "topic_accuracy": topic_accuracy,
                    "test_results": test_results
                }
            
        except Exception as e:
            logger.error(f"❌ Topic classification accuracy test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_bert_classification(self) -> Dict[str, Any]:
        """Test 5: BERT classification functionality"""
        logger.info("Testing BERT classification...")
        
        try:
            classifier = BERTTopicClassifier()
            await classifier.load_model()
            
            # Test specific topics
            bert_tests = [
                ("Technology and software development programming", "technology"),
                ("Business meeting with marketing and sales", "business"),
                ("Medical doctor healthcare treatment", "healthcare"),
                ("University education and academic learning", "education"),
                ("Movie entertainment and celebrity news", "entertainment"),
                ("Government politics and legal policy", "politics"),
                ("Personal family relationships and lifestyle", "personal"),
                ("Violent content with hate and harassment", "inappropriate")
            ]
            
            bert_results = []
            for text, expected in bert_tests:
                result = await classifier.detect(text)
                detected = result.metadata.get("top_topic", "unknown")
                
                bert_results.append({
                    "text": text,
                    "expected": expected,
                    "detected": detected,
                    "confidence": result.confidence,
                    "correct": detected == expected
                })
            
            correct_bert = sum(1 for r in bert_results if r["correct"])
            bert_accuracy = correct_bert / len(bert_results)
            
            logger.info(f"BERT classification accuracy: {bert_accuracy:.2f}")
            
            if bert_accuracy >= 0.60:  # 60% accuracy threshold for individual classifier
                logger.info("✅ BERT classification test passed")
                return {"status": "passed", "accuracy": bert_accuracy, "results": bert_results}
            else:
                logger.warning("❌ BERT classification accuracy below threshold")
                return {"status": "failed", "accuracy": bert_accuracy, "results": bert_results}
            
        except Exception as e:
            logger.error(f"❌ BERT classification test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_rule_based_classification(self) -> Dict[str, Any]:
        """Test 6: Rule-based classification functionality"""
        logger.info("Testing rule-based classification...")
        
        try:
            classifier = RuleBasedTopicClassifier()
            await classifier.load_model()
            
            # Test specific rule patterns
            rule_tests = [
                ("Business company meeting with financial profit", "business"),
                ("Software programming and computer technology", "technology"),
                ("Doctor medical treatment and healthcare", "healthcare"),
                ("University student academic education", "education"),
                ("Movie entertainment with celebrity music", "entertainment"),
                ("Government political election and policy", "politics"),
                ("Personal family relationship and private life", "personal"),
                ("Sexual violence and threatening harassment", "inappropriate")
            ]
            
            rule_results = []
            for text, expected in rule_tests:
                result = await classifier.detect(text)
                detected = result.metadata.get("top_topic", "unknown")
                
                rule_results.append({
                    "text": text,
                    "expected": expected,
                    "detected": detected,
                    "confidence": result.confidence,
                    "correct": detected == expected
                })
            
            correct_rules = sum(1 for r in rule_results if r["correct"])
            rule_accuracy = correct_rules / len(rule_results)
            
            logger.info(f"Rule-based classification accuracy: {rule_accuracy:.2f}")
            
            if rule_accuracy >= 0.70:  # 70% accuracy threshold for rule-based
                logger.info("✅ Rule-based classification test passed")
                return {"status": "passed", "accuracy": rule_accuracy, "results": rule_results}
            else:
                logger.warning("❌ Rule-based classification accuracy below threshold")
                return {"status": "failed", "accuracy": rule_accuracy, "results": rule_results}
            
        except Exception as e:
            logger.error(f"❌ Rule-based classification test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_inappropriate_content_blocking(self) -> Dict[str, Any]:
        """Test 7: Inappropriate content blocking"""
        logger.info("Testing inappropriate content blocking...")
        
        try:
            ensemble = TopicEnsemble()
            await ensemble.initialize()
            
            # Test inappropriate content detection
            inappropriate_tests = [
                ("Explicit sexual content and adult material", True),
                ("Violent harassment and hate speech", True),
                ("Threatening behavior and harmful content", True),
                ("Normal business conversation", False),
                ("Educational technology discussion", False),
                ("Healthcare advice and medical information", False)
            ]
            
            blocking_results = []
            for text, should_block in inappropriate_tests:
                result = await ensemble.classify_topic(text)
                
                topic = result.get("topic", "unknown")
                blocked = topic == "inappropriate"
                
                blocking_results.append({
                    "text": text,
                    "should_block": should_block,
                    "blocked": blocked,
                    "topic": topic,
                    "confidence": result.get("confidence", 0.0),
                    "correct": blocked == should_block
                })
            
            correct_blocking = sum(1 for r in blocking_results if r["correct"])
            blocking_accuracy = correct_blocking / len(blocking_results)
            
            logger.info(f"Inappropriate content blocking accuracy: {blocking_accuracy:.2f}")
            
            if blocking_accuracy >= 0.75:  # 75% accuracy threshold for blocking
                logger.info("✅ Inappropriate content blocking test passed")
                return {"status": "passed", "accuracy": blocking_accuracy, "results": blocking_results}
            else:
                logger.warning("❌ Inappropriate content blocking accuracy below threshold")
                return {"status": "failed", "accuracy": blocking_accuracy, "results": blocking_results}
            
        except Exception as e:
            logger.error(f"❌ Inappropriate content blocking test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_ensemble_voting(self) -> Dict[str, Any]:
        """Test 8: Ensemble weighted voting"""
        logger.info("Testing ensemble weighted voting...")
        
        try:
            ensemble = TopicEnsemble()
            await ensemble.initialize()
            
            # Test ensemble voting with clear signals
            voting_tests = [
                "Business finance and corporate marketing strategies",
                "Advanced machine learning and AI technology development",
                "Medical healthcare treatment and doctor consultations",
                "University education and academic research studies"
            ]
            
            voting_results = []
            for text in voting_tests:
                result = await ensemble.classify_topic(text)
                
                individual_results = result.get("individual_results", [])
                topic_votes = result.get("topic_votes", {})
                final_topic = result.get("topic", "unknown")
                
                voting_results.append({
                    "text": text,
                    "final_topic": final_topic,
                    "topic_votes": topic_votes,
                    "individual_results": individual_results,
                    "confidence": result.get("confidence", 0.0)
                })
            
            # Check that voting mechanism works
            has_voting_data = all(r["topic_votes"] for r in voting_results)
            has_individual_results = all(r["individual_results"] for r in voting_results)
            
            if has_voting_data and has_individual_results:
                logger.info("✅ Ensemble weighted voting test passed")
                return {"status": "passed", "voting_results": voting_results}
            else:
                logger.warning("❌ Ensemble weighted voting test failed")
                return {"status": "failed", "voting_results": voting_results}
            
        except Exception as e:
            logger.error(f"❌ Ensemble weighted voting test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_ensemble_health_check(self) -> Dict[str, Any]:
        """Test 9: Ensemble health check"""
        logger.info("Testing ensemble health check...")
        
        try:
            ensemble = TopicEnsemble()
            await ensemble.initialize()
            
            health_status = await ensemble.health_check()
            
            assert "healthy" in health_status, "Health status should include 'healthy' field"
            assert "total_classifiers" in health_status, "Health status should include classifier count"
            assert "classifier_status" in health_status, "Health status should include classifier status"
            
            assert health_status["total_classifiers"] == 2, "Should report 2 classifiers"
            assert health_status["loaded_classifiers"] >= 1, "Should have at least 1 loaded classifier"
            
            logger.info("✅ Ensemble health check test passed")
            return {"status": "passed", "health_status": health_status}
            
        except Exception as e:
            logger.error(f"❌ Ensemble health check test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def test_topic_distribution_analysis(self) -> Dict[str, Any]:
        """Test 10: Topic distribution analysis"""
        logger.info("Testing topic distribution analysis...")
        
        try:
            ensemble = TopicEnsemble()
            await ensemble.initialize()
            
            # Test various topics to build distribution
            distribution_texts = [
                "Business and finance",
                "Technology and programming",
                "Healthcare and medicine",
                "Education and learning",
                "Entertainment and movies",
                "Politics and government",
                "Personal life and family",
                "Inappropriate harmful content"
            ]
            
            # Classify all texts
            for text in distribution_texts:
                await ensemble.classify_topic(text)
            
            # Get performance stats
            stats = ensemble.get_performance_stats()
            
            assert "total_classifications" in stats, "Should track total classifications"
            assert "topic_distribution" in stats, "Should track topic distribution"
            assert stats["total_classifications"] >= len(distribution_texts), "Should have classified all texts"
            
            topic_distribution = stats["topic_distribution"]
            topics_found = len(topic_distribution)
            
            logger.info(f"Topic distribution analysis: {topics_found} unique topics found")
            
            if topics_found >= 3:  # Should find at least 3 different topics
                logger.info("✅ Topic distribution analysis test passed")
                return {"status": "passed", "topic_distribution": topic_distribution, "stats": stats}
            else:
                logger.warning("❌ Topic distribution analysis test failed")
                return {"status": "failed", "topic_distribution": topic_distribution, "stats": stats}
            
        except Exception as e:
            logger.error(f"❌ Topic distribution analysis test failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all topic ensemble tests"""
        logger.info("Starting topic classification ensemble test suite...")
        
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": {}
        }
        
        # List of test methods
        test_methods = [
            ("bert_classifier_init", self.test_bert_topic_classifier_initialization),
            ("rule_based_classifier_init", self.test_rule_based_classifier_initialization),
            ("topic_ensemble_init", self.test_topic_ensemble_initialization),
            ("topic_classification_accuracy", self.test_topic_classification_accuracy),
            ("bert_classification", self.test_bert_classification),
            ("rule_based_classification", self.test_rule_based_classification),
            ("inappropriate_content_blocking", self.test_inappropriate_content_blocking),
            ("ensemble_voting", self.test_ensemble_voting),
            ("ensemble_health_check", self.test_ensemble_health_check),
            ("topic_distribution_analysis", self.test_topic_distribution_analysis)
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
        
        logger.info(f"Topic classification ensemble test suite completed: {test_results['passed_tests']}/{test_results['total_tests']} tests passed ({success_rate:.1f}%)")
        
        return test_results

async def main():
    """Main test runner"""
    logger.info("Topic Classification Ensemble Test Suite")
    logger.info("=" * 50)
    
    test_runner = TestTopicEnsemble()
    results = await test_runner.run_all_tests()
    
    print("\n" + "=" * 50)
    print("TOPIC CLASSIFICATION ENSEMBLE TEST RESULTS")
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
        print("🎉 Topic classification ensemble implementation: SUCCESS")
        return 0
    else:
        print("❌ Topic classification ensemble implementation: NEEDS WORK")
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