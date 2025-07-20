"""
PII Detection Ensemble
Implements the PII detection models as per the implementation plan:
- Microsoft Presidio Core (Weight: 40%)
- dslim/bert-large-NER (Weight: 25%)
- Flair NER (Weight: 20%)
- Custom Transformer NER (Weight: 15%)

Target Accuracy: 97-99%
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Any, Set
import spacy

from ..ensemble.base_ensemble import BaseDetector, DetectionResult, DetectionStage

logger = logging.getLogger(__name__)

class PresidioDetector(BaseDetector):
    """Microsoft Presidio Core detector - Weight: 40%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="presidio_core", weight=0.40, confidence_threshold=0.5)
        self.config = config or {}
        self.nlp = None
        self.pii_patterns = {}
        
    async def load_model(self) -> bool:
        """Load spaCy model for Presidio-like detection"""
        try:
            logger.info("Loading Presidio-like PII detector...")
            
            # Try to load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found, using fallback regex patterns")
                self.nlp = None
            
            # Define PII patterns
            self.pii_patterns = {
                "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                "phone": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
                "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                "credit_card": re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
                "ip_address": re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
                "url": re.compile(r'https?://[^\s]+'),
                "date": re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
                "zip_code": re.compile(r'\b\d{5}(?:-\d{4})?\b')
            }
            
            self.is_loaded = True
            logger.info("Presidio-like PII detector loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Presidio detector: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect PII using Presidio-like patterns"""
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
            detected_pii = {}
            blocking_reasons = []
            
            # Check regex patterns
            for pii_type, pattern in self.pii_patterns.items():
                matches = pattern.findall(text)
                if matches:
                    detected_pii[pii_type] = matches
                    blocking_reasons.append(f"{pii_type.upper()} detected")
            
            # Check named entities if spaCy is available
            if self.nlp:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ["PERSON", "ORG", "GPE", "LOC"]:
                        entity_type = ent.label_.lower()
                        if entity_type not in detected_pii:
                            detected_pii[entity_type] = []
                        detected_pii[entity_type].append(ent.text)
                        blocking_reasons.append(f"{entity_type.upper()} entity detected")
            
            # Calculate confidence based on number and types of PII detected
            confidence = 0.0
            if detected_pii:
                # Higher confidence for more sensitive PII types
                sensitive_types = ["ssn", "credit_card", "email", "phone"]
                confidence = min(len(detected_pii) * 0.3, 1.0)  # Base confidence
                
                # Boost confidence for sensitive types
                for pii_type in detected_pii:
                    if pii_type in sensitive_types:
                        confidence += 0.2
                
                confidence = min(confidence, 1.0)
            
            has_pii = len(detected_pii) > 0
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=has_pii and confidence > self.confidence_threshold,
                confidence=confidence,
                blocking_reasons=blocking_reasons,
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "detected_pii": detected_pii,
                    "pii_types": list(detected_pii.keys()),
                    "pii_count": len(detected_pii),
                    "spacy_available": self.nlp is not None
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in Presidio PII detection: {e}")
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
            self.nlp = None
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading Presidio detector: {e}")
            return False

class BERTNERDetector(BaseDetector):
    """dslim/bert-large-NER detector - Weight: 25%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="bert_large_ner", weight=0.25, confidence_threshold=0.5)
        self.config = config or {}
        self.model = None
        
    async def load_model(self) -> bool:
        """Load BERT NER model"""
        try:
            logger.info("Loading dslim/bert-large-NER model...")
            
            # Try to load transformers pipeline
            try:
                from transformers import pipeline
                self.model = pipeline(
                    "ner",
                    model="dslim/bert-large-NER",
                    aggregation_strategy="simple",
                    device=-1  # Use CPU
                )
            except Exception as e:
                logger.warning(f"Could not load BERT-large-NER model: {e}")
                # Use fallback regex-based detection
                self.model = "fallback"
            
            self.is_loaded = True
            logger.info("BERT NER detector loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load BERT NER detector: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect PII using BERT NER"""
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
            detected_entities = []
            blocking_reasons = []
            
            if self.model != "fallback":
                # Use BERT NER model
                entities = self.model(text)
                
                for entity in entities:
                    entity_type = entity['entity_group']
                    if entity_type in ['PER', 'PERSON', 'ORG', 'LOC', 'MISC']:
                        detected_entities.append({
                            'type': entity_type,
                            'text': entity['word'],
                            'confidence': entity['score']
                        })
                        blocking_reasons.append(f"{entity_type} entity detected")
            else:
                # Fallback pattern matching
                patterns = {
                    'PERSON': re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'),
                    'ORG': re.compile(r'\b[A-Z][a-z]+ (?:Inc|LLC|Corp|Company)\b'),
                    'EMAIL': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
                }
                
                for entity_type, pattern in patterns.items():
                    matches = pattern.findall(text)
                    for match in matches:
                        detected_entities.append({
                            'type': entity_type,
                            'text': match,
                            'confidence': 0.7  # Default confidence for pattern matching
                        })
                        blocking_reasons.append(f"{entity_type} pattern detected")
            
            # Calculate overall confidence
            if detected_entities:
                confidence = sum(e['confidence'] for e in detected_entities) / len(detected_entities)
            else:
                confidence = 0.0
            
            has_pii = len(detected_entities) > 0
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=has_pii and confidence > self.confidence_threshold,
                confidence=confidence,
                blocking_reasons=blocking_reasons,
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "detected_entities": detected_entities,
                    "entity_count": len(detected_entities),
                    "model_type": "bert_ner" if self.model != "fallback" else "fallback_patterns"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in BERT NER detection: {e}")
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
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading BERT NER detector: {e}")
            return False

class FlairNERDetector(BaseDetector):
    """Flair NER detector - Weight: 20%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="flair_ner", weight=0.20, confidence_threshold=0.5)
        self.config = config or {}
        self.model = None
        
    async def load_model(self) -> bool:
        """Load Flair NER model"""
        try:
            logger.info("Loading Flair NER model...")
            
            # Try to load Flair
            try:
                from flair.data import Sentence
                from flair.models import SequenceTagger
                
                self.model = SequenceTagger.load('ner')
                self.sentence_class = Sentence
            except Exception as e:
                logger.warning(f"Could not load Flair NER model: {e}")
                # Use fallback
                self.model = "fallback"
            
            self.is_loaded = True
            logger.info("Flair NER detector loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Flair NER detector: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect PII using Flair NER"""
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
            detected_entities = []
            blocking_reasons = []
            
            if self.model != "fallback":
                # Use Flair NER model
                sentence = self.sentence_class(text)
                self.model.predict(sentence)
                
                for entity in sentence.get_spans('ner'):
                    entity_type = entity.get_label('ner').value
                    confidence = entity.get_label('ner').score
                    
                    if entity_type in ['PER', 'ORG', 'LOC', 'MISC']:
                        detected_entities.append({
                            'type': entity_type,
                            'text': entity.text,
                            'confidence': confidence
                        })
                        blocking_reasons.append(f"{entity_type} entity detected")
            else:
                # Fallback using simple patterns
                patterns = {
                    'PER': re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'),
                    'ORG': re.compile(r'\b[A-Z][A-Za-z\s]+(?:Inc|LLC|Corp|Ltd|Company)\b'),
                    'LOC': re.compile(r'\b[A-Z][a-z]+ (?:Street|Avenue|Road|Drive|Boulevard)\b')
                }
                
                for entity_type, pattern in patterns.items():
                    matches = pattern.findall(text)
                    for match in matches:
                        detected_entities.append({
                            'type': entity_type,
                            'text': match,
                            'confidence': 0.6  # Lower confidence for fallback
                        })
                        blocking_reasons.append(f"{entity_type} pattern detected")
            
            # Calculate overall confidence
            if detected_entities:
                confidence = sum(e['confidence'] for e in detected_entities) / len(detected_entities)
            else:
                confidence = 0.0
            
            has_pii = len(detected_entities) > 0
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=has_pii and confidence > self.confidence_threshold,
                confidence=confidence,
                blocking_reasons=blocking_reasons,
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "detected_entities": detected_entities,
                    "entity_count": len(detected_entities),
                    "model_type": "flair_ner" if self.model != "fallback" else "fallback_patterns"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in Flair NER detection: {e}")
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
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading Flair NER detector: {e}")
            return False

class CustomTransformerNERDetector(BaseDetector):
    """Custom Transformer NER detector - Weight: 15%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="custom_transformer_ner", weight=0.15, confidence_threshold=0.5)
        self.config = config or {}
        self.model = None
        
    async def load_model(self) -> bool:
        """Load custom transformer NER model"""
        try:
            logger.info("Loading custom transformer NER model...")
            
            # Use a general NER model as fallback
            try:
                from transformers import pipeline
                self.model = pipeline(
                    "ner",
                    model="dbmdz/bert-large-cased-finetuned-conll03-english",
                    aggregation_strategy="simple",
                    device=-1  # Use CPU
                )
            except Exception as e:
                logger.warning(f"Could not load transformer NER model: {e}")
                self.model = "fallback"
            
            self.is_loaded = True
            logger.info("Custom transformer NER detector loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load custom transformer NER detector: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect PII using custom transformer NER"""
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
            detected_entities = []
            blocking_reasons = []
            
            if self.model != "fallback":
                # Use transformer NER model
                entities = self.model(text)
                
                for entity in entities:
                    entity_type = entity['entity_group']
                    if entity_type in ['PER', 'ORG', 'LOC', 'MISC']:
                        detected_entities.append({
                            'type': entity_type,
                            'text': entity['word'],
                            'confidence': entity['score']
                        })
                        blocking_reasons.append(f"{entity_type} entity detected")
            else:
                # Fallback context-aware detection
                context_patterns = {
                    'PERSON': re.compile(r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-z]+\b'),
                    'LOCATION': re.compile(r'\b[A-Z][a-z]+,\s+[A-Z]{2}\b'),  # City, State
                    'ORGANIZATION': re.compile(r'\b[A-Z][a-zA-Z\s]+\s+(?:University|College|Hospital|Bank)\b')
                }
                
                for entity_type, pattern in context_patterns.items():
                    matches = pattern.findall(text)
                    for match in matches:
                        detected_entities.append({
                            'type': entity_type,
                            'text': match,
                            'confidence': 0.8  # Higher confidence for context-aware patterns
                        })
                        blocking_reasons.append(f"{entity_type} context pattern detected")
            
            # Calculate overall confidence
            if detected_entities:
                confidence = sum(e['confidence'] for e in detected_entities) / len(detected_entities)
            else:
                confidence = 0.0
            
            has_pii = len(detected_entities) > 0
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=has_pii and confidence > self.confidence_threshold,
                confidence=confidence,
                blocking_reasons=blocking_reasons,
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "detected_entities": detected_entities,
                    "entity_count": len(detected_entities),
                    "model_type": "transformer_ner" if self.model != "fallback" else "context_patterns"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in custom transformer NER detection: {e}")
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
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading custom transformer NER detector: {e}")
            return False

class PIIEnsemble:
    """
    PII Detection Ensemble Manager
    Coordinates all PII detectors as per implementation plan
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
        """Initialize all PII detectors"""
        try:
            logger.info("Initializing PII detection ensemble...")
            
            # Initialize detectors according to implementation plan weights
            self.detectors = [
                PresidioDetector(self.config.get('presidio', {})),              # 40%
                BERTNERDetector(self.config.get('bert_ner', {})),              # 25%
                FlairNERDetector(self.config.get('flair_ner', {})),            # 20%
                CustomTransformerNERDetector(self.config.get('custom_ner', {})) # 15%
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
                logger.error("No PII detectors loaded successfully")
                return False
            
            self.is_initialized = True
            logger.info(f"PII ensemble initialized with {successful_loads}/{len(self.detectors)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PII ensemble: {e}")
            return False
    
    def get_detectors(self) -> List[BaseDetector]:
        """Get list of loaded detectors"""
        return [detector for detector in self.detectors if detector.is_loaded]
    
    async def update_config(self, config: Dict[str, Any]) -> None:
        """Update ensemble configuration"""
        self.config.update(config)
        logger.info("Updated PII ensemble configuration")
    
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
            logger.info("PII ensemble cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during PII ensemble cleanup: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_stats.copy()