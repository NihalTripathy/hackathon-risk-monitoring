"""
ML-based Risk Model Implementation
Replaces/enhances rule-based risk model with machine learning
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

from .config import ML_MODEL_PATH, ML_MIN_TRAINING_SAMPLES
from .risk_model import RuleBasedRiskModel


class MLRiskModel:
    """
    Machine Learning-based risk prediction model
    Uses Random Forest to learn from historical project data
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or ML_MODEL_PATH
        self.model: Optional[RandomForestRegressor] = None
        self.feature_names: List[str] = []
        self.metadata: Dict = {}
        self.is_trained = False
        
    def _get_feature_names(self) -> List[str]:
        """Get list of feature names used for training"""
        return [
            "delay_baseline_days",
            "float_days",
            "progress_slip",
            "expected_delay_days",
            "is_on_critical_path",
            "predecessor_count",
            "successor_count",
            "downstream_critical_depth",
            "in_degree",
            "out_degree",
            "resource_utilization",
            "resource_overbooked",
            "percent_complete",
            "risk_probability",
            "risk_delay_impact_days",
            "cost_impact_of_risk",
        ]
    
    def _extract_features(self, features: Dict) -> np.ndarray:
        """Extract feature vector from features dictionary"""
        feature_names = self._get_feature_names()
        feature_vector = []
        
        for name in feature_names:
            value = features.get(name, 0.0)
            # Convert boolean to float
            if isinstance(value, bool):
                value = 1.0 if value else 0.0
            # Handle None values
            if value is None:
                value = 0.0
            feature_vector.append(float(value))
        
        return np.array(feature_vector).reshape(1, -1)
    
    def train(self, X: List[Dict], y: List[float], test_size: float = 0.2) -> Dict:
        """
        Train the ML model on historical data
        
        Args:
            X: List of feature dictionaries
            y: List of target risk scores (0-100)
            test_size: Fraction of data to use for testing
        
        Returns:
            Dictionary with training metrics
        """
        if len(X) < ML_MIN_TRAINING_SAMPLES:
            raise ValueError(
                f"Insufficient training data: {len(X)} samples. "
                f"Minimum required: {ML_MIN_TRAINING_SAMPLES}"
            )
        
        # Extract feature vectors
        feature_names = self._get_feature_names()
        X_array = []
        for features in X:
            feature_vector = []
            for name in feature_names:
                value = features.get(name, 0.0)
                if isinstance(value, bool):
                    value = 1.0 if value else 0.0
                if value is None:
                    value = 0.0
                feature_vector.append(float(value))
            X_array.append(feature_vector)
        
        X_array = np.array(X_array)
        y_array = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_array, y_array, test_size=test_size, random_state=42
        )
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        self.feature_names = feature_names
        self.is_trained = True
        
        # Evaluate
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)
        
        # Calculate metrics
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        train_mse = mean_squared_error(y_train, y_train_pred)
        test_mse = mean_squared_error(y_test, y_test_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='r2')
        
        # Feature importance
        feature_importance = dict(zip(feature_names, self.model.feature_importances_))
        
        metrics = {
            "train_r2": float(train_r2),
            "test_r2": float(test_r2),
            "train_mae": float(train_mae),
            "test_mae": float(test_mae),
            "train_mse": float(train_mse),
            "test_mse": float(test_mse),
            "cv_r2_mean": float(cv_scores.mean()),
            "cv_r2_std": float(cv_scores.std()),
            "feature_importance": feature_importance,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "total_samples": len(X),
        }
        
        self.metadata = {
            "trained_at": datetime.now().isoformat(),
            "metrics": metrics,
            "model_type": "RandomForestRegressor",
            "feature_count": len(feature_names),
        }
        
        return metrics
    
    def predict(self, features: Dict) -> float:
        """
        Predict risk score for given features
        
        Args:
            features: Feature dictionary
        
        Returns:
            Risk score (0-100)
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first or load a saved model.")
        
        feature_vector = self._extract_features(features)
        prediction = self.model.predict(feature_vector)[0]
        
        # Ensure prediction is in 0-100 range
        return max(0.0, min(100.0, float(prediction)))
    
    def save(self, path: Optional[str] = None) -> str:
        """Save model to disk"""
        if not self.is_trained or self.model is None:
            raise ValueError("No model to save. Train or load a model first.")
        
        save_path = path or self.model_path
        metadata_path = save_path.replace('.pkl', '_metadata.json')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        
        # Save model
        joblib.dump(self.model, save_path)
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        return save_path
    
    def load(self, path: Optional[str] = None) -> bool:
        """Load model from disk"""
        load_path = path or self.model_path
        metadata_path = load_path.replace('.pkl', '_metadata.json')
        
        if not os.path.exists(load_path):
            return False
        
        try:
            # Load model
            self.model = joblib.load(load_path)
            self.model_path = load_path
            self.feature_names = self._get_feature_names()
            self.is_trained = True
            
            # Load metadata if available
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    "trained_at": "unknown",
                    "metrics": {},
                    "model_type": "RandomForestRegressor",
                }
            
            return True
        except Exception as e:
            print(f"Error loading ML model: {e}")
            return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if not self.is_trained or self.model is None:
            return {}
        
        return dict(zip(self.feature_names, self.model.feature_importances_))


class HybridRiskModel:
    """
    Hybrid model that combines ML and rule-based predictions
    Provides fallback and ensemble capabilities
    """
    
    def __init__(self, ml_model_path: Optional[str] = None, ml_weight: float = 0.7):
        self.ml_model = MLRiskModel(ml_model_path)
        self.rule_model = RuleBasedRiskModel()
        self.ml_weight = ml_weight
        self.rule_weight = 1.0 - ml_weight
        self.ml_available = False
        
        # Try to load ML model
        self.ml_available = self.ml_model.load()
    
    def predict(self, features: Dict, use_ml: bool = True, fallback_to_rule: bool = True, project_features: Optional[List[Dict]] = None) -> Tuple[float, str]:
        """
        Predict risk score using hybrid approach
        
        Args:
            features: Feature dictionary
            use_ml: Whether to use ML model if available
            fallback_to_rule: Whether to fallback to rule-based if ML fails
            project_features: Optional list of all activity features for project-wide normalization (used by rule-based component)
        
        Returns:
            Tuple of (risk_score, method_used)
            method_used: "ml", "rule", "ensemble", or "ml_fallback"
        """
        ml_score = None
        rule_score = self.rule_model.predict(features, project_features=project_features)
        
        # Try ML prediction
        if use_ml and self.ml_available:
            try:
                ml_score = self.ml_model.predict(features)
            except Exception as e:
                print(f"ML prediction failed: {e}")
                ml_score = None
        
        # Determine which method to use
        if ml_score is not None and use_ml:
            if self.ml_weight == 1.0:
                # Pure ML
                return ml_score, "ml"
            elif self.ml_weight == 0.0:
                # Pure rule-based
                return rule_score, "rule"
            else:
                # Ensemble
                ensemble_score = (self.ml_weight * ml_score) + (self.rule_weight * rule_score)
                return ensemble_score, "ensemble"
        else:
            # Fallback to rule-based
            if fallback_to_rule:
                return rule_score, "ml_fallback" if use_ml else "rule"
            else:
                raise ValueError("ML model not available and fallback disabled")
    
    def is_ml_available(self) -> bool:
        """Check if ML model is available"""
        return self.ml_available
    
    def get_model_info(self) -> Dict:
        """Get information about available models"""
        info = {
            "rule_based_available": True,
            "ml_available": self.ml_available,
            "ml_weight": self.ml_weight,
            "rule_weight": self.rule_weight,
        }
        
        if self.ml_available and self.ml_model.metadata:
            info["ml_metadata"] = self.ml_model.metadata
        
        return info

