"""
Serious Crime Filter Agent - Identifies serious crimes consistently.
Centralizes logic for homicide, robbery, aggravated assault, etc.
"""

import re
from typing import Dict, List, Optional, Set, Any
import pandas as pd

from .base import BaseAgent, AgentMessage, AgentExecutionContext, ClassificationResult, ProcessingError, ValidationResult

class SeriousCrimeFilterAgent(BaseAgent):
    """Agent responsible for identifying serious crimes."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("serious_crime_filter_agent", config)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.8)
        self._initialize_serious_crime_rules()
        
    def execute(self, context: AgentExecutionContext, input_data: Any) -> AgentMessage:
        """Execute serious crime classification."""
        self.log_execution("starting_serious_crime_classification", {"record_count": len(input_data)})
        
        try:
            # Convert to DataFrame for processing
            df = pd.DataFrame(input_data)
            
            # Classify each record for serious crime status
            serious_crime_classifications = []
            
            for idx, record in df.iterrows():
                # Extract text content
                text_content = self._extract_text_content(record)
                
                # Classify as serious crime
                classification = self._classify_serious_crime(text_content, record.get('uid', f'record_{idx}'))
                
                serious_crime_classifications.append({
                    'record_id': record.get('uid', f'record_{idx}'),
                    'severity_flag': classification.category == 'serious',
                    'severity_confidence': classification.confidence,
                    'severity_type': classification.metadata.get('crime_type', 'unknown'),
                    'severity_metadata': classification.metadata
                })
            
            # Add classifications back to records
            classified_records = self._merge_classifications(input_data, serious_crime_classifications)
            
            # Generate classification statistics
            classification_stats = self._generate_classification_stats(serious_crime_classifications)
            
            self.log_execution("serious_crime_classification_completed", {
                "records_classified": len(serious_crime_classifications),
                "serious_crimes_identified": classification_stats["serious_crime_count"]
            })
            
            return self.create_message(
                message_type="serious_crime_classified_data",
                data=classified_records,
                metadata={
                    "classification_time": pd.Timestamp.now().isoformat(),
                    "classification_stats": classification_stats,
                    "agent_version": "1.0"
                }
            )
            
        except Exception as e:
            self.log_execution("serious_crime_classification_failed", {"error": str(e)})
            raise ProcessingError(self.agent_id, f"Serious crime classification failed: {str(e)}")
    
    def _initialize_serious_crime_rules(self):
        """Initialize serious crime classification rules."""
        self.serious_crime_rules = {
            'homicide': {
                'patterns': [
                    r'\b(murder|homicide|manslaughter|killing|killed)\b',
                    r'\b(death|deadly|fatal|fatally)\b',
                    r'\b(assassination|execution)\b'
                ],
                'confidence_weights': [0.95, 0.8, 0.9],
                'exclusions': [r'\b(attempted|conspiracy|threat)\b']
            },
            'assault': {
                'patterns': [
                    r'\b(aggravated assault|assault with deadly weapon)\b',
                    r'\b(violent assault|brutal attack)\b',
                    r'\b(beating|battered|brutally)\b'
                ],
                'confidence_weights': [0.95, 0.85, 0.8],
                'exclusions': [r'\b(simple assault|minor)\b']
            },
            'robbery': {
                'patterns': [
                    r'\b(armed robbery|bank robbery|robbery)\b',
                    r'\b(robbed|robbing|heist)\b',
                    r'\b(hold-up|holdup|stick-up)\b'
                ],
                'confidence_weights': [0.9, 0.85, 0.8],
                'exclusions': [r'\b(petty theft|shoplifting)\b']
            },
            'kidnapping': {
                'patterns': [
                    r'\b(kidnapping|kidnapped|abduction|abducted)\b',
                    r'\b(hostage|held captive|unlawful detention)\b'
                ],
                'confidence_weights': [0.95, 0.9],
                'exclusions': []
            },
            'sexual_assault': {
                'patterns': [
                    r'\b(rape|sexual assault|sexual abuse)\b',
                    r'\b(sexual violence|sexual battery)\b'
                ],
                'confidence_weights': [0.95, 0.9],
                'exclusions': []
            },
            'terrorism': {
                'patterns': [
                    r'\b(terrorism|terrorist|terror attack)\b',
                    r'\b(bombing|explosive|mass shooting)\b',
                    r'\b(domestic terrorism|international terrorism)\b'
                ],
                'confidence_weights': [0.95, 0.9, 0.95],
                'exclusions': []
            },
            'shooting': {
                'patterns': [
                    r'\b(shooting|shot|gunshot|gunfire)\b',
                    r'\b(mass shooting|active shooter)\b',
                    r'\b(drive-by|sniper)\b'
                ],
                'confidence_weights': [0.85, 0.95, 0.9],
                'exclusions': [r'\b(accidental|negligent)\b']
            }
        }
        
        # Non-serious crime patterns (for exclusion)
        self.non_serious_patterns = [
            r'\b(fraud|embezzlement|tax evasion|money laundering)\b',
            r'\b(cyber crime|computer fraud|identity theft)\b',
            r'\b(drug trafficking|narcotics|drug possession)\b',
            r'\b(white collar|financial crime)\b',
            r'\b(forgery|counterfeiting|bribery)\b'
        ]
    
    def _extract_text_content(self, record: Dict) -> str:
        """Extract relevant text fields for serious crime classification."""
        text_fields = ['title', 'description', 'warning_message', 'caution']
        text_parts = []
        
        for field in text_fields:
            if field in record and record[field]:
                text_parts.append(str(record[field]))
        
        return ' '.join(text_parts).lower()
    
    def _classify_serious_crime(self, text_content: str, record_id: str) -> ClassificationResult:
        """Classify whether a crime is serious based on text content."""
        if not text_content or text_content.strip() == '':
            return ClassificationResult(
                category="unknown",
                confidence=0.5,
                raw_input=text_content,
                metadata={"reason": "empty_text"}
            )
        
        # Check for non-serious crime patterns first
        for pattern in self.non_serious_patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                return ClassificationResult(
                    category="non_serious",
                    confidence=0.8,
                    raw_input=text_content,
                    metadata={
                        "reason": "non_serious_pattern_match",
                        "pattern": pattern
                    }
                )
        
        # Score serious crime categories
        category_scores = {}
        best_matches = {}
        
        for crime_type, rules in self.serious_crime_rules.items():
            score, details = self._score_serious_crime_category(text_content, rules)
            category_scores[crime_type] = score
            if score > 0:
                best_matches[crime_type] = details
        
        # Find best match
        if not category_scores or max(category_scores.values()) == 0:
            return ClassificationResult(
                category="non_serious",
                confidence=0.7,
                raw_input=text_content,
                metadata={"reason": "no_serious_crime_patterns"}
            )
        
        best_crime_type = max(category_scores.keys(), key=lambda k: category_scores[k])
        best_score = category_scores[best_crime_type]
        
        # Determine final classification
        if best_score >= self.confidence_threshold:
            category = "serious"
            confidence = best_score
        elif best_score > 0.5:
            category = "possibly_serious"
            confidence = best_score * 0.8  # Reduce confidence for uncertain cases
        else:
            category = "non_serious"
            confidence = 0.7
        
        return ClassificationResult(
            category=category,
            confidence=confidence,
            raw_input=text_content,
            metadata={
                "crime_type": best_crime_type,
                "category_scores": category_scores,
                "best_matches": best_matches.get(best_crime_type, {}),
                "record_id": record_id
            }
        )
    
    def _score_serious_crime_category(self, text: str, rules: Dict) -> tuple:
        """Score a serious crime category based on pattern matching."""
        patterns = rules['patterns']
        weights = rules['confidence_weights']
        exclusions = rules.get('exclusions', [])
        
        # Check for exclusions
        for exclusion in exclusions:
            if re.search(exclusion, text, re.IGNORECASE):
                return 0.0, {"excluded": True, "exclusion_pattern": exclusion}
        
        # Calculate pattern matches
        matches = []
        total_score = 0.0
        
        for pattern, weight in zip(patterns, weights):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matches.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "weight": weight
                })
                total_score += weight
        
        # Normalize score
        max_possible_score = sum(weights)
        normalized_score = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        # Boost score for multiple matches
        if len(matches) > 1:
            normalized_score = min(normalized_score * 1.2, 1.0)
        
        details = {
            "matches": matches,
            "match_count": len(matches),
            "raw_score": total_score,
            "normalized_score": normalized_score
        }
        
        return normalized_score, details
    
    def _merge_classifications(self, original_records: List[Dict], classifications: List[Dict]) -> List[Dict]:
        """Merge serious crime classifications back into original records."""
        classification_lookup = {
            cls['record_id']: cls for cls in classifications
        }
        
        enhanced_records = []
        for i, record in enumerate(original_records):
            record_id = record.get('uid', f'record_{i}')
            classification = classification_lookup.get(record_id, {})
            
            enhanced_record = record.copy()
            enhanced_record.update({
                'severity_flag': classification.get('severity_flag', False),
                'severity_confidence': classification.get('severity_confidence', 0.0),
                'severity_type': classification.get('severity_type', 'unknown'),
                'severity_classification_metadata': classification.get('severity_metadata', {})
            })
            
            enhanced_records.append(enhanced_record)
        
        return enhanced_records
    
    def _generate_classification_stats(self, classifications: List[Dict]) -> Dict:
        """Generate statistics about serious crime classifications."""
        if not classifications:
            return {"serious_crime_count": 0, "serious_crime_rate": 0.0}
        
        serious_crimes = [cls for cls in classifications if cls['severity_flag']]
        serious_crime_types = [cls['severity_type'] for cls in serious_crimes]
        
        # Type distribution
        type_counts = pd.Series(serious_crime_types).value_counts().to_dict() if serious_crime_types else {}
        
        # Confidence statistics
        confidences = [cls['severity_confidence'] for cls in classifications]
        serious_confidences = [cls['severity_confidence'] for cls in serious_crimes]
        
        stats = {
            "total_records": len(classifications),
            "serious_crime_count": len(serious_crimes),
            "serious_crime_rate": len(serious_crimes) / len(classifications),
            "serious_crime_types": type_counts,
            "confidence_stats": {
                "overall_mean": float(pd.Series(confidences).mean()) if confidences else 0.0,
                "serious_crimes_mean": float(pd.Series(serious_confidences).mean()) if serious_confidences else 0.0,
                "high_confidence_count": sum(1 for c in confidences if c >= self.confidence_threshold)
            }
        }
        
        return stats
    
    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data for serious crime classification."""
        errors = []
        warnings = []
        
        if not isinstance(input_data, list):
            errors.append("Input data must be a list of records")
        elif len(input_data) == 0:
            errors.append("Input data cannot be empty")
        else:
            # Check if records have text fields for classification
            text_fields = ['title', 'description', 'warning_message', 'caution']
            records_with_text = 0
            
            for record in input_data[:10]:  # Sample first 10 records
                if any(field in record and record[field] for field in text_fields):
                    records_with_text += 1
            
            if records_with_text == 0:
                warnings.append("No records found with text fields for serious crime classification")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )