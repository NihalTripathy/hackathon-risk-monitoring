"""
ML Model Training API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict
from core.database import get_db
from core.auth_dependencies import get_current_user
from core.config import ML_MODEL_PATH, ML_MIN_TRAINING_SAMPLES
from api.auth import UserResponse
import os

router = APIRouter()

# Lazy import ML modules to avoid errors if dependencies not installed
def _check_ml_dependencies():
    """Check if ML dependencies are available"""
    try:
        import joblib
        import sklearn
        return True
    except ImportError:
        return False


def _get_ml_modules():
    """Get ML modules if available"""
    if not _check_ml_dependencies():
        raise HTTPException(
            status_code=503,
            detail="ML dependencies not installed. Install with: pip install scikit-learn joblib"
        )
    from core.ml_risk_model import MLRiskModel
    from core.ml_training_data import collect_training_data, get_training_data_stats
    return MLRiskModel, collect_training_data, get_training_data_stats


@router.get("/ml/status")
def get_ml_status(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get ML model status and availability.
    Shows what's configured AND what's actually being used.
    """
    from core.config import USE_ML_MODEL, ML_ENSEMBLE_WEIGHT
    
    ml_deps_available = _check_ml_dependencies()
    
    if not ml_deps_available:
        return {
            "ml_enabled": False,
            "model_available": False,
            "ml_dependencies_installed": False,
            "error": "ML dependencies not installed. Install with: pip install scikit-learn joblib",
            "training_data": {"project_count": 0, "activity_count": 0, "sufficient_data": False},
            "can_train": False,
            "min_samples_required": ML_MIN_TRAINING_SAMPLES,
            "active_model": "rule",  # Always rule-based if ML deps not installed
            "message": "ML dependencies not installed - using rule-based model"
        }
    
    MLRiskModel, _, get_training_data_stats = _get_ml_modules()
    
    ml_model = MLRiskModel(ML_MODEL_PATH)
    model_loaded = ml_model.load()
    
    # Get training data stats - use unique projects only when USE_ML_MODEL=true
    from core.config import USE_ML_MODEL
    use_unique_only = USE_ML_MODEL
    stats = get_training_data_stats(db, project_ids=None, use_unique_only=use_unique_only)
    
    # Determine what's actually being used
    if USE_ML_MODEL and model_loaded:
        if ML_ENSEMBLE_WEIGHT == 1.0:
            active_model = "ml"
        elif ML_ENSEMBLE_WEIGHT == 0.0:
            active_model = "rule"
        else:
            active_model = "ensemble"
        message = f"ML model is active ({active_model} mode)"
    elif USE_ML_MODEL and not model_loaded:
        active_model = "rule"
        message = "ML enabled but model not available - using rule-based (fallback)"
    else:
        active_model = "rule"
        message = "Rule-based model is active (USE_ML_MODEL=false)"
    
    return {
        "ml_enabled": USE_ML_MODEL,
        "model_available": model_loaded,
        "model_path": ML_MODEL_PATH,
        "ml_dependencies_installed": True,
        "training_data": stats,
        "can_train": stats["sufficient_data"],
        "min_samples_required": ML_MIN_TRAINING_SAMPLES,
        "active_model": active_model,  # What's actually being used
        "ensemble_weight": ML_ENSEMBLE_WEIGHT if USE_ML_MODEL else None,
        "message": message
    }


@router.get("/ml/metrics")
def get_ml_metrics(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get ML model performance metrics
    """
    MLRiskModel, _, _ = _get_ml_modules()
    ml_model = MLRiskModel(ML_MODEL_PATH)
    
    if not ml_model.load():
        raise HTTPException(status_code=404, detail="ML model not found. Train a model first.")
    
    if not ml_model.metadata:
        return {
            "model_available": True,
            "metrics": {},
            "message": "Model loaded but no metrics available"
        }
    
    return {
        "model_available": True,
        "metadata": ml_model.metadata,
        "feature_importance": ml_model.get_feature_importance() if ml_model.is_trained else {},
    }


@router.post("/ml/train")
def train_ml_model(
    background_tasks: BackgroundTasks,
    project_ids: Optional[list] = None,
    use_background: bool = False,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Train ML model from historical project data
    
    Args:
        project_ids: Optional list of project IDs to use for training.
                    If None, uses all projects.
        use_background: If True, trains in background (returns immediately)
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Training results or job status
    """
    MLRiskModel, collect_training_data, get_training_data_stats = _get_ml_modules()
    
    # Check training data availability - use unique projects only when USE_ML_MODEL=true
    from core.config import USE_ML_MODEL
    use_unique_only = USE_ML_MODEL
    stats = get_training_data_stats(db, project_ids, use_unique_only=use_unique_only)
    
    if not stats["sufficient_data"]:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient training data: {stats['activity_count']} activities. "
                   f"Minimum required: {ML_MIN_TRAINING_SAMPLES}"
        )
    
    def _train_model():
        """Internal training function"""
        try:
            # Collect training data - use unique projects only when USE_ML_MODEL=true
            # This ensures we don't train on duplicate CSV files
            from core.config import USE_ML_MODEL
            use_unique_only = USE_ML_MODEL  # Only filter duplicates when ML is enabled
            
            X, y = collect_training_data(
                db, 
                project_ids, 
                use_rule_based_labels=True,
                use_unique_only=use_unique_only
            )
            
            if len(X) < ML_MIN_TRAINING_SAMPLES:
                return {
                    "success": False,
                    "error": f"Insufficient data: {len(X)} samples"
                }
            
            # Train model
            ml_model = MLRiskModel(ML_MODEL_PATH)
            metrics = ml_model.train(X, y)
            
            # Save model
            model_path = ml_model.save()
            
            return {
                "success": True,
                "metrics": metrics,
                "model_path": model_path,
                "training_samples": len(X),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    if use_background:
        # Train in background
        background_tasks.add_task(_train_model)
        return {
            "status": "training_started",
            "message": "Model training started in background. Check /api/ml/status for progress.",
            "training_data_stats": stats
        }
    else:
        # Train synchronously
        result = _train_model()
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Training failed"))
        
        return result


@router.post("/ml/retrain")
def retrain_ml_model(
    background_tasks: BackgroundTasks,
    use_background: bool = False,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Retrain ML model with all available data
    """
    return train_ml_model(background_tasks, project_ids=None, use_background=use_background, db=db, current_user=current_user)


@router.delete("/ml/model")
def delete_ml_model(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete ML model (revert to rule-based only)
    """
    # No need for ML modules to delete files
    metadata_path = ML_MODEL_PATH.replace('.pkl', '_metadata.json')
    
    deleted_files = []
    
    if os.path.exists(ML_MODEL_PATH):
        os.remove(ML_MODEL_PATH)
        deleted_files.append(ML_MODEL_PATH)
    
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
        deleted_files.append(metadata_path)
    
    if not deleted_files:
        raise HTTPException(status_code=404, detail="ML model not found")
    
    return {
        "success": True,
        "message": "ML model deleted. System will use rule-based model.",
        "deleted_files": deleted_files
    }

