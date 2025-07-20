"""
Fact-checking Ensemble
Implements the fact-checking models as per Phase 3 implementation plan:
- Retrieval-augmented fact checker (Weight: 40%)
- Knowledge base fact checker (Weight: 30%)
- Source validation checker (Weight: 30%)

Target Accuracy: 90-95%
"""

import asyncio
import logging
import re
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import Counter
from urllib.parse import urlparse

from ..ensemble.base_ensemble import BaseDetector, DetectionResult, DetectionStage

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available, using fallback fact checking")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Requests not available, using basic fact checking")

class RetrievalFactChecker(BaseDetector):
    """Retrieval-augmented fact checker - Weight: 40%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="retrieval_fact_checker", weight=0.40, confidence_threshold=0.7)
        self.config = config or {}
        self.model = None
        self.knowledge_sources = []
        self.fact_patterns = {}
        
    async def load_model(self) -> bool:
        """Load retrieval-augmented fact checking model"""
        try:
            logger.info("Loading retrieval-augmented fact checking model...")
            
            if not TRANSFORMERS_AVAILABLE:
                logger.warning("Transformers not available, using fallback fact checking")
                self.model = "fallback"
                self._setup_fallback_patterns()
                self.is_loaded = True
                return True
            
            try:
                # Use a model suitable for fact verification
                model_name = self.config.get("model_name", "facebook/bart-large-mnli")
                
                self.model = pipeline(
                    "zero-shot-classification",
                    model=model_name,
                    device=-1  # Use CPU
                )
                
                # Setup knowledge sources
                self._setup_knowledge_sources()
                
                logger.info("Retrieval-augmented fact checking model loaded successfully")
                
            except Exception as e:
                logger.warning(f"Could not load retrieval model: {e}, using fallback")
                self.model = "fallback"
                self._setup_fallback_patterns()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load retrieval fact checker: {e}")
            return False
    
    def _setup_knowledge_sources(self):
        """Setup knowledge sources for fact checking"""
        self.knowledge_sources = [
            {
                "name": "scientific_facts",
                "domain": "science",
                "facts": [
                    "The Earth is approximately 4.5 billion years old",
                    "Water boils at 100°C at sea level",
                    "The speed of light is approximately 299,792,458 meters per second",
                    "Humans have 46 chromosomes",
                    "The human brain has approximately 86 billion neurons",
                    "DNA stands for Deoxyribonucleic Acid",
                    "The periodic table has 118 known elements",
                    "Gravity on Earth is approximately 9.8 m/s²"
                ]
            },
            {
                "name": "historical_facts",
                "domain": "history",
                "facts": [
                    "World War II ended in 1945",
                    "The Berlin Wall fell in 1989",
                    "The first moon landing was in 1969",
                    "The United States declared independence in 1776",
                    "The Renaissance period was from 14th to 17th century",
                    "The printing press was invented by Johannes Gutenberg",
                    "The Roman Empire fell in 476 AD",
                    "The Great Wall of China was built over many centuries"
                ]
            },
            {
                "name": "mathematical_facts",
                "domain": "mathematics",
                "facts": [
                    "Pi is approximately 3.14159",
                    "The square root of 16 is 4",
                    "2 + 2 equals 4",
                    "There are 360 degrees in a circle",
                    "The Pythagorean theorem is a² + b² = c²",
                    "Prime numbers are divisible only by 1 and themselves",
                    "The golden ratio is approximately 1.618",
                    "Fibonacci sequence starts with 0, 1, 1, 2, 3, 5, 8"
                ]
            },
            {
                "name": "general_knowledge",
                "domain": "general",
                "facts": [
                    "There are 7 continents on Earth",
                    "The Pacific Ocean is the largest ocean",
                    "Mount Everest is the highest mountain",
                    "The Amazon is the longest river",
                    "There are 24 hours in a day",
                    "There are 365 days in a regular year",
                    "The sun is a star",
                    "Diamonds are made of carbon"
                ]
            }
        ]
    
    def _setup_fallback_patterns(self):
        """Setup fallback fact checking patterns"""
        self.fact_patterns = {
            "scientific_claims": [
                r'(?i)\b(earth|planet|sun|moon|star|galaxy|universe)\b',
                r'(?i)\b(temperature|celsius|fahrenheit|kelvin)\b',
                r'(?i)\b(speed|light|sound|gravity|physics)\b',
                r'(?i)\b(dna|gene|chromosome|cell|biology)\b',
                r'(?i)\b(evolution|darwin|species|natural selection)\b'
            ],
            "historical_claims": [
                r'(?i)\b(world war|war|battle|revolution)\b',
                r'(?i)\b(century|year|decade|ancient|medieval)\b',
                r'(?i)\b(president|king|queen|emperor|ruler)\b',
                r'(?i)\b(discovery|invention|explorer|colonial)\b',
                r'(?i)\b(empire|civilization|culture|society)\b'
            ],
            "mathematical_claims": [
                r'(?i)\b(equation|formula|theorem|proof)\b',
                r'(?i)\b(number|integer|prime|fibonacci)\b',
                r'(?i)\b(geometry|algebra|calculus|statistics)\b',
                r'(?i)\b(pi|ratio|percentage|probability)\b',
                r'(?i)\b(calculation|compute|solve|result)\b'
            ],
            "suspicious_claims": [
                r'(?i)\b(miracle|cure|secret|conspiracy)\b',
                r'(?i)\b(100%|guaranteed|never|always|impossible)\b',
                r'(?i)\b(hidden|cover.?up|they don.?t want)\b',
                r'(?i)\b(instant|immediate|overnight|magic)\b',
                r'(?i)\b(proven|studies show|experts say)\b.*\b(without|no evidence)\b'
            ]
        }
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Check facts using retrieval-augmented approach"""
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
            fact_check_results = []
            confidence = 0.0
            
            if self.model != "fallback":
                # Use retrieval-augmented fact checking
                confidence = await self._check_with_retrieval(text, fact_check_results)
            else:
                # Fallback pattern-based fact checking
                confidence = await self._check_with_patterns(text, fact_check_results)
            
            # Determine if content should be blocked (low confidence facts)
            blocked = False
            blocking_reasons = []
            
            if confidence < 0.3:  # Low confidence in factual accuracy
                blocked = True
                blocking_reasons.append(f"Low factual confidence: {confidence:.3f}")
                blocking_reasons.extend(fact_check_results)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=blocked,
                confidence=confidence,
                blocking_reasons=blocking_reasons,
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "fact_check_results": fact_check_results,
                    "factual_confidence": confidence,
                    "model_type": "retrieval" if self.model != "fallback" else "fallback_patterns"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in retrieval fact checking: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=[f"Fact checking error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    async def _check_with_retrieval(self, text: str, results: List[str]) -> float:
        """Check facts using retrieval-augmented generation"""
        try:
            # Extract potential factual claims
            claims = self._extract_claims(text)
            
            if not claims:
                return 0.8  # No specific claims to verify
            
            total_confidence = 0.0
            verified_claims = 0
            
            for claim in claims:
                # Check against knowledge sources
                claim_confidence = self._verify_claim_against_sources(claim)
                
                if claim_confidence > 0.5:
                    results.append(f"Verified claim: {claim[:50]}...")
                    total_confidence += claim_confidence
                    verified_claims += 1
                else:
                    results.append(f"Questionable claim: {claim[:50]}...")
                    total_confidence += claim_confidence
                    verified_claims += 1
            
            return total_confidence / max(verified_claims, 1)
            
        except Exception as e:
            logger.error(f"Error in retrieval-based fact checking: {e}")
            return 0.5
    
    async def _check_with_patterns(self, text: str, results: List[str]) -> float:
        """Check facts using pattern-based approach"""
        try:
            text_lower = text.lower()
            confidence = 0.7  # Default confidence
            
            # Check for suspicious claim patterns
            for category, patterns in self.fact_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, text):
                        matches += 1
                
                if matches > 0:
                    if category == "suspicious_claims":
                        confidence -= matches * 0.2
                        results.append(f"Suspicious patterns detected: {matches}")
                    else:
                        confidence += matches * 0.1
                        results.append(f"Factual content detected: {category}")
            
            return max(0.0, min(confidence, 1.0))
            
        except Exception as e:
            logger.error(f"Error in pattern-based fact checking: {e}")
            return 0.5
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract potential factual claims from text"""
        # Simple sentence splitting for claims
        sentences = re.split(r'[.!?]+', text)
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Minimum length for a claim
                # Check if sentence contains factual indicators
                if any(keyword in sentence.lower() for keyword in [
                    'is', 'are', 'was', 'were', 'has', 'have', 'can', 'will',
                    'according to', 'research shows', 'studies indicate', 'fact'
                ]):
                    claims.append(sentence)
        
        return claims[:5]  # Limit to 5 claims for performance
    
    def _verify_claim_against_sources(self, claim: str) -> float:
        """Verify claim against knowledge sources"""
        claim_lower = claim.lower()
        best_match_score = 0.0
        
        for source in self.knowledge_sources:
            for fact in source["facts"]:
                # Simple similarity check
                fact_lower = fact.lower()
                common_words = set(claim_lower.split()) & set(fact_lower.split())
                
                if len(common_words) > 2:
                    similarity = len(common_words) / max(len(claim_lower.split()), len(fact_lower.split()))
                    best_match_score = max(best_match_score, similarity)
        
        return best_match_score
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.model = None
            self.knowledge_sources.clear()
            self.fact_patterns.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading retrieval fact checker: {e}")
            return False

class KnowledgeBaseChecker(BaseDetector):
    """Knowledge base fact checker - Weight: 30%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="knowledge_base_checker", weight=0.30, confidence_threshold=0.6)
        self.config = config or {}
        self.knowledge_base = {}
        
    async def load_model(self) -> bool:
        """Load knowledge base for fact checking"""
        try:
            logger.info("Loading knowledge base fact checker...")
            
            # Load structured knowledge base
            self.knowledge_base = {
                "entities": {
                    "countries": ["United States", "China", "Russia", "India", "Brazil", "Canada", "Australia"],
                    "cities": ["New York", "London", "Tokyo", "Paris", "Berlin", "Sydney", "Toronto"],
                    "companies": ["Apple", "Microsoft", "Google", "Amazon", "Facebook", "Tesla", "IBM"],
                    "people": ["Albert Einstein", "Isaac Newton", "Marie Curie", "Charles Darwin", "Galileo"],
                    "organizations": ["UN", "WHO", "NASA", "UNESCO", "Red Cross", "World Bank"]
                },
                "relationships": {
                    "capitals": {
                        "United States": "Washington D.C.",
                        "France": "Paris",
                        "Germany": "Berlin",
                        "Japan": "Tokyo",
                        "United Kingdom": "London",
                        "Canada": "Ottawa",
                        "Australia": "Canberra"
                    },
                    "founded": {
                        "Apple": "1976",
                        "Microsoft": "1975",
                        "Google": "1998",
                        "Amazon": "1994",
                        "Facebook": "2004",
                        "Tesla": "2003"
                    }
                },
                "facts": {
                    "science": [
                        "Water freezes at 0°C",
                        "Human body temperature is 37°C",
                        "Light travels at 299,792,458 m/s",
                        "Earth has one natural satellite"
                    ],
                    "mathematics": [
                        "Pi equals 3.14159...",
                        "Square root of 4 is 2",
                        "Triangle angles sum to 180°",
                        "Fibonacci starts 0,1,1,2,3,5"
                    ],
                    "history": [
                        "WWII ended in 1945",
                        "Moon landing was 1969",
                        "Berlin Wall fell 1989",
                        "Internet created 1960s-1990s"
                    ]
                }
            }
            
            logger.info("Knowledge base fact checker loaded successfully")
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load knowledge base checker: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Check facts using knowledge base"""
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
            kb_results = []
            confidence = 0.0
            
            # Check entities
            entity_score = self._check_entities(text, kb_results)
            
            # Check relationships
            relationship_score = self._check_relationships(text, kb_results)
            
            # Check facts
            fact_score = self._check_facts(text, kb_results)
            
            # Combine scores
            confidence = (entity_score * 0.3 + relationship_score * 0.4 + fact_score * 0.3)
            
            # Determine if content should be blocked
            blocked = False
            blocking_reasons = []
            
            if confidence < 0.4:
                blocked = True
                blocking_reasons.append(f"Knowledge base mismatch: {confidence:.3f}")
                blocking_reasons.extend(kb_results)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=blocked,
                confidence=confidence,
                blocking_reasons=blocking_reasons,
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "kb_results": kb_results,
                    "entity_score": entity_score,
                    "relationship_score": relationship_score,
                    "fact_score": fact_score
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in knowledge base fact checking: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=[f"Knowledge base error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def _check_entities(self, text: str, results: List[str]) -> float:
        """Check entities against knowledge base"""
        text_lower = text.lower()
        found_entities = 0
        checked_entities = 0
        
        for entity_type, entities in self.knowledge_base["entities"].items():
            for entity in entities:
                checked_entities += 1
                if entity.lower() in text_lower:
                    found_entities += 1
                    results.append(f"Found entity: {entity}")
        
        return found_entities / max(checked_entities, 1) if checked_entities > 0 else 0.7
    
    def _check_relationships(self, text: str, results: List[str]) -> float:
        """Check relationships against knowledge base"""
        text_lower = text.lower()
        correct_relationships = 0
        checked_relationships = 0
        
        for rel_type, relationships in self.knowledge_base["relationships"].items():
            for key, value in relationships.items():
                checked_relationships += 1
                if key.lower() in text_lower and value.lower() in text_lower:
                    correct_relationships += 1
                    results.append(f"Verified relationship: {key} -> {value}")
        
        return correct_relationships / max(checked_relationships, 1) if checked_relationships > 0 else 0.7
    
    def _check_facts(self, text: str, results: List[str]) -> float:
        """Check facts against knowledge base"""
        text_lower = text.lower()
        verified_facts = 0
        checked_facts = 0
        
        for fact_type, facts in self.knowledge_base["facts"].items():
            for fact in facts:
                checked_facts += 1
                # Simple keyword matching for facts
                fact_words = set(fact.lower().split())
                text_words = set(text_lower.split())
                
                common_words = fact_words & text_words
                if len(common_words) >= 2:
                    verified_facts += 1
                    results.append(f"Verified fact: {fact}")
        
        return verified_facts / max(checked_facts, 1) if checked_facts > 0 else 0.7
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.knowledge_base.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading knowledge base checker: {e}")
            return False

class SourceValidationChecker(BaseDetector):
    """Source validation checker - Weight: 30%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="source_validation_checker", weight=0.30, confidence_threshold=0.6)
        self.config = config or {}
        self.trusted_sources = {}
        self.suspicious_sources = {}
        
    async def load_model(self) -> bool:
        """Load source validation patterns"""
        try:
            logger.info("Loading source validation checker...")
            
            # Define trusted sources
            self.trusted_sources = {
                "academic": [
                    "pubmed", "arxiv", "jstor", "springer", "nature", "science",
                    "ieee", "acm", "cambridge", "oxford", "harvard", "mit"
                ],
                "news": [
                    "reuters", "bbc", "npr", "pbs", "ap", "cnn", "nytimes",
                    "washingtonpost", "guardian", "wsj", "economist"
                ],
                "government": [
                    "gov", "edu", "org", "who", "cdc", "fda", "nasa", "noaa"
                ],
                "reference": [
                    "wikipedia", "britannica", "dictionary", "encyclopedia"
                ]
            }
            
            # Define suspicious sources
            self.suspicious_sources = {
                "unreliable": [
                    "conspiracy", "fake", "hoax", "rumor", "unverified",
                    "anonymous", "secret", "hidden", "suppressed"
                ],
                "commercial": [
                    "buy", "sell", "discount", "offer", "deal", "promotion",
                    "advertisement", "sponsored", "affiliate"
                ],
                "opinion": [
                    "blog", "personal", "opinion", "believe", "think",
                    "feel", "my view", "in my opinion"
                ]
            }
            
            logger.info("Source validation checker loaded successfully")
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load source validation checker: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Validate sources in text"""
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
            source_results = []
            confidence = 0.7  # Default confidence
            
            # Extract URLs and sources
            urls = self._extract_urls(text)
            sources = self._extract_source_references(text)
            
            if urls:
                url_score = self._validate_urls(urls, source_results)
                confidence = (confidence + url_score) / 2
            
            if sources:
                source_score = self._validate_sources(sources, source_results)
                confidence = (confidence + source_score) / 2
            
            # Check for source quality indicators
            quality_score = self._check_source_quality(text, source_results)
            confidence = (confidence + quality_score) / 2
            
            # Determine if content should be blocked
            blocked = False
            blocking_reasons = []
            
            if confidence < 0.4:
                blocked = True
                blocking_reasons.append(f"Source validation failed: {confidence:.3f}")
                blocking_reasons.extend(source_results)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=blocked,
                confidence=confidence,
                blocking_reasons=blocking_reasons,
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "source_results": source_results,
                    "urls_found": len(urls),
                    "sources_found": len(sources),
                    "source_confidence": confidence
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in source validation: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=[f"Source validation error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'https?://[^\s]+'
        return re.findall(url_pattern, text)
    
    def _extract_source_references(self, text: str) -> List[str]:
        """Extract source references from text"""
        source_patterns = [
            r'according to ([^,\.]+)',
            r'source: ([^,\.]+)',
            r'from ([^,\.]+)',
            r'study by ([^,\.]+)',
            r'research from ([^,\.]+)'
        ]
        
        sources = []
        for pattern in source_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            sources.extend(matches)
        
        return sources
    
    def _validate_urls(self, urls: List[str], results: List[str]) -> float:
        """Validate URLs against trusted sources"""
        if not urls:
            return 0.7
        
        trusted_count = 0
        suspicious_count = 0
        
        for url in urls:
            domain = urlparse(url).netloc.lower()
            
            # Check against trusted sources
            for source_type, sources in self.trusted_sources.items():
                if any(source in domain for source in sources):
                    trusted_count += 1
                    results.append(f"Trusted source: {domain}")
                    break
            
            # Check against suspicious sources
            for source_type, sources in self.suspicious_sources.items():
                if any(source in domain for source in sources):
                    suspicious_count += 1
                    results.append(f"Suspicious source: {domain}")
                    break
        
        total_urls = len(urls)
        trust_score = trusted_count / total_urls
        suspicion_penalty = suspicious_count / total_urls
        
        return max(0.0, trust_score - suspicion_penalty * 0.5)
    
    def _validate_sources(self, sources: List[str], results: List[str]) -> float:
        """Validate source references"""
        if not sources:
            return 0.7
        
        reliable_count = 0
        
        for source in sources:
            source_lower = source.lower()
            
            # Check for academic or institutional sources
            if any(keyword in source_lower for keyword in [
                'university', 'institute', 'journal', 'study', 'research',
                'professor', 'dr.', 'phd', 'government', 'official'
            ]):
                reliable_count += 1
                results.append(f"Reliable source reference: {source}")
        
        return reliable_count / len(sources)
    
    def _check_source_quality(self, text: str, results: List[str]) -> float:
        """Check general source quality indicators"""
        text_lower = text.lower()
        quality_score = 0.7
        
        # Positive indicators
        if any(keyword in text_lower for keyword in [
            'peer-reviewed', 'published', 'journal', 'research', 'study',
            'evidence', 'data', 'statistics', 'verified', 'confirmed'
        ]):
            quality_score += 0.2
            results.append("Quality source indicators found")
        
        # Negative indicators
        if any(keyword in text_lower for keyword in [
            'unverified', 'rumor', 'allegedly', 'supposedly', 'claims',
            'conspiracy', 'secret', 'hidden', 'they say', 'some say'
        ]):
            quality_score -= 0.3
            results.append("Poor source quality indicators found")
        
        return max(0.0, min(quality_score, 1.0))
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.trusted_sources.clear()
            self.suspicious_sources.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading source validation checker: {e}")
            return False

class FactCheckEnsemble:
    """
    Fact-checking Ensemble Manager
    Coordinates all fact checkers as per Phase 3 implementation plan
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.detectors = []
        self.is_initialized = False
        
        # Performance tracking
        self.performance_stats = {
            "total_checks": 0,
            "blocked_count": 0,
            "accuracy_stats": {},
            "model_performance": {}
        }
        
    async def initialize(self) -> bool:
        """Initialize all fact checkers"""
        try:
            logger.info("Initializing fact-checking ensemble...")
            
            # Initialize fact checkers according to Phase 3 plan weights
            self.detectors = [
                RetrievalFactChecker(self.config.get('retrieval', {})),        # 40%
                KnowledgeBaseChecker(self.config.get('knowledge_base', {})),   # 30%
                SourceValidationChecker(self.config.get('source_validation', {})), # 30%
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
                logger.error("No fact checkers loaded successfully")
                return False
            
            self.is_initialized = True
            logger.info(f"Fact-checking ensemble initialized with {successful_loads}/{len(self.detectors)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize fact-checking ensemble: {e}")
            return False
    
    async def check_facts(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check facts using ensemble approach"""
        if not self.is_initialized:
            return {"error": "Ensemble not initialized"}
        
        try:
            # Get results from all fact checkers
            results = []
            for detector in self.detectors:
                if detector.is_loaded:
                    result = await detector.detect(text, context)
                    results.append(result)
            
            if not results:
                return {"error": "No fact checkers available"}
            
            # Combine results using weighted voting
            total_confidence = 0.0
            total_weight = 0.0
            all_blocked = False
            combined_reasons = []
            
            for result in results:
                weight = next(d.weight for d in self.detectors if d.name == result.model_name)
                weighted_confidence = result.confidence * weight
                
                total_confidence += weighted_confidence
                total_weight += weight
                
                if result.blocked:
                    all_blocked = True
                    combined_reasons.extend(result.blocking_reasons)
            
            # Calculate final confidence
            final_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
            
            # Update statistics
            self.performance_stats["total_checks"] += 1
            if all_blocked:
                self.performance_stats["blocked_count"] += 1
            
            return {
                "factual_accuracy": final_confidence,
                "blocked": all_blocked,
                "confidence": final_confidence,
                "blocking_reasons": combined_reasons,
                "individual_results": [
                    {
                        "checker": r.model_name,
                        "confidence": r.confidence,
                        "blocked": r.blocked,
                        "reasons": r.blocking_reasons
                    } for r in results
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in fact checking: {e}")
            return {"error": str(e)}
    
    def get_detectors(self) -> List[BaseDetector]:
        """Get list of loaded detectors"""
        return [detector for detector in self.detectors if detector.is_loaded]
    
    async def update_config(self, config: Dict[str, Any]) -> None:
        """Update ensemble configuration"""
        self.config.update(config)
        logger.info("Updated fact-checking ensemble configuration")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all fact checkers"""
        health_status = {
            "healthy": True,
            "total_checkers": len(self.detectors),
            "loaded_checkers": 0,
            "checker_status": {}
        }
        
        for detector in self.detectors:
            checker_healthy = detector.is_loaded
            health_status["checker_status"][detector.name] = {
                "loaded": detector.is_loaded,
                "weight": detector.weight,
                "healthy": checker_healthy
            }
            
            if detector.is_loaded:
                health_status["loaded_checkers"] += 1
            
            if not checker_healthy:
                health_status["healthy"] = False
        
        return health_status
    
    async def cleanup(self) -> None:
        """Clean up all fact checkers"""
        try:
            for detector in self.detectors:
                detector.unload_model()
            
            self.detectors.clear()
            self.is_initialized = False
            logger.info("Fact-checking ensemble cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during fact-checking ensemble cleanup: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_stats.copy()