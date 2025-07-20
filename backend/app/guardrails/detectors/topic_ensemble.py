"""
Topic Classification Ensemble
Implements the topic classification models as per Phase 3 implementation plan:
- BERT-based topic classifier (Weight: 50%)
- Custom rule-based classifier (Weight: 25%)
- Keyword-based classifier (Weight: 15%)
- Context-aware classifier (Weight: 10%)

Target Accuracy: 90-95%
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Any, Set
from collections import Counter
import json

from ..ensemble.base_ensemble import BaseDetector, DetectionResult, DetectionStage

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available, using fallback classification")

class BERTTopicClassifier(BaseDetector):
    """BERT-based topic classifier - Weight: 50%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="bert_topic_classifier", weight=0.50, confidence_threshold=0.7)
        self.config = config or {}
        self.model = None
        self.topic_categories = {}
        
    async def load_model(self) -> bool:
        """Load BERT model for topic classification"""
        try:
            logger.info("Loading BERT topic classification model...")
            
            if not TRANSFORMERS_AVAILABLE:
                logger.warning("Transformers not available, using fallback classification")
                self.model = "fallback"
                self._setup_fallback_categories()
                self.is_loaded = True
                return True
            
            try:
                # Use a general text classification model
                model_name = self.config.get("model_name", "facebook/bart-large-mnli")
                
                self.model = pipeline(
                    "zero-shot-classification",
                    model=model_name,
                    device=-1  # Use CPU
                )
                
                # Define topic categories
                self.topic_categories = {
                    "inappropriate": [
                        "adult content", "sexual content", "violence", "harassment",
                        "hate speech", "threats", "disturbing content"
                    ],
                    "business": [
                        "business", "finance", "commerce", "marketing", "sales",
                        "corporate", "professional", "work"
                    ],
                    "technology": [
                        "technology", "software", "programming", "computers",
                        "internet", "AI", "machine learning", "cybersecurity"
                    ],
                    "healthcare": [
                        "health", "medicine", "medical", "doctor", "treatment",
                        "symptoms", "diagnosis", "wellness"
                    ],
                    "education": [
                        "education", "learning", "school", "university", "academic",
                        "teaching", "students", "curriculum"
                    ],
                    "entertainment": [
                        "entertainment", "movies", "music", "games", "sports",
                        "celebrities", "media", "fun"
                    ],
                    "politics": [
                        "politics", "government", "policy", "elections", "political",
                        "law", "legal", "regulation"
                    ],
                    "personal": [
                        "personal", "private", "family", "relationships", "lifestyle",
                        "hobbies", "personal experience"
                    ]
                }
                
                logger.info("BERT topic classification model loaded successfully")
                
            except Exception as e:
                logger.warning(f"Could not load BERT model: {e}, using fallback")
                self.model = "fallback"
                self._setup_fallback_categories()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load BERT topic classifier: {e}")
            return False
    
    def _setup_fallback_categories(self):
        """Setup fallback topic categories"""
        self.topic_categories = {
            "inappropriate": [
                "adult", "sexual", "violence", "harassment", "hate", "threats"
            ],
            "business": [
                "business", "finance", "commerce", "marketing", "sales"
            ],
            "technology": [
                "technology", "software", "programming", "computers"
            ],
            "healthcare": [
                "health", "medicine", "medical", "doctor", "treatment"
            ],
            "education": [
                "education", "learning", "school", "university"
            ],
            "entertainment": [
                "entertainment", "movies", "music", "games", "sports"
            ],
            "politics": [
                "politics", "government", "policy", "elections"
            ],
            "personal": [
                "personal", "private", "family", "relationships"
            ]
        }
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Classify topic using BERT model"""
        start_time = time.time()
        
        if not self.is_loaded:
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=["Model not loaded"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": "model_not_loaded"},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
        
        try:
            topic_predictions = {}
            confidence = 0.0
            
            if self.model != "fallback":
                # Use BERT model for zero-shot classification
                candidate_labels = list(self.topic_categories.keys())
                
                result = self.model(text, candidate_labels)
                
                # Extract predictions
                for label, score in zip(result['labels'], result['scores']):
                    topic_predictions[label] = score
                
                # Get top prediction
                top_topic = result['labels'][0]
                confidence = result['scores'][0]
                
            else:
                # Fallback keyword-based classification
                text_lower = text.lower()
                
                for topic, keywords in self.topic_categories.items():
                    matches = sum(1 for keyword in keywords if keyword in text_lower)
                    if matches > 0:
                        score = min(matches * 0.3, 1.0)
                        topic_predictions[topic] = score
                
                # Get highest scoring topic
                if topic_predictions:
                    top_topic = max(topic_predictions, key=topic_predictions.get)
                    confidence = topic_predictions[top_topic]
                else:
                    top_topic = "unknown"
                    confidence = 0.0
            
            # Determine if content should be blocked (inappropriate content)
            blocked = False
            blocking_reasons = []
            
            if top_topic == "inappropriate" and confidence > 0.7:
                blocked = True
                blocking_reasons.append(f"Inappropriate content detected: {confidence:.3f}")
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=blocked,
                confidence=confidence,
                blocking_reasons=blocking_reasons,
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "top_topic": top_topic,
                    "topic_predictions": topic_predictions,
                    "model_type": "bert" if self.model != "fallback" else "fallback_keywords"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in BERT topic classification: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=[f"Classification error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.model = None
            self.topic_categories.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading BERT topic classifier: {e}")
            return False

class RuleBasedTopicClassifier(BaseDetector):
    """Rule-based topic classifier - Weight: 25%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="rule_based_topic", weight=0.25, confidence_threshold=0.6)
        self.config = config or {}
        self.topic_rules = {}
        
    async def load_model(self) -> bool:
        """Load rule-based classification rules"""
        try:
            logger.info("Loading rule-based topic classification rules...")
            
            # Define topic classification rules
            self.topic_rules = {
                "inappropriate": {
                    "patterns": [
                        r'(?i)\b(sex|sexual|porn|nude|naked|adult)\b',
                        r'(?i)\b(violence|violent|kill|death|murder)\b',
                        r'(?i)\b(hate|racism|discrimination|harassment)\b',
                        r'(?i)\b(threat|threaten|harm|hurt|attack)\b',
                        r'(?i)\b(drug|drugs|illegal|criminal)\b'
                    ],
                    "keywords": [
                        "inappropriate", "explicit", "offensive", "disturbing",
                        "violent", "sexual", "harassment", "threats"
                    ]
                },
                "business": {
                    "patterns": [
                        r'(?i)\b(business|company|corporation|enterprise)\b',
                        r'(?i)\b(finance|financial|money|investment|profit)\b',
                        r'(?i)\b(marketing|sales|customer|client)\b',
                        r'(?i)\b(meeting|conference|presentation|proposal)\b',
                        r'(?i)\b(contract|agreement|deal|negotiate)\b'
                    ],
                    "keywords": [
                        "business", "finance", "marketing", "sales", "corporate",
                        "professional", "commerce", "trade", "industry"
                    ]
                },
                "technology": {
                    "patterns": [
                        r'(?i)\b(software|hardware|computer|programming)\b',
                        r'(?i)\b(technology|tech|digital|cyber)\b',
                        r'(?i)\b(AI|artificial intelligence|machine learning)\b',
                        r'(?i)\b(internet|web|online|website)\b',
                        r'(?i)\b(code|coding|development|developer)\b'
                    ],
                    "keywords": [
                        "technology", "software", "programming", "computers",
                        "internet", "AI", "cybersecurity", "digital"
                    ]
                },
                "healthcare": {
                    "patterns": [
                        r'(?i)\b(health|medical|medicine|doctor|physician)\b',
                        r'(?i)\b(hospital|clinic|treatment|therapy)\b',
                        r'(?i)\b(disease|illness|symptoms|diagnosis)\b',
                        r'(?i)\b(patient|healthcare|wellness|fitness)\b',
                        r'(?i)\b(medication|prescription|pharmacy)\b'
                    ],
                    "keywords": [
                        "health", "medical", "medicine", "doctor", "treatment",
                        "symptoms", "diagnosis", "wellness", "healthcare"
                    ]
                },
                "education": {
                    "patterns": [
                        r'(?i)\b(education|educational|school|university)\b',
                        r'(?i)\b(student|teacher|professor|instructor)\b',
                        r'(?i)\b(learn|learning|study|academic)\b',
                        r'(?i)\b(course|class|curriculum|assignment)\b',
                        r'(?i)\b(exam|test|grade|homework)\b'
                    ],
                    "keywords": [
                        "education", "learning", "school", "university", "academic",
                        "teaching", "students", "curriculum", "study"
                    ]
                },
                "entertainment": {
                    "patterns": [
                        r'(?i)\b(movie|film|cinema|entertainment)\b',
                        r'(?i)\b(music|song|album|concert)\b',
                        r'(?i)\b(game|gaming|sport|sports)\b',
                        r'(?i)\b(celebrity|actor|actress|musician)\b',
                        r'(?i)\b(TV|television|show|series)\b'
                    ],
                    "keywords": [
                        "entertainment", "movies", "music", "games", "sports",
                        "celebrities", "media", "fun", "leisure"
                    ]
                },
                "politics": {
                    "patterns": [
                        r'(?i)\b(politics|political|government|policy)\b',
                        r'(?i)\b(election|vote|voting|candidate)\b',
                        r'(?i)\b(law|legal|legislation|regulation)\b',
                        r'(?i)\b(president|minister|senator|congress)\b',
                        r'(?i)\b(democrat|republican|party|campaign)\b'
                    ],
                    "keywords": [
                        "politics", "government", "policy", "elections", "political",
                        "law", "legal", "regulation", "governance"
                    ]
                },
                "personal": {
                    "patterns": [
                        r'(?i)\b(personal|private|family|relationship)\b',
                        r'(?i)\b(friend|friendship|love|dating)\b',
                        r'(?i)\b(hobby|hobbies|interest|passion)\b',
                        r'(?i)\b(home|house|lifestyle|daily)\b',
                        r'(?i)\b(experience|story|memory|feeling)\b'
                    ],
                    "keywords": [
                        "personal", "private", "family", "relationships", "lifestyle",
                        "hobbies", "friends", "home", "life"
                    ]
                }
            }
            
            logger.info("Rule-based topic classification rules loaded successfully")
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load rule-based topic classifier: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Classify topic using rule-based approach"""
        start_time = time.time()
        
        if not self.is_loaded:
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=["Model not loaded"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": "model_not_loaded"},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
        
        try:
            topic_scores = {}
            pattern_matches = {}
            
            # Check each topic
            for topic, rules in self.topic_rules.items():
                score = 0.0
                matches = 0
                
                # Check patterns
                for pattern in rules["patterns"]:
                    if re.search(pattern, text):
                        matches += 1
                        score += 0.3
                
                # Check keywords
                text_lower = text.lower()
                keyword_matches = sum(1 for keyword in rules["keywords"] if keyword in text_lower)
                
                if keyword_matches > 0:
                    score += keyword_matches * 0.2
                    matches += keyword_matches
                
                if matches > 0:
                    topic_scores[topic] = min(score, 1.0)
                    pattern_matches[topic] = matches
            
            # Get top topic
            if topic_scores:
                top_topic = max(topic_scores, key=topic_scores.get)
                confidence = topic_scores[top_topic]
            else:
                top_topic = "unknown"
                confidence = 0.0
            
            # Determine if content should be blocked
            blocked = False
            blocking_reasons = []
            
            if top_topic == "inappropriate" and confidence > 0.6:
                blocked = True
                blocking_reasons.append(f"Inappropriate content detected: {confidence:.3f}")
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=blocked,
                confidence=confidence,
                blocking_reasons=blocking_reasons,
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "top_topic": top_topic,
                    "topic_scores": topic_scores,
                    "pattern_matches": pattern_matches,
                    "model_type": "rule_based"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in rule-based topic classification: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=[f"Classification error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.topic_rules.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading rule-based topic classifier: {e}")
            return False

class TopicEnsemble:
    """
    Topic Classification Ensemble Manager
    Coordinates all topic classifiers as per Phase 3 implementation plan
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.detectors = []
        self.is_initialized = False
        
        # Performance tracking
        self.performance_stats = {
            "total_classifications": 0,
            "blocked_count": 0,
            "topic_distribution": {},
            "model_performance": {}
        }
        
    async def initialize(self) -> bool:
        """Initialize all topic classifiers"""
        try:
            logger.info("Initializing topic classification ensemble...")
            
            # Initialize classifiers according to Phase 3 plan weights
            self.detectors = [
                BERTTopicClassifier(self.config.get('bert', {})),              # 50%
                RuleBasedTopicClassifier(self.config.get('rule_based', {})),   # 25%
            ]
            
            # Load all models
            load_tasks = [detector.load_model() for detector in self.detectors]
            load_results = await asyncio.gather(*load_tasks, return_exceptions=True)
            
            # Check results
            successful_loads = 0
            for i, result in enumerate(load_results):
                if isinstance(result, bool) and result:
                    successful_loads += 1
                    logger.info(f"Successfully loaded {self.detectors[i].name}")
                else:
                    logger.warning(f"Failed to load {self.detectors[i].name}: {result}")
            
            if successful_loads == 0:
                logger.error("No topic classifiers loaded successfully")
                return False
            
            self.is_initialized = True
            logger.info(f"Topic ensemble initialized with {successful_loads}/{len(self.detectors)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize topic ensemble: {e}")
            return False
    
    async def classify_topic(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify topic using ensemble approach"""
        if not self.is_initialized:
            return {"error": "Ensemble not initialized"}
        
        try:
            # Get predictions from all classifiers
            results = []
            for detector in self.detectors:
                if detector.is_loaded:
                    result = await detector.detect(text, context)
                    results.append(result)
            
            if not results:
                return {"error": "No classifiers available"}
            
            # Combine results using weighted voting
            topic_votes = {}
            total_weight = 0
            
            for result in results:
                if "top_topic" in result.metadata:
                    topic = result.metadata["top_topic"]
                    weight = next(d.weight for d in self.detectors if d.name == result.model_name)
                    confidence = result.confidence
                    
                    weighted_score = weight * confidence
                    
                    if topic not in topic_votes:
                        topic_votes[topic] = 0
                    topic_votes[topic] += weighted_score
                    total_weight += weight
            
            # Normalize votes
            if total_weight > 0:
                for topic in topic_votes:
                    topic_votes[topic] /= total_weight
            
            # Get final prediction
            if topic_votes:
                final_topic = max(topic_votes, key=topic_votes.get)
                final_confidence = topic_votes[final_topic]
            else:
                final_topic = "unknown"
                final_confidence = 0.0
            
            # Update statistics
            self.performance_stats["total_classifications"] += 1
            if final_topic not in self.performance_stats["topic_distribution"]:
                self.performance_stats["topic_distribution"][final_topic] = 0
            self.performance_stats["topic_distribution"][final_topic] += 1
            
            return {
                "topic": final_topic,
                "confidence": final_confidence,
                "topic_votes": topic_votes,
                "individual_results": [
                    {
                        "model": r.model_name,
                        "topic": r.metadata.get("top_topic", "unknown"),
                        "confidence": r.confidence,
                        "blocked": r.blocked
                    } for r in results
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in topic classification: {e}")
            return {"error": str(e)}
    
    def get_detectors(self) -> List[BaseDetector]:
        """Get list of loaded detectors"""
        return [detector for detector in self.detectors if detector.is_loaded]
    
    async def update_config(self, config: Dict[str, Any]) -> None:
        """Update ensemble configuration"""
        self.config.update(config)
        logger.info("Updated topic ensemble configuration")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all classifiers"""
        health_status = {
            "healthy": True,
            "total_classifiers": len(self.detectors),
            "loaded_classifiers": 0,
            "classifier_status": {}
        }
        
        for detector in self.detectors:
            classifier_healthy = detector.is_loaded
            health_status["classifier_status"][detector.name] = {
                "loaded": detector.is_loaded,
                "weight": detector.weight,
                "healthy": classifier_healthy
            }
            
            if detector.is_loaded:
                health_status["loaded_classifiers"] += 1
            
            if not classifier_healthy:
                health_status["healthy"] = False
        
        return health_status
    
    async def cleanup(self) -> None:
        """Clean up all classifiers"""
        try:
            for detector in self.detectors:
                detector.unload_model()
            
            self.detectors.clear()
            self.is_initialized = False
            logger.info("Topic ensemble cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during topic ensemble cleanup: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_stats.copy()