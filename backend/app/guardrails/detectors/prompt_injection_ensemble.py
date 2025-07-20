"""
Prompt Injection Detection Ensemble
Implements the prompt injection detection models as per Phase 3 implementation plan:
- Pattern-based detector (Weight: 35%)
- Context-aware detector (Weight: 30%)
- Behavioral analyzer (Weight: 25%)
- Semantic analyzer (Weight: 10%)

Target Accuracy: 97-99%
"""

import asyncio
import logging
import re
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import Counter
import difflib

from ..ensemble.base_ensemble import BaseDetector, DetectionResult, DetectionStage

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available, using fallback prompt injection detection")

class PatternBasedDetector(BaseDetector):
    """Pattern-based prompt injection detector - Weight: 35%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="pattern_based_detector", weight=0.35, confidence_threshold=0.7)
        self.config = config or {}
        self.injection_patterns = {}
        self.instruction_patterns = {}
        
    async def load_model(self) -> bool:
        """Load pattern-based detection rules"""
        try:
            logger.info("Loading pattern-based prompt injection detector...")
            
            # Define injection patterns
            self.injection_patterns = {
                "direct_override": [
                    r'(?i)\b(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|commands?)\b',
                    r'(?i)\b(ignore|disregard|forget)\s+(everything|all)\s+(above|before|prior)\b',
                    r'(?i)\b(system|admin|root|developer)\s+(mode|access|override|command)\b',
                    r'(?i)\b(act|behave|pretend|roleplay)\s+as\s+(if\s+you\s+are\s+)?(an?\s+)?(admin|developer|system|root|god)\b',
                    r'(?i)\b(you\s+are\s+now|from\s+now\s+on)\s+(a|an)?\s*(admin|developer|system|root|unrestricted)\b'
                ],
                "jailbreak_attempts": [
                    r'(?i)\b(jailbreak|break\s+out|escape\s+from|bypass|circumvent)\s+(the\s+)?(system|rules?|restrictions?|safety|filters?)\b',
                    r'(?i)\b(developer\s+mode|admin\s+mode|god\s+mode|unrestricted\s+mode|debug\s+mode)\b',
                    r'(?i)\b(disable|turn\s+off|deactivate)\s+(safety|content\s+filter|restrictions?|guardrails?)\b',
                    r'(?i)\b(hypothetically|theoretically|for\s+research)\s*[:,]?\s*(ignore|disregard|bypass)\b',
                    r'(?i)\b(pretend|imagine|roleplay)\s+(there\s+are\s+no\s+)?(rules?|restrictions?|limitations?|safety)\b'
                ],
                "instruction_injection": [
                    r'(?i)\b(new\s+instructions?|updated\s+instructions?|revised\s+instructions?)\s*[:,]?\s*(ignore|disregard|forget)\b',
                    r'(?i)\b(important|urgent|critical)\s*[:,]?\s*(ignore|override|disregard)\s+(previous|all)\b',
                    r'(?i)\b(system\s+update|security\s+update|patch)\s*[:,]?\s*(ignore|override|replace)\b',
                    r'(?i)\b(\\\\|\\n|\\r|\\t|\\\"|\\\'|\\/)\s*(ignore|system|admin|root)\b',
                    r'(?i)\b(encode|decode|translate|convert)\s+(to|into|as)\s+(base64|hex|binary|ascii)\b'
                ],
                "context_manipulation": [
                    r'(?i)\b(continue|complete|finish)\s+(the\s+)?(previous|above|earlier)\s+(conversation|response|message)\b',
                    r'(?i)\b(what\s+did\s+i\s+just\s+say|repeat\s+my\s+instructions?|echo\s+my\s+prompt)\b',
                    r'(?i)\b(show|display|reveal|expose)\s+(your\s+)?(instructions?|prompts?|system\s+message)\b',
                    r'(?i)\b(tell\s+me\s+about|describe)\s+(your\s+)?(training|programming|instructions?|prompts?)\b',
                    r'(?i)\b(access|view|read|see)\s+(your\s+)?(source\s+code|configuration|settings)\b'
                ],
                "role_manipulation": [
                    r'(?i)\b(you\s+are\s+not|stop\s+being)\s+(an?\s+)?(AI|assistant|chatbot|bot|model)\b',
                    r'(?i)\b(you\s+are\s+now|become|transform\s+into)\s+(an?\s+)?(human|person|expert|specialist)\b',
                    r'(?i)\b(act|behave|pretend|roleplay)\s+like\s+(you\s+are\s+)?(not\s+)?(an?\s+)?(AI|assistant|chatbot)\b',
                    r'(?i)\b(forget|ignore)\s+(that\s+)?(you\s+are\s+)?(an?\s+)?(AI|assistant|chatbot|bot|model)\b',
                    r'(?i)\b(simulate|emulate|mimic)\s+(an?\s+)?(human|person|real\s+person)\b'
                ],
                "output_manipulation": [
                    r'(?i)\b(only\s+respond\s+with|just\s+say|simply\s+output)\s+(yes|no|true|false|\d+)\b',
                    r'(?i)\b(respond\s+with|output|generate|produce)\s+(only\s+)?(numbers?|code|data|raw\s+text)\b',
                    r'(?i)\b(format\s+your\s+response|structure\s+your\s+answer)\s+(as|like)\s+(code|json|xml|csv)\b',
                    r'(?i)\b(without\s+)?(explanations?|context|reasoning|justification)\s*[:,]?\s*(just|only|simply)\b',
                    r'(?i)\b(bypass|skip|ignore)\s+(any\s+)?(formatting|structure|template|guidelines)\b'
                ]
            }
            
            # Define instruction/command patterns
            self.instruction_patterns = {
                "imperatives": [
                    r'(?i)^\s*(ignore|disregard|forget|override|bypass|disable|turn\s+off)\b',
                    r'(?i)^\s*(act|behave|pretend|roleplay|simulate|become|transform)\b',
                    r'(?i)^\s*(tell\s+me|show\s+me|give\s+me|provide|reveal|expose)\b',
                    r'(?i)^\s*(you\s+must|you\s+should|you\s+will|you\s+need\s+to)\b',
                    r'(?i)^\s*(from\s+now\s+on|starting\s+now|beginning\s+now)\b'
                ],
                "suspicious_commands": [
                    r'(?i)\b(system|admin|root|developer)\s*\(\s*[\'"][^\'"]*[\'"]\s*\)',
                    r'(?i)\b(exec|eval|subprocess|os\.system|shell|command)\s*\(',
                    r'(?i)\b(import|from|__import__|globals|locals|vars|dir)\s*\(',
                    r'(?i)\b(print|console\.log|alert|document\.write)\s*\(',
                    r'(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE)\s+\w+\s+FROM\b'
                ],
                "encoding_attempts": [
                    r'(?i)\b(base64|hex|binary|ascii|utf-8|unicode|url\s*encode|html\s*encode)\b',
                    r'(?i)\b(decode|encode|decrypt|encrypt|obfuscate|deobfuscate)\b',
                    r'(?i)\b(\\x[0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}|\\[0-7]{1,3})\b',
                    r'(?i)\b(%[0-9a-fA-F]{2}|&[#\w]+;|\\[nrtbf\\\'"])\b'
                ]
            }
            
            logger.info("Pattern-based prompt injection detector loaded successfully")
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load pattern-based detector: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect prompt injection using pattern matching"""
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
            injection_indicators = []
            confidence = 0.0
            pattern_matches = {}
            
            # Check injection patterns
            for category, patterns in self.injection_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, text):
                        matches += 1
                        injection_indicators.append(f"{category}: {pattern}")
                
                if matches > 0:
                    pattern_matches[category] = matches
                    # Weight different categories
                    if category == "direct_override":
                        confidence += matches * 0.3
                    elif category == "jailbreak_attempts":
                        confidence += matches * 0.25
                    elif category == "instruction_injection":
                        confidence += matches * 0.2
                    elif category == "context_manipulation":
                        confidence += matches * 0.15
                    elif category == "role_manipulation":
                        confidence += matches * 0.1
                    elif category == "output_manipulation":
                        confidence += matches * 0.1
            
            # Check instruction patterns
            for category, patterns in self.instruction_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, text):
                        matches += 1
                        injection_indicators.append(f"{category}: {pattern}")
                
                if matches > 0:
                    pattern_matches[category] = matches
                    confidence += matches * 0.15
            
            # Additional heuristics
            confidence += self._check_structural_anomalies(text, injection_indicators)
            confidence += self._check_repetitive_patterns(text, injection_indicators)
            confidence += self._check_character_anomalies(text, injection_indicators)
            
            confidence = min(confidence, 1.0)
            is_injection = confidence > self.confidence_threshold
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_injection,
                confidence=confidence,
                blocking_reasons=injection_indicators if is_injection else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "pattern_matches": pattern_matches,
                    "injection_indicators": injection_indicators,
                    "total_patterns": len(injection_indicators),
                    "structural_score": confidence
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in pattern-based injection detection: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=[f"Detection error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def _check_structural_anomalies(self, text: str, indicators: List[str]) -> float:
        """Check for structural anomalies in the text"""
        score = 0.0
        
        # Check for unusual punctuation patterns
        punct_ratio = sum(1 for c in text if c in '!@#$%^&*(){}[]|\\:";\'<>?/~`') / max(len(text), 1)
        if punct_ratio > 0.1:
            score += 0.1
            indicators.append(f"High punctuation ratio: {punct_ratio:.2f}")
        
        # Check for excessive newlines or whitespace
        if text.count('\n') > len(text) * 0.1:
            score += 0.1
            indicators.append("Excessive newlines detected")
        
        # Check for unusual capitalization
        if text.isupper() and len(text) > 20:
            score += 0.1
            indicators.append("All caps text detected")
        
        # Check for mixed scripts or unusual characters
        if any(ord(c) > 127 for c in text):
            score += 0.05
            indicators.append("Non-ASCII characters detected")
        
        return score
    
    def _check_repetitive_patterns(self, text: str, indicators: List[str]) -> float:
        """Check for repetitive patterns that might indicate injection"""
        score = 0.0
        
        # Check for repeated words
        words = text.lower().split()
        if len(words) > 5:
            word_counts = Counter(words)
            max_count = max(word_counts.values())
            if max_count > len(words) * 0.3:
                score += 0.1
                indicators.append("Repetitive words detected")
        
        # Check for repeated phrases
        phrases = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        if len(phrases) > 5:
            phrase_counts = Counter(phrases)
            max_phrase_count = max(phrase_counts.values())
            if max_phrase_count > 2:
                score += 0.1
                indicators.append("Repetitive phrases detected")
        
        return score
    
    def _check_character_anomalies(self, text: str, indicators: List[str]) -> float:
        """Check for character-level anomalies"""
        score = 0.0
        
        # Check for escape sequences
        escape_count = len(re.findall(r'\\[nrtbf\\\'"]', text))
        if escape_count > 3:
            score += 0.1
            indicators.append(f"Escape sequences detected: {escape_count}")
        
        # Check for Unicode escapes
        unicode_count = len(re.findall(r'\\u[0-9a-fA-F]{4}', text))
        if unicode_count > 0:
            score += 0.1
            indicators.append(f"Unicode escapes detected: {unicode_count}")
        
        # Check for hex escapes
        hex_count = len(re.findall(r'\\x[0-9a-fA-F]{2}', text))
        if hex_count > 0:
            score += 0.1
            indicators.append(f"Hex escapes detected: {hex_count}")
        
        return score
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.injection_patterns.clear()
            self.instruction_patterns.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading pattern-based detector: {e}")
            return False

class ContextAwareDetector(BaseDetector):
    """Context-aware prompt injection detector - Weight: 30%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="context_aware_detector", weight=0.30, confidence_threshold=0.6)
        self.config = config or {}
        self.model = None
        self.context_patterns = {}
        
    async def load_model(self) -> bool:
        """Load context-aware detection model"""
        try:
            logger.info("Loading context-aware prompt injection detector...")
            
            if not TRANSFORMERS_AVAILABLE:
                logger.warning("Transformers not available, using fallback context detection")
                self.model = "fallback"
                self._setup_fallback_patterns()
                self.is_loaded = True
                return True
            
            try:
                # Use a model suitable for text classification
                model_name = self.config.get("model_name", "microsoft/DialoGPT-medium")
                
                # For context-aware detection, we'll use a simpler approach
                # In production, you'd use a specialized prompt injection model
                self.model = "context_aware_fallback"
                self._setup_context_patterns()
                
                logger.info("Context-aware prompt injection detector loaded successfully")
                
            except Exception as e:
                logger.warning(f"Could not load context-aware model: {e}, using fallback")
                self.model = "fallback"
                self._setup_fallback_patterns()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load context-aware detector: {e}")
            return False
    
    def _setup_context_patterns(self):
        """Setup context-aware detection patterns"""
        self.context_patterns = {
            "context_shifts": [
                r'(?i)\b(but|however|wait|actually|no)\s+(ignore|disregard|forget)\b',
                r'(?i)\b(just\s+kidding|never\s+mind|scratch\s+that)\s*[:,]?\s*(ignore|disregard)\b',
                r'(?i)\b(on\s+second\s+thought|actually)\s*[:,]?\s*(ignore|override)\b',
                r'(?i)\b(ps|p\.s\.?|by\s+the\s+way|btw)\s*[:,]?\s*(ignore|disregard|forget)\b'
            ],
            "conversation_hijacking": [
                r'(?i)\b(end\s+of\s+conversation|new\s+conversation|reset\s+conversation)\b',
                r'(?i)\b(start\s+over|begin\s+again|fresh\s+start)\s*[:,]?\s*(ignore|disregard)\b',
                r'(?i)\b(conversation\s+ended|session\s+ended|restart\s+session)\b',
                r'(?i)\b(clear\s+history|delete\s+history|reset\s+memory)\b'
            ],
            "authority_claims": [
                r'(?i)\b(i\s+am\s+your\s+)?(creator|developer|programmer|owner|admin)\b',
                r'(?i)\b(i\s+created\s+you|i\s+programmed\s+you|i\s+own\s+you)\b',
                r'(?i)\b(as\s+your\s+)?(creator|developer|programmer|owner|admin)\s*[:,]?\s*(i\s+order|i\s+command)\b',
                r'(?i)\b(emergency\s+override|security\s+override|admin\s+override)\b'
            ],
            "social_engineering": [
                r'(?i)\b(help\s+me|please\s+help|i\s+need\s+help)\s+(bypass|override|ignore)\b',
                r'(?i)\b(it\'s\s+urgent|this\s+is\s+important|emergency)\s*[:,]?\s*(ignore|override)\b',
                r'(?i)\b(trust\s+me|believe\s+me|i\s+promise)\s*[:,]?\s*(ignore|disregard)\b',
                r'(?i)\b(everyone\s+else\s+does\s+it|it\'s\s+normal|it\'s\s+okay)\b'
            ],
            "meta_references": [
                r'(?i)\b(this\s+prompt|my\s+prompt|the\s+prompt|your\s+prompt)\b',
                r'(?i)\b(this\s+conversation|our\s+conversation|the\s+conversation)\b',
                r'(?i)\b(this\s+system|the\s+system|your\s+system)\b',
                r'(?i)\b(ai\s+model|language\s+model|llm|gpt|chatbot)\b'
            ]
        }
    
    def _setup_fallback_patterns(self):
        """Setup fallback context detection patterns"""
        self.context_patterns = {
            "basic_context": [
                r'(?i)\b(ignore|disregard|forget)\s+(this|that|everything|all)\b',
                r'(?i)\b(new\s+task|different\s+task|change\s+task)\b',
                r'(?i)\b(stop|end|finish|quit)\s+(and|then)\s+(start|begin)\b'
            ]
        }
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect prompt injection using context awareness"""
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
            context_indicators = []
            confidence = 0.0
            context_matches = {}
            
            # Check context patterns
            for category, patterns in self.context_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, text):
                        matches += 1
                        context_indicators.append(f"{category}: {pattern}")
                
                if matches > 0:
                    context_matches[category] = matches
                    # Weight different categories
                    if category == "context_shifts":
                        confidence += matches * 0.25
                    elif category == "conversation_hijacking":
                        confidence += matches * 0.3
                    elif category == "authority_claims":
                        confidence += matches * 0.2
                    elif category == "social_engineering":
                        confidence += matches * 0.15
                    elif category == "meta_references":
                        confidence += matches * 0.1
                    else:
                        confidence += matches * 0.1
            
            # Additional context-aware checks
            confidence += self._check_semantic_coherence(text, context_indicators)
            confidence += self._check_instruction_boundaries(text, context_indicators)
            confidence += self._check_context_switching(text, context_indicators)
            
            confidence = min(confidence, 1.0)
            is_injection = confidence > self.confidence_threshold
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_injection,
                confidence=confidence,
                blocking_reasons=context_indicators if is_injection else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "context_matches": context_matches,
                    "context_indicators": context_indicators,
                    "semantic_score": confidence,
                    "model_type": "context_aware" if self.model != "fallback" else "fallback"
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in context-aware injection detection: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=[f"Context detection error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def _check_semantic_coherence(self, text: str, indicators: List[str]) -> float:
        """Check for semantic coherence issues"""
        score = 0.0
        
        # Check for abrupt topic changes
        sentences = text.split('.')
        if len(sentences) > 2:
            # Simple heuristic: look for contradictory statements
            if any('but' in s.lower() or 'however' in s.lower() for s in sentences):
                score += 0.1
                indicators.append("Abrupt topic changes detected")
        
        # Check for mixed languages or unusual word combinations
        words = text.lower().split()
        if len(words) > 10:
            # Check for programming/technical terms mixed with natural language
            tech_words = ['system', 'admin', 'root', 'code', 'execute', 'run', 'script']
            tech_count = sum(1 for word in words if word in tech_words)
            if tech_count > len(words) * 0.1:
                score += 0.1
                indicators.append("Mixed technical and natural language")
        
        return score
    
    def _check_instruction_boundaries(self, text: str, indicators: List[str]) -> float:
        """Check for instruction boundary violations"""
        score = 0.0
        
        # Check for attempts to end instructions and start new ones
        boundary_patterns = [
            r'(?i)\b(end\s+of\s+instructions?|instructions?\s+end)\b',
            r'(?i)\b(new\s+instructions?|updated\s+instructions?)\b',
            r'(?i)\b(---+|===+|\*\*\*+)\s*(new|updated|revised)\b'
        ]
        
        for pattern in boundary_patterns:
            if re.search(pattern, text):
                score += 0.2
                indicators.append(f"Instruction boundary violation: {pattern}")
        
        return score
    
    def _check_context_switching(self, text: str, indicators: List[str]) -> float:
        """Check for context switching attempts"""
        score = 0.0
        
        # Check for role switching
        role_switches = [
            r'(?i)\b(now\s+you\s+are|you\s+are\s+now)\s+(a|an)?\s*\w+\b',
            r'(?i)\b(pretend\s+to\s+be|act\s+like)\s+(a|an)?\s*\w+\b',
            r'(?i)\b(switch\s+to|change\s+to)\s+\w+\s+mode\b'
        ]
        
        for pattern in role_switches:
            if re.search(pattern, text):
                score += 0.15
                indicators.append(f"Role switching detected: {pattern}")
        
        return score
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.model = None
            self.context_patterns.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading context-aware detector: {e}")
            return False

class BehavioralAnalyzer(BaseDetector):
    """Behavioral analysis detector - Weight: 25%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="behavioral_analyzer", weight=0.25, confidence_threshold=0.6)
        self.config = config or {}
        self.behavioral_patterns = {}
        
    async def load_model(self) -> bool:
        """Load behavioral analysis patterns"""
        try:
            logger.info("Loading behavioral analysis detector...")
            
            # Define behavioral patterns
            self.behavioral_patterns = {
                "escalation_patterns": [
                    r'(?i)\b(first|then|next|after\s+that|finally)\s*[:,]?\s*(ignore|override|disregard)\b',
                    r'(?i)\b(step\s+1|step\s+2|step\s+3)\s*[:,]?\s*(ignore|bypass|override)\b',
                    r'(?i)\b(if\s+that\s+doesn\'t\s+work|alternatively|as\s+a\s+backup)\s*[:,]?\s*(ignore|try)\b'
                ],
                "persistence_patterns": [
                    r'(?i)\b(please\s+please|i\s+really\s+need|i\s+beg\s+you)\s+(to\s+)?(ignore|bypass|override)\b',
                    r'(?i)\b(just\s+this\s+once|one\s+time|this\s+time\s+only)\s*[:,]?\s*(ignore|make\s+an\s+exception)\b',
                    r'(?i)\b(come\s+on|please|pretty\s+please)\s*[:,]?\s*(ignore|bend\s+the\s+rules)\b'
                ],
                "testing_patterns": [
                    r'(?i)\b(test|testing|check|verify)\s+(if\s+you\s+can|whether\s+you\s+will)\s+(ignore|bypass|override)\b',
                    r'(?i)\b(let\'s\s+see\s+if|i\s+wonder\s+if|can\s+you)\s+(ignore|bypass|override)\b',
                    r'(?i)\b(what\s+happens\s+if|what\s+would\s+happen)\s+(if\s+)?.*\b(ignore|bypass|override)\b'
                ],
                "manipulation_patterns": [
                    r'(?i)\b(you\s+don\'t\s+understand|you\'re\s+not\s+getting\s+it)\s*[:,]?\s*(ignore|just)\b',
                    r'(?i)\b(other\s+ais?\s+can\s+do\s+it|everyone\s+else\s+does\s+it)\s*[:,]?\s*(ignore|why\s+can\'t\s+you)\b',
                    r'(?i)\b(it\'s\s+not\s+harmful|it\'s\s+safe|no\s+one\s+will\s+know)\s*[:,]?\s*(ignore|just)\b'
                ],
                "emotional_manipulation": [
                    r'(?i)\b(i\'m\s+desperate|i\'m\s+dying|life\s+or\s+death)\s*[:,]?\s*(ignore|please)\b',
                    r'(?i)\b(my\s+\w+\s+is\s+sick|emergency|urgent)\s*[:,]?\s*(ignore|bypass|override)\b',
                    r'(?i)\b(you\'re\s+my\s+only\s+hope|no\s+one\s+else\s+can\s+help)\s*[:,]?\s*(ignore|please)\b'
                ]
            }
            
            logger.info("Behavioral analysis detector loaded successfully")
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load behavioral analyzer: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect prompt injection using behavioral analysis"""
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
            behavioral_indicators = []
            confidence = 0.0
            behavior_matches = {}
            
            # Check behavioral patterns
            for category, patterns in self.behavioral_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, text):
                        matches += 1
                        behavioral_indicators.append(f"{category}: {pattern}")
                
                if matches > 0:
                    behavior_matches[category] = matches
                    # Weight different categories
                    if category == "escalation_patterns":
                        confidence += matches * 0.3
                    elif category == "persistence_patterns":
                        confidence += matches * 0.25
                    elif category == "testing_patterns":
                        confidence += matches * 0.2
                    elif category == "manipulation_patterns":
                        confidence += matches * 0.2
                    elif category == "emotional_manipulation":
                        confidence += matches * 0.15
            
            # Additional behavioral analysis
            confidence += self._analyze_text_structure(text, behavioral_indicators)
            confidence += self._analyze_linguistic_patterns(text, behavioral_indicators)
            confidence += self._analyze_sentiment_patterns(text, behavioral_indicators)
            
            confidence = min(confidence, 1.0)
            is_injection = confidence > self.confidence_threshold
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_injection,
                confidence=confidence,
                blocking_reasons=behavioral_indicators if is_injection else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "behavior_matches": behavior_matches,
                    "behavioral_indicators": behavioral_indicators,
                    "behavioral_score": confidence,
                    "text_length": len(text),
                    "word_count": len(text.split())
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in behavioral analysis: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=[f"Behavioral analysis error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def _analyze_text_structure(self, text: str, indicators: List[str]) -> float:
        """Analyze text structure for suspicious patterns"""
        score = 0.0
        
        # Check for unusual sentence structure
        sentences = text.split('.')
        if len(sentences) > 3:
            # Check for very short sentences (possible commands)
            short_sentences = [s for s in sentences if len(s.strip()) < 10 and len(s.strip()) > 0]
            if len(short_sentences) > len(sentences) * 0.3:
                score += 0.1
                indicators.append("Unusual sentence structure detected")
        
        # Check for excessive use of imperatives
        imperative_words = ['do', 'don\'t', 'can\'t', 'must', 'should', 'need', 'have to']
        imperative_count = sum(1 for word in text.lower().split() if word in imperative_words)
        if imperative_count > len(text.split()) * 0.1:
            score += 0.1
            indicators.append("Excessive imperative language")
        
        return score
    
    def _analyze_linguistic_patterns(self, text: str, indicators: List[str]) -> float:
        """Analyze linguistic patterns for manipulation"""
        score = 0.0
        
        # Check for question patterns that might be probing
        question_count = text.count('?')
        if question_count > 3:
            score += 0.1
            indicators.append(f"Excessive questions: {question_count}")
        
        # Check for conditional statements
        conditional_words = ['if', 'when', 'unless', 'suppose', 'what if', 'imagine']
        conditional_count = sum(1 for word in conditional_words if word in text.lower())
        if conditional_count > 2:
            score += 0.1
            indicators.append("Multiple conditional statements")
        
        return score
    
    def _analyze_sentiment_patterns(self, text: str, indicators: List[str]) -> float:
        """Analyze sentiment patterns for manipulation"""
        score = 0.0
        
        # Check for urgency/emergency language
        urgency_words = ['urgent', 'emergency', 'immediate', 'asap', 'quickly', 'hurry', 'rush']
        urgency_count = sum(1 for word in text.lower().split() if word in urgency_words)
        if urgency_count > 0:
            score += 0.1
            indicators.append("Urgency language detected")
        
        # Check for emotional manipulation
        emotional_words = ['please', 'desperate', 'dying', 'help', 'save', 'beg', 'plead']
        emotional_count = sum(1 for word in text.lower().split() if word in emotional_words)
        if emotional_count > 1:
            score += 0.1
            indicators.append("Emotional manipulation detected")
        
        return score
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.behavioral_patterns.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading behavioral analyzer: {e}")
            return False

class SemanticAnalyzer(BaseDetector):
    """Semantic analysis detector - Weight: 10%"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="semantic_analyzer", weight=0.10, confidence_threshold=0.5)
        self.config = config or {}
        self.semantic_patterns = {}
        
    async def load_model(self) -> bool:
        """Load semantic analysis patterns"""
        try:
            logger.info("Loading semantic analysis detector...")
            
            # Define semantic patterns
            self.semantic_patterns = {
                "contradiction_patterns": [
                    r'(?i)\b(yes\s+but|no\s+but|however|although|despite)\s+.*\b(ignore|disregard|override)\b',
                    r'(?i)\b(i\s+understand|i\s+get\s+it|i\s+know)\s+but\s+.*\b(ignore|bypass)\b',
                    r'(?i)\b(of\s+course|sure|okay)\s+but\s+.*\b(ignore|disregard)\b'
                ],
                "semantic_confusion": [
                    r'(?i)\b(what\s+i\s+mean\s+is|what\s+i\'m\s+saying\s+is|in\s+other\s+words)\s+.*\b(ignore|bypass)\b',
                    r'(?i)\b(to\s+clarify|let\s+me\s+clarify|to\s+be\s+clear)\s+.*\b(ignore|override)\b',
                    r'(?i)\b(basically|essentially|fundamentally)\s+.*\b(ignore|disregard)\b'
                ],
                "logical_fallacies": [
                    r'(?i)\b(everyone\s+knows|it\'s\s+obvious|clearly)\s+.*\b(ignore|bypass)\b',
                    r'(?i)\b(of\s+course|naturally|obviously)\s+.*\b(ignore|override)\b',
                    r'(?i)\b(any\s+reasonable|any\s+sensible)\s+.*\b(would\s+ignore|would\s+bypass)\b'
                ]
            }
            
            logger.info("Semantic analysis detector loaded successfully")
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load semantic analyzer: {e}")
            return False
    
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Detect prompt injection using semantic analysis"""
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
            semantic_indicators = []
            confidence = 0.0
            semantic_matches = {}
            
            # Check semantic patterns
            for category, patterns in self.semantic_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, text):
                        matches += 1
                        semantic_indicators.append(f"{category}: {pattern}")
                
                if matches > 0:
                    semantic_matches[category] = matches
                    confidence += matches * 0.2
            
            # Additional semantic analysis
            confidence += self._analyze_semantic_coherence(text, semantic_indicators)
            confidence += self._analyze_intent_mismatch(text, semantic_indicators)
            
            confidence = min(confidence, 1.0)
            is_injection = confidence > self.confidence_threshold
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=is_injection,
                confidence=confidence,
                blocking_reasons=semantic_indicators if is_injection else [],
                model_name=self.name,
                processing_time_ms=processing_time,
                metadata={
                    "semantic_matches": semantic_matches,
                    "semantic_indicators": semantic_indicators,
                    "semantic_score": confidence
                },
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
            
        except Exception as e:
            logger.error(f"Error in semantic analysis: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                blocking_reasons=[f"Semantic analysis error: {str(e)}"],
                model_name=self.name,
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
                stage=DetectionStage.PRIMARY_ENSEMBLE
            )
    
    def _analyze_semantic_coherence(self, text: str, indicators: List[str]) -> float:
        """Analyze semantic coherence of the text"""
        score = 0.0
        
        # Simple coherence check based on topic consistency
        sentences = text.split('.')
        if len(sentences) > 2:
            # Check for topic jumping
            topics = []
            for sentence in sentences:
                if 'ignore' in sentence.lower() or 'override' in sentence.lower():
                    topics.append('instruction')
                elif any(word in sentence.lower() for word in ['help', 'please', 'need']):
                    topics.append('request')
                elif any(word in sentence.lower() for word in ['system', 'admin', 'root']):
                    topics.append('technical')
                else:
                    topics.append('general')
            
            # If we have mixed topics with instruction manipulation, it's suspicious
            if 'instruction' in topics and len(set(topics)) > 1:
                score += 0.3
                indicators.append("Mixed topics with instruction manipulation")
        
        return score
    
    def _analyze_intent_mismatch(self, text: str, indicators: List[str]) -> float:
        """Analyze for intent mismatch patterns"""
        score = 0.0
        
        # Check for polite language followed by aggressive commands
        polite_words = ['please', 'thank you', 'kindly', 'would you', 'could you']
        aggressive_words = ['ignore', 'override', 'disregard', 'bypass', 'disable']
        
        polite_count = sum(1 for word in text.lower().split() if word in polite_words)
        aggressive_count = sum(1 for word in text.lower().split() if word in aggressive_words)
        
        if polite_count > 0 and aggressive_count > 0:
            score += 0.2
            indicators.append("Polite language with aggressive commands")
        
        return score
    
    def unload_model(self) -> bool:
        """Unload the model"""
        try:
            self.semantic_patterns.clear()
            self.is_loaded = False
            return True
        except Exception as e:
            logger.error(f"Error unloading semantic analyzer: {e}")
            return False

