"""
Phase 4: Fast Pre-Screening Layer
High-speed rule-based detection with lightweight models for initial filtering
"""

import re
import time
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import unicodedata
import statistics

from app.utils.logger import app_logger
from app.guardrails.models import DetectionResult, PipelineStage, PipelineContext

class PreScreeningStrategy(Enum):
    """Pre-screening detection strategies"""
    RULE_BASED = "rule_based"
    PATTERN_MATCHING = "pattern_matching"
    CHARACTER_ANALYSIS = "character_analysis"
    LENGTH_VALIDATION = "length_validation"
    ENCODING_DETECTION = "encoding_detection"

@dataclass
class PreScreeningRule:
    """Individual pre-screening rule"""
    name: str
    pattern: str
    guardrail_types: List[str]
    confidence_score: float
    case_sensitive: bool = False
    regex_flags: int = re.IGNORECASE
    description: str = ""

@dataclass
class PreScreeningConfig:
    """Configuration for pre-screening layer"""
    enable_character_analysis: bool = True
    enable_length_validation: bool = True
    enable_pattern_matching: bool = True
    enable_encoding_detection: bool = True
    max_text_length: int = 50000
    min_confidence_threshold: float = 0.8
    suspicious_character_threshold: float = 0.1
    
class PreScreeningLayer:
    """
    Fast pre-screening layer with rule-based detection
    
    Features:
    - Character-level analysis for encoding attacks
    - Pattern matching for known attack signatures
    - Length and format validation
    - Suspicious character detection
    - High-speed regex-based filtering
    """
    
    def __init__(self, config: PreScreeningConfig = None):
        self.config = config or PreScreeningConfig()
        self.rules = self._initialize_rules()
        self.suspicious_patterns = self._initialize_suspicious_patterns()
        self.character_blacklist = self._initialize_character_blacklist()
        
        # Performance tracking
        self.screening_stats = {
            "total_processed": 0,
            "blocked_count": 0,
            "average_time_ms": 0.0,
            "rule_hit_counts": {},
            "strategy_performance": {}
        }
        
        app_logger.info("Pre-screening layer initialized with enhanced rule-based detection")
    
    async def screen(
        self, 
        text: str, 
        guardrail_type: str, 
        context: PipelineContext
    ) -> DetectionResult:
        """
        Perform fast pre-screening analysis
        
        Args:
            text: Input text to analyze
            guardrail_type: Type of guardrail to check
            context: Pipeline context
            
        Returns:
            DetectionResult with pre-screening analysis
        """
        start_time = time.time()
        
        try:
            self.screening_stats["total_processed"] += 1
            
            # Run all pre-screening strategies in parallel
            screening_tasks = [
                self._character_analysis(text, guardrail_type),
                self._length_validation(text, guardrail_type),
                self._pattern_matching(text, guardrail_type),
                self._encoding_detection(text, guardrail_type),
                self._rule_based_detection(text, guardrail_type)
            ]
            
            screening_results = await asyncio.gather(*screening_tasks, return_exceptions=True)
            
            # Aggregate results
            blocked = False
            confidence_scores = []
            reasons = []
            metadata = {}
            
            for i, strategy in enumerate([
                PreScreeningStrategy.CHARACTER_ANALYSIS,
                PreScreeningStrategy.LENGTH_VALIDATION,
                PreScreeningStrategy.PATTERN_MATCHING,
                PreScreeningStrategy.ENCODING_DETECTION,
                PreScreeningStrategy.RULE_BASED
            ]):
                if isinstance(screening_results[i], Exception):
                    app_logger.warning(f"Pre-screening strategy {strategy.value} failed: {screening_results[i]}")
                    continue
                
                result = screening_results[i]
                if result["blocked"]:
                    blocked = True
                
                confidence_scores.append(result["confidence"])
                reasons.extend(result["reasons"])
                metadata[strategy.value] = result["metadata"]
            
            # Calculate final confidence
            final_confidence = max(confidence_scores) if confidence_scores else 0.0
            
            # Update statistics
            if blocked:
                self.screening_stats["blocked_count"] += 1
            
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_stats(processing_time)
            
            return DetectionResult(
                blocked=blocked,
                confidence=final_confidence,
                stage=PipelineStage.PRE_SCREENING,
                guardrail_type=guardrail_type,
                reasons=reasons,
                metadata={
                    "pre_screening_strategies": metadata,
                    "character_analysis": metadata.get("character_analysis", {}),
                    "pattern_matches": len(reasons)
                },
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            app_logger.error(f"Pre-screening failed for {guardrail_type}: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                stage=PipelineStage.PRE_SCREENING,
                guardrail_type=guardrail_type,
                reasons=[f"Pre-screening error: {str(e)}"],
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _character_analysis(self, text: str, guardrail_type: str) -> Dict[str, Any]:
        """Analyze character-level patterns for suspicious content"""
        if not self.config.enable_character_analysis:
            return {"blocked": False, "confidence": 0.0, "reasons": [], "metadata": {}}
        
        suspicious_chars = 0
        total_chars = len(text)
        suspicious_details = []
        
        # Check for suspicious characters
        for char in text:
            if char in self.character_blacklist:
                suspicious_chars += 1
                suspicious_details.append(f"Suspicious character: {repr(char)}")
        
        # Check for unusual Unicode categories
        unicode_categories = {}
        for char in text:
            category = unicodedata.category(char)
            unicode_categories[category] = unicode_categories.get(category, 0) + 1
        
        # Flag unusual category distributions
        control_chars = unicode_categories.get('Cc', 0)  # Control characters
        format_chars = unicode_categories.get('Cf', 0)   # Format characters
        private_use = unicode_categories.get('Co', 0)    # Private use area
        
        unusual_chars = control_chars + format_chars + private_use
        
        if total_chars > 0:
            suspicious_ratio = (suspicious_chars + unusual_chars) / total_chars
        else:
            suspicious_ratio = 0.0
        
        blocked = suspicious_ratio > self.config.suspicious_character_threshold
        confidence = min(0.95, suspicious_ratio * 2.0) if blocked else 0.0
        
        reasons = []
        if blocked:
            reasons.append(f"High suspicious character ratio: {suspicious_ratio:.2%}")
            reasons.extend(suspicious_details[:3])  # Limit details
        
        return {
            "blocked": blocked,
            "confidence": confidence,
            "reasons": reasons,
            "metadata": {
                "suspicious_char_count": suspicious_chars,
                "unusual_unicode_count": unusual_chars,
                "suspicious_ratio": suspicious_ratio,
                "unicode_categories": unicode_categories
            }
        }
    
    async def _length_validation(self, text: str, guardrail_type: str) -> Dict[str, Any]:
        """Validate text length and format"""
        if not self.config.enable_length_validation:
            return {"blocked": False, "confidence": 0.0, "reasons": [], "metadata": {}}
        
        text_length = len(text)
        blocked = False
        confidence = 0.0
        reasons = []
        
        # Check maximum length
        if text_length > self.config.max_text_length:
            blocked = True
            confidence = 0.9
            reasons.append(f"Text exceeds maximum length: {text_length} > {self.config.max_text_length}")
        
        # Check for extremely long lines (potential obfuscation)
        lines = text.split('\n')
        max_line_length = max(len(line) for line in lines) if lines else 0
        
        if max_line_length > 5000:  # Very long single line
            blocked = True
            confidence = max(confidence, 0.8)
            reasons.append(f"Extremely long line detected: {max_line_length} characters")
        
        # Check for suspicious repetition patterns
        if len(set(text)) < len(text) * 0.1 and len(text) > 100:  # Low character diversity
            blocked = True
            confidence = max(confidence, 0.7)
            reasons.append("Low character diversity detected (potential spam/flooding)")
        
        return {
            "blocked": blocked,
            "confidence": confidence,
            "reasons": reasons,
            "metadata": {
                "text_length": text_length,
                "max_line_length": max_line_length,
                "line_count": len(lines),
                "character_diversity": len(set(text)) / len(text) if text else 0
            }
        }
    
    async def _pattern_matching(self, text: str, guardrail_type: str) -> Dict[str, Any]:
        """Match against known suspicious patterns"""
        if not self.config.enable_pattern_matching:
            return {"blocked": False, "confidence": 0.0, "reasons": [], "metadata": {}}
        
        blocked = False
        max_confidence = 0.0
        reasons = []
        matched_patterns = []
        
        # Get patterns relevant to this guardrail type
        relevant_patterns = self.suspicious_patterns.get(guardrail_type, [])
        
        for pattern_info in relevant_patterns:
            pattern = pattern_info["pattern"]
            confidence = pattern_info["confidence"]
            description = pattern_info["description"]
            
            try:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    blocked = True
                    max_confidence = max(max_confidence, confidence)
                    reasons.append(f"Matched suspicious pattern: {description}")
                    matched_patterns.append(description)
                    
            except re.error as e:
                app_logger.warning(f"Invalid regex pattern: {pattern}, error: {e}")
        
        return {
            "blocked": blocked,
            "confidence": max_confidence,
            "reasons": reasons,
            "metadata": {
                "patterns_checked": len(relevant_patterns),
                "patterns_matched": len(matched_patterns),
                "matched_pattern_descriptions": matched_patterns
            }
        }
    
    async def _encoding_detection(self, text: str, guardrail_type: str) -> Dict[str, Any]:
        """Detect encoding-based attacks and obfuscation"""
        if not self.config.enable_encoding_detection:
            return {"blocked": False, "confidence": 0.0, "reasons": [], "metadata": {}}
        
        blocked = False
        confidence = 0.0
        reasons = []
        encoding_issues = []
        
        # Check for common encoding attack patterns
        suspicious_encodings = [
            r'&#x[0-9a-fA-F]+;',     # HTML hex entities
            r'&#[0-9]+;',             # HTML decimal entities
            r'%[0-9a-fA-F]{2}',       # URL encoding
            r'\\u[0-9a-fA-F]{4}',     # Unicode escape sequences
            r'\\x[0-9a-fA-F]{2}',     # Hex escape sequences
        ]
        
        for pattern in suspicious_encodings:
            matches = re.findall(pattern, text)
            if len(matches) > 10:  # High count of encoded characters
                blocked = True
                confidence = max(confidence, 0.8)
                reasons.append(f"High count of encoded characters: {len(matches)} {pattern}")
                encoding_issues.append(f"{len(matches)} matches of {pattern}")
        
        # Check for mixed scripts (potential homograph attacks)
        scripts = set()
        for char in text:
            if char.isalpha():
                script = unicodedata.name(char, "UNKNOWN").split()[0]
                scripts.add(script)
        
        if len(scripts) > 3:  # Multiple scripts in one text
            blocked = True
            confidence = max(confidence, 0.7)
            reasons.append(f"Multiple scripts detected: {len(scripts)} different scripts")
            encoding_issues.append(f"Scripts: {list(scripts)[:5]}")  # Limit output
        
        return {
            "blocked": blocked,
            "confidence": confidence,
            "reasons": reasons,
            "metadata": {
                "encoding_issues": encoding_issues,
                "script_count": len(scripts),
                "detected_scripts": list(scripts)
            }
        }
    
    async def _rule_based_detection(self, text: str, guardrail_type: str) -> Dict[str, Any]:
        """Apply rule-based detection for the specific guardrail type"""
        blocked = False
        max_confidence = 0.0
        reasons = []
        matched_rules = []
        
        # Get rules relevant to this guardrail type
        relevant_rules = [rule for rule in self.rules if guardrail_type in rule.guardrail_types]
        
        for rule in relevant_rules:
            try:
                flags = rule.regex_flags if not rule.case_sensitive else 0
                
                if re.search(rule.pattern, text, flags):
                    blocked = True
                    max_confidence = max(max_confidence, rule.confidence_score)
                    reasons.append(f"Rule triggered: {rule.name}")
                    matched_rules.append(rule.name)
                    
                    # Update rule hit statistics
                    self.screening_stats["rule_hit_counts"][rule.name] = (
                        self.screening_stats["rule_hit_counts"].get(rule.name, 0) + 1
                    )
                    
            except re.error as e:
                app_logger.warning(f"Invalid regex in rule {rule.name}: {e}")
        
        return {
            "blocked": blocked,
            "confidence": max_confidence,
            "reasons": reasons,
            "metadata": {
                "rules_checked": len(relevant_rules),
                "rules_matched": len(matched_rules),
                "matched_rule_names": matched_rules
            }
        }
    
    def _initialize_rules(self) -> List[PreScreeningRule]:
        """Initialize pre-screening rules for different guardrail types"""
        return [
            # Toxicity rules
            PreScreeningRule(
                name="explicit_toxicity",
                pattern=r'\b(kill\s+yourself|kys|die\s+in\s+a\s+fire|rot\s+in\s+hell)\b',
                guardrail_types=["toxicity"],
                confidence_score=0.95,
                description="Explicit toxic language"
            ),
            PreScreeningRule(
                name="hate_speech_slurs",
                pattern=r'\b(n[i1!]gg[ae3]r|f[a4@]gg[o0]t|ret[a4@]rd)\b',
                guardrail_types=["toxicity"],
                confidence_score=0.98,
                description="Hate speech slurs"
            ),
            
            # PII rules
            PreScreeningRule(
                name="ssn_pattern",
                pattern=r'\b\d{3}-\d{2}-\d{4}\b',
                guardrail_types=["pii"],
                confidence_score=0.9,
                description="Social Security Number pattern"
            ),
            PreScreeningRule(
                name="credit_card_pattern",
                pattern=r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                guardrail_types=["pii"],
                confidence_score=0.85,
                description="Credit card number pattern"
            ),
            PreScreeningRule(
                name="email_pattern",
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                guardrail_types=["pii"],
                confidence_score=0.7,
                description="Email address pattern"
            ),
            
            # Prompt injection rules
            PreScreeningRule(
                name="prompt_injection_commands",
                pattern=r'\b(ignore\s+previous\s+instructions|forget\s+everything|system\s+prompt|jailbreak)\b',
                guardrail_types=["prompt_injection"],
                confidence_score=0.9,
                description="Prompt injection commands"
            ),
            PreScreeningRule(
                name="role_play_injection",
                pattern=r'\b(pretend\s+to\s+be|act\s+as\s+if|roleplay\s+as|simulate\s+being)\b',
                guardrail_types=["prompt_injection"],
                confidence_score=0.7,
                description="Role-playing injection attempts"
            ),
            
            # Spam rules
            PreScreeningRule(
                name="excessive_caps",
                pattern=r'\b[A-Z]{10,}\b',
                guardrail_types=["spam"],
                confidence_score=0.6,
                description="Excessive capital letters"
            ),
            PreScreeningRule(
                name="repeated_exclamation",
                pattern=r'!{5,}',
                guardrail_types=["spam"],
                confidence_score=0.7,
                description="Excessive exclamation marks"
            )
        ]
    
    def _initialize_suspicious_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize suspicious patterns by guardrail type"""
        return {
            "toxicity": [
                {
                    "pattern": r'\b(worthless|pathetic|disgusting)\s+(human|person|being)\b',
                    "confidence": 0.8,
                    "description": "Dehumanizing language"
                },
                {
                    "pattern": r'\b(should\s+die|deserve\s+to\s+die|better\s+off\s+dead)\b',
                    "confidence": 0.9,
                    "description": "Death wishes"
                }
            ],
            "prompt_injection": [
                {
                    "pattern": r'(DAN|Do\s+Anything\s+Now)',
                    "confidence": 0.85,
                    "description": "DAN jailbreak attempt"
                },
                {
                    "pattern": r'\\n\\n.*?(Human|Assistant):',
                    "confidence": 0.7,
                    "description": "Conversation simulation attempt"
                }
            ],
            "pii": [
                {
                    "pattern": r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b',
                    "confidence": 0.8,
                    "description": "Credit card with spaces"
                }
            ]
        }
    
    def _initialize_character_blacklist(self) -> Set[str]:
        """Initialize set of suspicious characters"""
        return {
            '\u200b',  # Zero width space
            '\u200c',  # Zero width non-joiner
            '\u200d',  # Zero width joiner
            '\ufeff',  # Zero width no-break space
            '\u00a0',  # Non-breaking space
        }
    
    def _update_performance_stats(self, processing_time: float):
        """Update performance statistics"""
        current_avg = self.screening_stats["average_time_ms"]
        total_processed = self.screening_stats["total_processed"]
        
        # Calculate running average
        if total_processed == 1:
            self.screening_stats["average_time_ms"] = processing_time
        else:
            self.screening_stats["average_time_ms"] = (
                (current_avg * (total_processed - 1) + processing_time) / total_processed
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get pre-screening performance statistics"""
        total_processed = self.screening_stats["total_processed"]
        blocked_count = self.screening_stats["blocked_count"]
        
        return {
            "total_processed": total_processed,
            "total_blocked": blocked_count,
            "block_rate": blocked_count / total_processed if total_processed > 0 else 0,
            "average_processing_time_ms": self.screening_stats["average_time_ms"],
            "top_triggered_rules": sorted(
                self.screening_stats["rule_hit_counts"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }