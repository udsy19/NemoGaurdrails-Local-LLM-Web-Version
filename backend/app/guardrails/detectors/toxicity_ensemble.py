"""
Toxicity Detection Ensemble
Implements the toxicity detection models as per the implementation plan:
- unitary/toxic-bert (Weight: 35%)
- martin-ha/toxic-comment-model (Weight: 30%) 
- nicholasKluge/ToxicityModel (Weight: 25%)
- Custom DistilBERT Model (Weight: 10%)

Target Accuracy: 96-98%
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

from ..ensemble.base_ensemble import BaseDetector, DetectionResult, DetectionStage

logger = logging.getLogger(__name__)

class ToxicBERTDetector(BaseDetector):
    """unitary/toxic-bert detector - Weight: 35%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="toxic_bert", weight=0.35, confidence_threshold=0.5)
        self.config = config or {}
        self.model = None
        self.tokenizer = None
        
    async def load_model(self) -> bool:
        """Load the unitary/toxic-bert model"""
        try:
            logger.info("Loading unitary/toxic-bert model...")
            
            # Use transformers pipeline for simplicity
            self.model = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=0 if torch.cuda.is_available() else -1,
                batch_size=1
            )
            
            self.is_loaded = True
            logger.info("toxic-bert model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load toxic-bert model: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect toxicity using toxic-bert"""
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
            # Run inference
            result = self.model(text)
            
            # toxic-bert returns TOXIC or NOT_TOXIC
            is_toxic = result[0]['label'] == 'TOXIC'
            confidence = result[0]['score']
            
            # If prediction is NOT_TOXIC, invert confidence
            if not is_toxic:
                confidence = 1.0 - confidence
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_toxic and confidence > self.confidence_threshold,
                confidence=confidence,
                blocking_reasons=["Toxic content detected"] if is_toxic else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "raw_prediction": result[0],
                    "model_type": "transformer",
                    "model_size": "420MB"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in toxic-bert detection: {e}")
            return DetectionResult(
                blocked=True,  # Fail safe
                confidence=0.1,
                blocking_reasons=[f"Detection error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def unload_model(self) -> bool:
        """Unload the model to free memory"""
        try:
            self.model = None
            self.tokenizer = None
            self.is_loaded = False
            
            # Force garbage collection
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return True
        except Exception as e:
            logger.error(f"Error unloading toxic-bert model: {e}")
            return False

class MartinHaToxicDetector(BaseDetector):
    """martin-ha/toxic-comment-model detector - Weight: 30%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="martin_ha_toxic", weight=0.30, confidence_threshold=0.5)
        self.config = config or {}
        self.model = None
        
    async def load_model(self) -> bool:
        """Load the martin-ha/toxic-comment-model"""
        try:
            logger.info("Loading martin-ha/toxic-comment-model...")
            
            self.model = pipeline(
                "text-classification",
                model="martin-ha/toxic-comment-model",
                device=0 if torch.cuda.is_available() else -1,
                batch_size=1
            )
            
            self.is_loaded = True
            logger.info("martin-ha toxic model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load martin-ha toxic model: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect toxicity using martin-ha model"""
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
            result = self.model(text)
            
            # Assuming this model outputs TOXIC/NOT_TOXIC
            is_toxic = result[0]['label'] == 'TOXIC'
            confidence = result[0]['score']
            
            if not is_toxic:
                confidence = 1.0 - confidence
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_toxic and confidence > self.confidence_threshold,
                confidence=confidence,
                blocking_reasons=["Toxic content detected"] if is_toxic else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "raw_prediction": result[0],
                    "model_type": "transformer",
                    "model_size": "500MB"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in martin-ha toxic detection: {e}")
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
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return True
        except Exception as e:
            logger.error(f"Error unloading martin-ha model: {e}")
            return False

class NicholasKlugeToxicDetector(BaseDetector):
    """nicholasKluge/ToxicityModel detector - Weight: 25%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="nicholas_kluge_toxic", weight=0.25, confidence_threshold=0.5)
        self.config = config or {}
        self.model = None
        
    async def load_model(self) -> bool:
        """Load the nicholasKluge/ToxicityModel"""
        try:
            logger.info("Loading nicholasKluge/ToxicityModel...")
            
            self.model = pipeline(
                "text-classification",
                model="nicholasKluge/ToxicityModel",
                device=0 if torch.cuda.is_available() else -1,
                batch_size=1
            )
            
            self.is_loaded = True
            logger.info("nicholasKluge toxicity model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load nicholasKluge model: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect toxicity using nicholasKluge model"""
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
            result = self.model(text)
            
            # This is a RoBERTa-based model, check output format
            is_toxic = result[0]['label'] in ['TOXIC', 'toxic', '1']
            confidence = result[0]['score']
            
            if not is_toxic:
                confidence = 1.0 - confidence
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_toxic and confidence > self.confidence_threshold,
                confidence=confidence,
                blocking_reasons=["Toxic content detected"] if is_toxic else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "raw_prediction": result[0],
                    "model_type": "roberta",
                    "model_size": "450MB"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in nicholasKluge detection: {e}")
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
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return True
        except Exception as e:
            logger.error(f"Error unloading nicholasKluge model: {e}")
            return False

class CustomDistilBERTDetector(BaseDetector):
    """Custom DistilBERT detector - Weight: 10%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="custom_distilbert", weight=0.10, confidence_threshold=0.5)
        self.config = config or {}
        self.model = None
        
    async def load_model(self) -> bool:
        """Load a custom DistilBERT model (using distilbert-base-uncased as fallback)"""
        try:
            logger.info("Loading custom DistilBERT model...")
            
            # Use a pre-trained DistilBERT model as fallback
            # In production, this would be your custom fine-tuned model
            self.model = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if torch.cuda.is_available() else -1,
                batch_size=1
            )
            
            self.is_loaded = True
            logger.info("Custom DistilBERT model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load custom DistilBERT model: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect toxicity using custom DistilBERT"""
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
            result = self.model(text)
            
            # This is using sentiment model as fallback - NEGATIVE indicates potentially toxic
            is_toxic = result[0]['label'] == 'NEGATIVE'
            confidence = result[0]['score']
            
            # For sentiment model, adjust confidence interpretation
            if is_toxic:
                confidence = min(confidence * 0.7, 0.8)  # Lower confidence since this is adapted
            else:
                confidence = 1.0 - confidence
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_toxic and confidence > self.confidence_threshold,
                confidence=confidence,
                blocking_reasons=["Potentially toxic content"] if is_toxic else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "raw_prediction": result[0],
                    "model_type": "distilbert",
                    "model_size": "250MB",
                    "note": "adapted_sentiment_model"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in custom DistilBERT detection: {e}")
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
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            return True
        except Exception as e:
            logger.error(f"Error unloading custom DistilBERT model: {e}")
            return False

class ToxicityEnsemble:
    """
    Toxicity Detection Ensemble Manager
    Coordinates all toxicity detectors as per implementation plan
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
        """Initialize all toxicity detectors"""
        try:
            logger.info("Initializing toxicity detection ensemble...")
            
            # Initialize detectors according to implementation plan weights
            self.detectors = [
                ToxicBERTDetector(self.config.get('toxic_bert', {})),           # 35%
                MartinHaToxicDetector(self.config.get('martin_ha', {})),        # 30%
                NicholasKlugeToxicDetector(self.config.get('nicholas_kluge', {})), # 25%
                CustomDistilBERTDetector(self.config.get('custom_distilbert', {})) # 10%
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
                    logger.error(f"Failed to load {self.detectors[i].name}: {result}")
            
            if successful_loads == 0:
                logger.error("No toxicity detectors loaded successfully")
                return False
            
            self.is_initialized = True
            logger.info(f"Toxicity ensemble initialized with {successful_loads}/{len(self.detectors)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize toxicity ensemble: {e}")
            return False
    
    def get_detectors(self) -> List[BaseDetector]:
        """Get list of loaded detectors"""
        return [detector for detector in self.detectors if detector.is_loaded]
    
    async def update_config(self, config: Dict[str, Any]) -> None:
        """Update ensemble configuration"""
        self.config.update(config)
        # In a full implementation, this would update detector configurations
        logger.info("Updated toxicity ensemble configuration")
    
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
            logger.info("Toxicity ensemble cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during toxicity ensemble cleanup: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_stats.copy()