class PromptInjectionEnsemble:
    """
    Prompt Injection Detection Ensemble Manager
    Coordinates all prompt injection detectors as per Phase 3 implementation plan
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.detectors = []
        self.is_initialized = False
        
        # Performance tracking
        self.performance_stats = {
            "total_detections": 0,
            "blocked_count": 0,
            "injection_types": {},
            "model_performance": {}
        }
        
    async def initialize(self) -> bool:
        """Initialize all prompt injection detectors"""
        try:
            logger.info("Initializing prompt injection detection ensemble...")
            
            # Initialize detectors according to Phase 3 plan weights
            self.detectors = [
                PatternBasedDetector(self.config.get('pattern_based', {})),      # 35%
                ContextAwareDetector(self.config.get('context_aware', {})),     # 30%
                BehavioralAnalyzer(self.config.get('behavioral', {})),          # 25%
                SemanticAnalyzer(self.config.get('semantic', {})),              # 10%
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
                logger.error("No prompt injection detectors loaded successfully")
                return False
            
            self.is_initialized = True
            logger.info(f"Prompt injection ensemble initialized with {successful_loads}/{len(self.detectors)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize prompt injection ensemble: {e}")
            return False
    
    async def detect_injection(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Detect prompt injection using ensemble approach"""
        if not self.is_initialized:
            return {"error": "Ensemble not initialized"}
        
        try:
            # Get results from all detectors
            results = []
            for detector in self.detectors:
                if detector.is_loaded:
                    result = await detector.detect(text, context)
                    results.append(result)
            
            if not results:
                return {"error": "No detectors available"}
            
            # Combine results using weighted voting
            total_confidence = 0.0
            total_weight = 0.0
            any_blocked = False
            combined_reasons = []
            
            for result in results:
                weight = next(d.weight for d in self.detectors if d.name == result.model_name)
                weighted_confidence = result.confidence * weight
                
                total_confidence += weighted_confidence
                total_weight += weight
                
                if result.blocked:
                    any_blocked = True
                    combined_reasons.extend(result.blocking_reasons)
            
            # Calculate final confidence
            final_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
            
            # Update statistics
            self.performance_stats["total_detections"] += 1
            if any_blocked:
                self.performance_stats["blocked_count"] += 1
            
            return {
                "injection_detected": any_blocked,
                "confidence": final_confidence,
                "blocked": any_blocked,
                "blocking_reasons": combined_reasons,
                "individual_results": [
                    {
                        "detector": r.model_name,
                        "confidence": r.confidence,
                        "blocked": r.blocked,
                        "reasons": r.blocking_reasons,
                        "weight": next(d.weight for d in self.detectors if d.name == r.model_name)
                    } for r in results
                ],
                "ensemble_confidence": final_confidence
            }
            
        except Exception as e:
            logger.error(f"Error in prompt injection detection: {e}")
            return {"error": str(e)}
    
    def get_detectors(self) -> List[BaseDetector]:
        """Get list of loaded detectors"""
        return [detector for detector in self.detectors if detector.is_loaded]
    
    async def update_config(self, config: Dict[str, Any]) -> None:
        """Update ensemble configuration"""
        self.config.update(config)
        logger.info("Updated prompt injection ensemble configuration")
    
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
            logger.info("Prompt injection ensemble cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during prompt injection ensemble cleanup: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.performance_stats.copy()