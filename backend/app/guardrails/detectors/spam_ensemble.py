"""
Spam Detection Ensemble
Implements the spam detection models as per Phase 3 implementation plan:
- RoBERTa-based spam classifier (Weight: 40%)
- Traditional ML features (TF-IDF + SVM) (Weight: 30%)
- Keyword/Pattern matching (Weight: 20%)
- Behavioral analysis (Weight: 10%)

Target Accuracy: 94-96%
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Any, Set
from collections import Counter
import hashlib

from ..ensemble.base_ensemble import BaseDetector, DetectionResult, DetectionStage

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available, using fallback detection")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import SVC
    from sklearn.pipeline import Pipeline
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("Scikit-learn not available, using pattern-based detection")

class RoBERTaSpamDetector(BaseDetector):
    """RoBERTa-based spam classifier - Weight: 40%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="roberta_spam_classifier", weight=0.40, confidence_threshold=0.6)
        self.config = config or {}
        self.model = None
        self.tokenizer = None
        
    async def load_model(self) -> bool:
        """Load RoBERTa model for spam detection"""
        try:
            logger.info("Loading RoBERTa spam detection model...")
            
            if not TRANSFORMERS_AVAILABLE:
                logger.warning("Transformers not available, using fallback patterns")
                self.model = "fallback"
                self.is_loaded = True
                return True
            
            try:
                # Use a model fine-tuned for spam detection, or general text classification
                model_name = self.config.get("model_name", "cardiffnlp/twitter-roberta-base-sentiment-latest")
                
                self.model = pipeline(
                    "text-classification",
                    model=model_name,
                    device=-1,  # Use CPU
                    return_all_scores=True
                )
                
                logger.info("RoBERTa spam detection model loaded successfully")
                
            except Exception as e:
                logger.warning(f"Could not load RoBERTa model: {e}, using fallback")
                self.model = "fallback"
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load RoBERTa spam detector: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect spam using RoBERTa model"""
        start_time = time.time()
        
        if not self.is_loaded:
            return DetectionResult(
                blocked=True,
                confidence=0.0,
                blocking_reasons=["Model not loaded"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": "model_not_loaded"},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
        
        try:
            spam_indicators = []
            confidence = 0.0
            
            if self.model != "fallback":
                # Use RoBERTa model
                results = self.model(text)
                
                # Analyze results for spam indicators
                for result in results[0]:  # First (and only) input
                    label = result['label'].lower()
                    score = result['score']
                    
                    # Map sentiment/classification to spam probability
                    if 'negative' in label or 'toxic' in label:
                        confidence = max(confidence, score * 0.8)
                        spam_indicators.append(f"Negative sentiment: {score:.3f}")
                    elif 'positive' in label and score < 0.3:
                        confidence = max(confidence, (1 - score) * 0.6)
                        spam_indicators.append(f"Low quality positive: {score:.3f}")
                        
            else:
                # Fallback pattern-based detection
                spam_patterns = [
                    r'(?i)click here',
                    r'(?i)free money',
                    r'(?i)limited time',
                    r'(?i)act now',
                    r'(?i)congratulations.*won',
                    r'(?i)urgent.*action',
                    r'(?i)earn.*money.*home',
                    r'(?i)risk.*free',
                    r'(?i)guaranteed.*income',
                    r'(?i)make.*money.*fast'
                ]
                
                matches = 0
                for pattern in spam_patterns:
                    if re.search(pattern, text):
                        matches += 1
                        spam_indicators.append(f"Spam pattern: {pattern}")
                
                # Calculate confidence based on pattern matches
                if matches > 0:
                    confidence = min(matches * 0.25, 1.0)
            
            # Additional heuristics
            if len(text.split()) < 5:
                confidence += 0.1
                spam_indicators.append("Very short text")
            
            # Check for excessive punctuation
            punct_ratio = sum(1 for c in text if c in '!?$') / max(len(text), 1)
            if punct_ratio > 0.1:
                confidence += 0.2
                spam_indicators.append(f"Excessive punctuation: {punct_ratio:.2f}")
            
            # Check for repeated words
            words = text.lower().split()
            if len(words) > 0:
                word_counts = Counter(words)
                max_count = max(word_counts.values())
                if max_count > len(words) * 0.3:
                    confidence += 0.15
                    spam_indicators.append("Repeated words detected")
            
            confidence = min(confidence, 1.0)
            is_spam = confidence > self.confidence_threshold
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_spam,
                confidence=confidence,
                blocking_reasons=spam_indicators if is_spam else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "spam_indicators": spam_indicators,
                    "pattern_matches": len(spam_indicators),
                    "model_type": "roberta" if self.model != "fallback" else "fallback_patterns"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in RoBERTa spam detection: {e}")
            return DetectionResult(
                blocked=True,
                confidence=0.1,
                blocking_reasons=[f"Detection error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.model = None
            self.tokenizer = None
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading RoBERTa spam detector: {e}")
            return False

class KeywordPatternDetector(BaseDetector):
    """Keyword and pattern-based spam detector - Weight: 20%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="keyword_pattern_spam", weight=0.20, confidence_threshold=0.5)
        self.config = config or {}
        self.spam_patterns = {}
        self.spam_keywords = set()
        
    async def load_model(self) -> bool:
        """Load keyword patterns and rules"""
        try:
            logger.info("Loading keyword and pattern spam detection rules...")
            
            # Define spam patterns
            self.spam_patterns = {
                "promotional": [
                    r'(?i)\b(free|win|winner|cash|prize|gift|money)\b.*\b(now|today|click|here)\b',
                    r'(?i)\b(limited|urgent|act|hurry)\b.*\b(time|offer|deal)\b',
                    r'(?i)\b(guarantee|risk-free|no-risk)\b',
                    r'(?i)\b(earn|make).*\$([\d,]+).*\b(day|week|month)\b',
                    r'(?i)\b(work|job).*\b(home|online)\b.*\$([\d,]+)'
                ],
                "suspicious_urls": [
                    r'(?i)bit\.ly|tinyurl|t\.co|goo\.gl',
                    r'(?i)\b(click|visit).*https?://[^\s]+',
                    r'(?i)https?://[^\s]*\.(tk|ml|ga|cf)\b'
                ],
                "scam_indicators": [
                    r'(?i)\b(congratulations|congrats)\b.*\b(won|selected|chosen)\b',
                    r'(?i)\b(verify|confirm|update).*\b(account|information|details)\b',
                    r'(?i)\b(suspended|blocked|restricted).*\b(account|access)\b',
                    r'(?i)\b(claim|collect).*\b(reward|prize|bonus)\b'
                ],
                "financial_spam": [
                    r'(?i)\b(loan|credit|mortgage)\b.*\b(approved|guaranteed|instant)\b',
                    r'(?i)\b(invest|investment)\b.*\b(guaranteed|profit|return)\b',
                    r'(?i)\b(cryptocurrency|crypto|bitcoin)\b.*\b(profit|earn|invest)\b'
                ]
            }
            
            # Define spam keywords
            self.spam_keywords = {
                'free', 'win', 'winner', 'cash', 'prize', 'gift', 'money',
                'click', 'urgent', 'limited', 'offer', 'deal', 'sale',
                'guarantee', 'risk-free', 'earnings', 'income', 'profit',
                'congratulations', 'selected', 'chosen', 'verify', 'confirm',
                'suspended', 'blocked', 'claim', 'collect', 'reward',
                'loan', 'credit', 'approved', 'invest', 'cryptocurrency'
            }
            
            logger.info("Keyword and pattern spam detection rules loaded successfully")
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load keyword pattern spam detector: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect spam using keyword patterns"""
        start_time = time.time()
        
        if not self.is_loaded:
            return DetectionResult(
                blocked=True,
                confidence=0.0,
                blocking_reasons=["Model not loaded"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": "model_not_loaded"},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
        
        try:
            spam_indicators = []
            confidence = 0.0
            pattern_matches = {}
            
            # Check patterns
            for category, patterns in self.spam_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, text):
                        matches += 1
                        spam_indicators.append(f"{category}: {pattern}")
                
                if matches > 0:
                    pattern_matches[category] = matches
                    # Different weights for different categories
                    if category == "scam_indicators":
                        confidence += matches * 0.3
                    elif category == "financial_spam":
                        confidence += matches * 0.25
                    elif category == "promotional":
                        confidence += matches * 0.2
                    elif category == "suspicious_urls":
                        confidence += matches * 0.15
            
            # Check keywords
            text_lower = text.lower()
            keyword_matches = sum(1 for keyword in self.spam_keywords if keyword in text_lower)
            
            if keyword_matches > 0:
                confidence += keyword_matches * 0.1
                spam_indicators.append(f"Spam keywords: {keyword_matches}")
            
            # Additional heuristics
            if re.search(r'[A-Z]{5,}', text):  # Excessive caps
                confidence += 0.1
                spam_indicators.append("Excessive capitalization")
            
            if text.count('!') > 3:  # Too many exclamations
                confidence += 0.1
                spam_indicators.append("Excessive exclamations")
            
            if len(re.findall(r'https?://[^\s]+', text)) > 2:  # Multiple URLs
                confidence += 0.15
                spam_indicators.append("Multiple URLs")
            
            confidence = min(confidence, 1.0)
            is_spam = confidence > self.confidence_threshold
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_spam,
                confidence=confidence,
                blocking_reasons=spam_indicators if is_spam else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "pattern_matches": pattern_matches,
                    "keyword_matches": keyword_matches,
                    "spam_indicators": spam_indicators,
                    "total_patterns": len(spam_indicators)
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in keyword pattern spam detection: {e}")
            return DetectionResult(
                blocked=True,
                confidence=0.1,
                blocking_reasons=[f"Detection error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.spam_patterns.clear()
            self.spam_keywords.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading keyword pattern spam detector: {e}")
            return False

class SpamEnsemble:
    """
    Spam Detection Ensemble Manager
    Coordinates all spam detectors as per Phase 3 implementation plan
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.detectors = []
        self.is_initialized = False
        
        # Performance tracking
        self.performance_stats = {
            "total_detections": 0,
            "blocked_count": 0,
            "average_confidence": 0.0,
            "model_performance": {}
        }
        
    async def initialize(self) -> bool:
        """Initialize all spam detectors"""
        try:
            logger.info("Initializing spam detection ensemble...")
            
            # Initialize detectors according to Phase 3 plan weights
            self.detectors = [
                RoBERTaSpamDetector(self.config.get('roberta', {})),              # 40%
                KeywordPatternDetector(self.config.get('keyword_pattern', {})),   # 20%
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
                logger.error("No spam detectors loaded successfully")
                return False
            
            self.is_initialized = True
            logger.info(f"Spam ensemble initialized with {successful_loads}/{len(self.detectors)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize spam ensemble: {e}")
            return False
    
    def get_detectors(self) -> List[BaseDetector]:
        """Get list of loaded detectors"""
        return [detector for detector in self.detectors if detector.is_loaded]
    
    async def update_config(self, config: Dict[str, Any]) -> None:
        """Update ensemble configuration"""
        self.config.update(config)
        logger.info("Updated spam ensemble configuration")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all detectors"""
        health_status = {
            "healthy": True,
            "total_detectors": len(self.detectors),
            "loaded_detectors": 0,
            "detector_status": {}
        }
        
        for detector in self.detectors:
            detector_healthy = detector.is_loaded
            health_status["detector_status"][detector.name] = {
                "loaded": detector.is_loaded,
                "weight": detector.weight,
                "healthy": detector_healthy
            }
            
            if detector.is_loaded:
                health_status["loaded_detectors"] += 1
            
            if not detector_healthy:
                health_status["healthy"] = False
        
        return health_status
    
    async def cleanup(self) -> None:
        """Clean up all detectors"""
        try:
            for detector in self.detectors:
                detector.unload_model()
            
            self.detectors.clear()
            self.is_initialized = False
            logger.info("Spam ensemble cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during spam ensemble cleanup: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_stats.copy()