"""
Training Data Collection for ML Risk Model
Collects historical project data for training ML models
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from .db_adapter import get_project_activities
from .features import compute_features
from .risk_model import RuleBasedRiskModel
from .models import Activity as ActivityModel


def collect_training_data(
    db: Session,
    project_ids: Optional[List[str]] = None,
    use_rule_based_labels: bool = True,
    use_unique_only: bool = True
) -> Tuple[List[Dict], List[float]]:
    """
    Collect training data from historical projects
    
    Args:
        db: Database session
        project_ids: Optional list of specific project IDs to use.
                     If None, uses all projects in database.
        use_rule_based_labels: If True, uses rule-based model predictions as labels.
                               If False, uses actual outcomes (requires outcome tracking).
        use_unique_only: If True, filters out duplicate projects (by file_hash).
                        Only used when project_ids is None.
                        When USE_ML_MODEL=true, this ensures training on unique data only.
    
    Returns:
        Tuple of (features_list, labels_list)
        - features_list: List of feature dictionaries
        - labels_list: List of risk scores (0-100)
    """
    from .db_service import get_all_projects
    from sqlalchemy import text
    
    # Get all projects if not specified
    if project_ids is None:
        projects = get_all_projects(db)
        
        # Filter unique projects by file_hash if requested
        if use_unique_only:
            # Check if file_hash column exists
            try:
                result = db.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='projects' AND column_name='file_hash'
                """))
                has_file_hash = result.first() is not None
            except Exception:
                has_file_hash = False
            
            if has_file_hash:
                # Get unique projects by file_hash (one per unique hash)
                # This ensures we only train on unique CSV files, not duplicates
                unique_projects = {}
                for project in projects:
                    project_id = project["project_id"]
                    # Get file_hash for this project
                    hash_result = db.execute(text("""
                        SELECT file_hash FROM projects WHERE project_id = :project_id
                    """), {"project_id": project_id})
                    row = hash_result.first()
                    file_hash = row[0] if row and row[0] else None
                    
                    if file_hash:
                        # If we haven't seen this hash, add the project
                        if file_hash not in unique_projects:
                            unique_projects[file_hash] = project
                    else:
                        # Projects without hash (old data) - include them
                        # Use project_id as key to ensure uniqueness
                        unique_projects[f"no_hash_{project_id}"] = project
                
                projects = list(unique_projects.values())
                project_ids = [p["project_id"] for p in projects] if projects else []
            else:
                # Column doesn't exist - use all projects (backward compatibility)
                project_ids = [p["project_id"] for p in projects] if projects else []
        else:
            # Use all projects (including duplicates)
            project_ids = [p["project_id"] for p in projects] if projects else []
    
    if not project_ids:
        return [], []
    
    # Initialize rule-based model for labels
    rule_model = RuleBasedRiskModel() if use_rule_based_labels else None
    
    features_list = []
    labels_list = []
    
    # Collect data from each project
    for project_id in project_ids:
        try:
            # Get activities for this project
            activities = get_project_activities(db, project_id)
            
            if not activities:
                continue
            
            # Compute features and labels for each activity
            for activity in activities:
                try:
                    # Compute features
                    features = compute_features(activity, project_id, activities=activities)
                    
                    # Get label (risk score)
                    if use_rule_based_labels and rule_model:
                        # Use rule-based model prediction as label
                        label = rule_model.predict(features)
                    else:
                        # TODO: Use actual project outcomes as labels
                        # This requires tracking actual delays, overruns, etc.
                        # For now, fallback to rule-based
                        label = rule_model.predict(features) if rule_model else 0.0
                    
                    features_list.append(features)
                    labels_list.append(label)
                    
                except Exception as e:
                    # Skip activities with errors
                    print(f"Error processing activity {activity.activity_id}: {e}")
                    continue
                    
        except Exception as e:
            # Skip projects with errors
            print(f"Error processing project {project_id}: {e}")
            continue
    
    return features_list, labels_list


def collect_training_data_from_project(
    db: Session,
    project_id: str,
    use_rule_based_labels: bool = True
) -> Tuple[List[Dict], List[float]]:
    """
    Collect training data from a single project
    
    Args:
        db: Database session
        project_id: Project ID to collect data from
        use_rule_based_labels: Whether to use rule-based predictions as labels
    
    Returns:
        Tuple of (features_list, labels_list)
    """
    return collect_training_data(
        db,
        project_ids=[project_id],
        use_rule_based_labels=use_rule_based_labels
    )


def get_training_data_stats(
    db: Session,
    project_ids: Optional[List[str]] = None,
    use_unique_only: bool = True
) -> Dict:
    """
    Get statistics about available training data
    
    Args:
        db: Database session
        project_ids: Optional list of specific project IDs
        use_unique_only: If True, counts only unique projects (by file_hash)
    
    Returns:
        Dictionary with statistics:
        - project_count: Number of projects (unique if use_unique_only=True)
        - activity_count: Total number of activities
        - feature_count: Number of features per activity
        - sample_count: Total training samples available
        - unique_project_count: Number of unique projects (by file_hash)
        - total_project_count: Total projects (including duplicates)
    """
    from .db_service import get_all_projects
    from sqlalchemy import text
    
    # Get all projects if not specified
    if project_ids is None:
        projects = get_all_projects(db)
        
        # Filter unique projects if requested
        if use_unique_only:
            try:
                result = db.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='projects' AND column_name='file_hash'
                """))
                has_file_hash = result.first() is not None
            except Exception:
                has_file_hash = False
            
            total_project_count = len(projects)
            
            if has_file_hash:
                # Count unique projects by file_hash
                unique_projects = {}
                for project in projects:
                    project_id = project["project_id"]
                    hash_result = db.execute(text("""
                        SELECT file_hash FROM projects WHERE project_id = :project_id
                    """), {"project_id": project_id})
                    row = hash_result.first()
                    file_hash = row[0] if row and row[0] else None
                    
                    if file_hash:
                        if file_hash not in unique_projects:
                            unique_projects[file_hash] = project
                    else:
                        unique_projects[f"no_hash_{project_id}"] = project
                
                projects = list(unique_projects.values())
                project_ids = [p["project_id"] for p in projects] if projects else []
                unique_project_count = len(projects)
            else:
                project_ids = [p["project_id"] for p in projects] if projects else []
                unique_project_count = len(projects)
                total_project_count = len(projects)
        else:
            project_ids = [p["project_id"] for p in projects] if projects else []
            unique_project_count = len(projects)
            total_project_count = len(projects)
    else:
        unique_project_count = len(project_ids)
        total_project_count = len(project_ids)
    
    total_activities = 0
    
    for project_id in project_ids:
        try:
            activities = get_project_activities(db, project_id)
            total_activities += len(activities) if activities else 0
        except Exception:
            continue
    
    # Get feature count from a sample
    feature_count = 0
    if project_ids:
        try:
            activities = get_project_activities(db, project_ids[0])
            if activities:
                features = compute_features(activities[0], project_ids[0], activities=activities)
                feature_count = len(features)
        except Exception:
            pass
    
    return {
        "project_count": unique_project_count if use_unique_only else len(project_ids),
        "activity_count": total_activities,
        "feature_count": feature_count,
        "sample_count": total_activities,  # One sample per activity
        "sufficient_data": total_activities >= 50,  # Minimum for training
        "unique_project_count": unique_project_count,
        "total_project_count": total_project_count if use_unique_only else unique_project_count,
        "duplicate_count": total_project_count - unique_project_count if use_unique_only else 0,
    }

