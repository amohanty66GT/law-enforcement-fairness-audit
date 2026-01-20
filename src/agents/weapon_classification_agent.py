"""
Weapon Classification Agent - Normalizes weapon text into fixed categories.
Uses rule-based mapping with explicit fallbacks and confidence flags.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from .base import BaseAgent, AgentMessage, AgentExecutionContext, ClassificationResult, ProcessingError, ValidationResult

class WeaponClassificationAgent(BaseAgent):
    """Agent responsible for weapon classification from text descriptions."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("weapon_classification_agent", config)
        self.weapon_categories = ["firearm", "knife", "blunt_object", "none", "unknown", "other"]
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self._initialize_classification_rules()
        
    def execute(self, context: AgentExecutionContext, input_data: Any) -> AgentMessage:
        """Execute weapon classification on validated data."""
        self.log_execution("starting_weapon_classification", {"record_count": len(input_data)})
        
        try:
            # Convert to DataFrame for processing
            df = pd.DataFrame(input_data)
            
            # Extract weapon information from text fields
            weapon_classifications = []
            
            for idx, record in df.iterrows():
                # Combine relevant text fields
                text_content = self._extract_text_content(record)
                
                # Classify weapon
                classification = self._classify_weapon(text_content, record.get('uid', f'record_{idx}'))
                
                # Add to record
                weapon_classifications.append({
                    'record_id': record.get('uid', f'record_{idx}'),
                    'weapon_raw': text_content,
                    'weapon_category': classification.category,
                    'weapon_confidence': classification.confidence,
                    'classification_metadata': classification.metadata
                })
            
            # Add weapon classifications back to records
            classified_records = self._merge_classifications(input_data, weapon_classifications)
            
            # Generate classification statistics
            classification_stats = self._generate_classification_stats(weapon_classifications)
            
            self.log_execution("weapon_classification_completed", {
                "records_classified": len(weapon_classifications),
                "category_distribution": classification_stats["category_distribution"]
            })
            
            return self.create_message(
                message_type="weapon_classified_data",
                data=classified_records,
                metadata={
                    "classification_time": pd.Timestamp.now().isoformat(),
                    "classification_stats": classification_stats,
                    "agent_version": "1.0",
                    "categories_used": self.weapon_categories
                }
            )
            
        except Exception as e:
            self.log_execution("weapon_classification_failed", {"error": str(e)})
            raise ProcessingError(self.agent_id, f"Weapon classification failed: {str(e)}")
    
    def _initialize_classification_rules(self):
        """Initialize weapon classification rules and patterns."""
        self.classification_rules = {
            'firearm': {
                'patterns': [
                    r'\b(gun|firearm|pistol|rifle|shotgun|revolver)\b',
                    r'\b(weapon|armed|shooting|shot|bullet|ammunition)\b',
                    r'\b(handgun|automatic|semi-automatic)\b',
                    r'\b(caliber|\.22|\.38|\.45|9mm)\b',
                    r'\b(ak-47|ar-15|glock|smith|wesson)\b',
                    r'\b(firearm|gunshot|gunfire)\b'
                ],
                'confidence_weights': [0.9, 0.8, 0.85, 0.8, 0.95, 0.9],
                'exclusions': [r'\b(toy|fake|replica|water)\b']
            },
            'knife': {
                'patterns': [
                    r'\b(knife|blade|stabbing|stabbed)\b',
                    r'\b(cut|cutting|slash|slashing)\b',
                    r'\b(machete|sword|dagger|razor)\b',
                    r'\b(sharp object|edged weapon)\b'
                ],
                'confidence_weights': [0.9, 0.7, 0.85, 0.8],
                'exclusions': [r'\b(butter|kitchen|cooking)\b']
            },
            'blunt_object': {
                'patterns': [
                    r'\b(bat|club|hammer|pipe|stick)\b',
                    r'\b(bludgeon|blunt object|beating|beaten)\b',
                    r'\b(struck with|hit with|baseball bat)\b',
                    r'\b(crowbar|wrench|brick|rock)\b'
                ],
                'confidence_weights': [0.8, 0.9, 0.85, 0.8],
                'exclusions': []
            },
            'none': {
                'patterns': [
                    r'\b(unarmed|no weapon|without weapon)\b',
                    r'\b(bare hands|fists|physical force)\b',
                    r'\b(non-violent|fraud|cyber|computer)\b'
                ],
                'confidence_weights': [0.9, 0.8, 0.7],
                'exclusions': []
            }
        }
    
    def _extract_text_content(self, record: Dict) -> str:
        """Extract and combine relevant text fields for weapon classification."""
        text_fields = ['title', 'description', 'warning_message', 'caution']
        text_parts = []
        
        for field in text_fields:
            if field in record and record[field]:
                text_parts.append(str(record[field]))
        
        return ' '.join(text_parts).lower()
    
    def _classify_weapon(self, text_content: str, record_id: str) -> ClassificationResult:
        """Classify weapon based on text content."""
        if not text_content or text_content.strip() == '':
            return ClassificationResult(
                category="unknown",
                confidence=1.0,
                raw_input=text_content,
                metadata={"reason": "empty_text"}
            )
        
        # Score each category
        category_scores = {}
        classification_details = {}
        
        for category, rules in self.classification_rules.items():
            score, details = self._score_category(text_content, rules)
            category_scores[category] = score
            classification_details[category] = details
        
        # Find best match
        best_category = max(category_scores.keys(), key=lambda k: category_scores[k])
        best_score = category_scores[best_category]
        
        # Determine final classification
        if best_score >= self.confidence_threshold:
            final_category = best_category
            confidence = best_score
            reason = "rule_based_match"
        elif best_score > 0.3:  # Some evidence but not confident
            final_category = "other"
            confidence = 0.5
            reason = "low_confidence_match"
        else:
            final_category = "unknown"
            confidence = 0.8  # High confidence in unknown classification
            reason = "no_clear_match"
        
        return ClassificationResult(
            category=final_category,
            confidence=confidence,
            raw_input=text_content,
            metadata={
                "reason": reason,
                "category_scores": category_scores,
                "classification_details": classification_details,
                "record_id": record_id
            }
        )
    
    def _score_category(self, text: str, rules: Dict) -> Tuple[float, Dict]:
        """Score a category based on pattern matching rules."""
        patterns = rules['patterns']
        weights = rules['confidence_weights']
        exclusions = rules.get('exclusions', [])
        
        # Check for exclusions first
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
        
        # Normalize score (max possible score is sum of all weights)
        max_possible_score = sum(weights)
        normalized_score = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        # Apply diminishing returns for multiple matches
        if len(matches) > 1:
            normalized_score = normalized_score * (1.0 + 0.1 * (len(matches) - 1))
            normalized_score = min(normalized_score, 1.0)
        
        details = {
            "matches": matches,
            "match_count": len(matches),
            "raw_score": total_score,
            "normalized_score": normalized_score
        }
        
        return normalized_score, details
    
    def _merge_classifications(self, original_records: List[Dict], classifications: List[Dict]) -> List[Dict]:
        """Merge weapon classifications back into original records."""
        # Create lookup dictionary
        classification_lookup = {
            cls['record_id']: cls for cls in classifications
        }
        
        # Add classifications to records
        enhanced_records = []
        for i, record in enumerate(original_records):
            record_id = record.get('uid', f'record_{i}')
            classification = classification_lookup.get(record_id, {})
            
            # Add weapon fields
            enhanced_record = record.copy()
            enhanced_record.update({
                'weapon_raw': classification.get('weapon_raw', ''),
                'weapon_category': classification.get('weapon_category', 'unknown'),
                'weapon_confidence': classification.get('weapon_confidence', 0.0),
                'weapon_classification_metadata': classification.get('classification_metadata', {})
            })
            
            enhanced_records.append(enhanced_record)
        
        return enhanced_records
    
    def _generate_classification_stats(self, classifications: List[Dict]) -> Dict:
        """Generate statistics about weapon classifications."""
        if not classifications:
            return {"category_distribution": {}, "confidence_stats": {}}
        
        # Category distribution
        categories = [cls['weapon_category'] for cls in classifications]
        category_counts = pd.Series(categories).value_counts().to_dict()
        category_percentages = pd.Series(categories).value_counts(normalize=True).to_dict()
        
        # Confidence statistics
        confidences = [cls['weapon_confidence'] for cls in classifications]
        confidence_stats = {
            "mean_confidence": float(pd.Series(confidences).mean()),
            "median_confidence": float(pd.Series(confidences).median()),
            "min_confidence": float(pd.Series(confidences).min()),
            "max_confidence": float(pd.Series(confidences).max()),
            "low_confidence_count": sum(1 for c in confidences if c < self.confidence_threshold)
        }
        
        # Category-specific confidence
        category_confidence = {}
        for category in set(categories):
            cat_confidences = [
                cls['weapon_confidence'] for cls in classifications 
                if cls['weapon_category'] == category
            ]
            if cat_confidences:
                category_confidence[category] = {
                    "mean": float(pd.Series(cat_confidences).mean()),
                    "count": len(cat_confidences)
                }
        
        return {
            "category_distribution": {
                "counts": category_counts,
                "percentages": category_percentages
            },
            "confidence_stats": confidence_stats,
            "category_confidence": category_confidence,
            "total_classified": len(classifications)
        }
    
    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data for weapon classification."""
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
                warnings.append("No records found with text fields for weapon classification")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )