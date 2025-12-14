"""
CSV file connector implementation.
Refactored to use the BaseConnector interface.
"""

import pandas as pd
import os
from typing import List
from .base import BaseConnector, ConnectorConfig, ConnectorResult
from core.models import Activity


class CSVConnector(BaseConnector):
    """
    Connector for loading activities from CSV files.
    
    This is the refactored version of the original CSV connector,
    now implementing the BaseConnector interface for consistency.
    """
    
    def connect(self) -> bool:
        """CSV files don't require active connection"""
        file_path = self.config.connection_params.get("file_path")
        if not file_path:
            raise ValueError("file_path is required in connection_params")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        return True
    
    def load_activities(self, project_id: str) -> ConnectorResult:
        """
        Load activities from CSV file.
        
        Args:
            project_id: Project ID to associate activities with
            
        Returns:
            ConnectorResult with activities and metadata
        """
        errors = []
        warnings = []
        
        try:
            # Validate connection
            if not self.connect():
                return ConnectorResult(
                    success=False,
                    activities=[],
                    errors=["Failed to connect to CSV file"]
                )
            
            file_path = self.config.connection_params["file_path"]
            
            # Load CSV
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                return ConnectorResult(
                    success=False,
                    activities=[],
                    errors=[f"Failed to read CSV file: {str(e)}"]
                )
            
            # Convert to activities
            activities = []
            for idx, row in df.iterrows():
                try:
                    activity = self._row_to_activity(row, project_id)
                    # Sanitize
                    activity = self.sanitize_activity(activity)
                    activities.append(activity)
                except Exception as e:
                    errors.append(f"Row {idx + 1}: {str(e)}")
                    continue
            
            # Validate activities
            if self.config.validate_data:
                valid_activities, validation_errors = self.validate_activities(activities)
                errors.extend(validation_errors)
                activities = valid_activities
            
            metadata = {
                "source": "csv",
                "file_path": file_path,
                "total_rows": len(df),
                "valid_activities": len(activities),
                "invalid_rows": len(errors)
            }
            
            return ConnectorResult(
                success=len(errors) == 0 or len(activities) > 0,
                activities=activities,
                metadata=metadata,
                errors=errors if errors else None,
                warnings=warnings if warnings else None
            )
            
        except Exception as e:
            return ConnectorResult(
                success=False,
                activities=[],
                errors=[f"Unexpected error: {str(e)}"]
            )
    
    def test_connection(self) -> dict:
        """Test CSV file accessibility"""
        try:
            file_path = self.config.connection_params.get("file_path")
            if not file_path:
                return {
                    "success": False,
                    "error": "file_path not provided"
                }
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            # Try to read first few rows
            df = pd.read_csv(file_path, nrows=5)
            
            return {
                "success": True,
                "file_path": file_path,
                "columns": list(df.columns),
                "sample_rows": len(df)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _row_to_activity(self, row: pd.Series, project_id: str) -> Activity:
        """Convert CSV row to Activity model (reusing original logic)"""
        # Helper functions (same as original csv_connector)
        def _clean_value(value):
            if pd.isna(value):
                return None
            return value
        
        def _clean_string_value(value):
            if pd.isna(value) or value is None:
                return None
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    return None
                return value
            return str(value) if value else None
        
        def _get_column_value(row, possible_names, default=0):
            for name in possible_names:
                if name in row.index:
                    value = row[name]
                    if pd.isna(value):
                        return default
                    return value
            return default
        
        def _get_string_column_value(row, possible_names):
            for name in possible_names:
                if name in row.index:
                    return _clean_string_value(row[name])
            return None
        
        def _get_required_string_column_value(row, possible_names, column_description="column"):
            """Get required string value from row using multiple possible column names, raises error if not found"""
            for name in possible_names:
                if name in row.index:
                    value = _clean_string_value(row[name])
                    if value is None or value == "":
                        raise ValueError(f"Required {column_description} column found ('{name}') but value is empty")
                    return value
            
            # If not found, provide helpful error message with available columns
            available_columns = list(row.index)
            raise ValueError(
                f"Required {column_description} column not found. "
                f"Expected one of: {', '.join(possible_names)}. "
                f"Available columns: {', '.join(available_columns)}"
            )
        
        def _parse_bool_value(value):
            if pd.isna(value) or value is None:
                return False
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                value = value.strip().lower()
                if value in ('true', '1', 'yes', 'y', 'on'):
                    return True
                if value in ('false', '0', 'no', 'n', 'off', ''):
                    return False
            return False
        
        def _parse_percent_value(value):
            if pd.isna(value) or value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                value = value.strip()
                if value.endswith('%'):
                    value = value[:-1].strip()
                try:
                    parsed = float(value)
                    if parsed > 1.0:
                        return parsed
                    else:
                        return parsed * 100.0
                except (ValueError, TypeError):
                    return 0.0
            return 0.0
        
        # Parse percent complete
        percent_complete_raw = _get_column_value(
            row,
            ["Percent_Complete", "Percent Complete", "percent_complete", "PercentComplete", "% Complete", "%_Complete"],
            0
        )
        percent_complete = _parse_percent_value(percent_complete_raw)
        
        # Get schedule analysis fields
        early_start = _get_string_column_value(row, ["ES", "Early_Start", "Early Start", "early_start"])
        early_finish = _get_string_column_value(row, ["EF", "Early_Finish", "Early Finish", "early_finish"])
        late_start = _get_string_column_value(row, ["LS", "Late_Start", "Late Start", "late_start"])
        late_finish = _get_string_column_value(row, ["LF", "Late_Finish", "Late Finish", "late_finish"])
        
        # Get required fields with flexible column name matching
        activity_id = _get_required_string_column_value(
            row,
            ["Activity_ID", "Activity ID", "activity_id", "ActivityID", "ID", "Id", "id"],
            "activity ID"
        )
        name = _get_required_string_column_value(
            row,
            ["Activity_Name", "Activity Name", "activity_name", "ActivityName", "Name", "name", "Task_Name", "Task Name"],
            "activity name"
        )
        
        # Get date/duration fields with flexible column name matching
        planned_start = _get_string_column_value(row, ["Planned_Start", "Planned Start", "planned_start", "PlannedStart"])
        planned_finish = _get_string_column_value(row, ["Planned_Finish", "Planned Finish", "planned_finish", "PlannedFinish"])
        planned_duration = _get_column_value(row, ["Planned_Duration", "Planned Duration", "planned_duration", "PlannedDuration"], None)
        if planned_duration is not None:
            planned_duration = _clean_value(planned_duration)
        
        # Baseline fields - try Baseline 1 first, then fallback to Baseline
        baseline_start = _get_string_column_value(row, [
            "Baseline 1 Start", "Baseline_1_Start", "Baseline_Start", "Baseline Start", 
            "baseline_start", "BaselineStart", "Baseline1Start"
        ])
        baseline_finish = _get_string_column_value(row, [
            "Baseline 1 Finish", "Baseline_1_Finish", "Baseline_Finish", "Baseline Finish",
            "baseline_finish", "BaselineFinish", "Baseline1Finish"
        ])
        baseline_duration = _get_column_value(row, [
            "Baseline 1 Duration", "Baseline_1_Duration", "Baseline_Duration", "Baseline Duration",
            "baseline_duration", "BaselineDuration", "Baseline1Duration"
        ], None)
        if baseline_duration is not None:
            baseline_duration = _clean_value(baseline_duration)
        
        actual_start = _get_string_column_value(row, ["Actual_Start", "Actual Start", "actual_start", "ActualStart"])
        actual_finish = _get_string_column_value(row, ["Actual_Finish", "Actual Finish", "actual_finish", "ActualFinish"])
        remaining_duration = _get_column_value(row, ["Remaining_Duration", "Remaining Duration", "remaining_duration", "RemainingDuration"], None)
        if remaining_duration is not None:
            remaining_duration = _clean_value(remaining_duration)
        
        # Total Float with flexible naming
        total_float_raw = _get_column_value(row, ["Total_Float", "Total Float", "total_float", "TotalFloat", "Float", "float"], 0.0)
        total_float = float(total_float_raw) if not pd.isna(total_float_raw) else 0.0
        
        # Risk fields with flexible naming
        risk_probability_raw = _get_column_value(row, [
            "Risk Impact Probability", "Risk_Impact_Probability", "Probability_%", "Probability %", 
            "probability", "Probability", "Risk_Probability", "Risk Probability"
        ], 0)
        # If value is > 1, assume it's already a percentage; if <= 1, assume it's 0-1 and convert
        if not pd.isna(risk_probability_raw):
            if risk_probability_raw > 1:
                risk_probability = risk_probability_raw / 100
            else:
                risk_probability = risk_probability_raw
        else:
            risk_probability = 0
        
        risk_delay_impact_days = _get_column_value(row, [
            "Risk Impact Delay", "Risk_Impact_Delay", "Delay_Impact_days", "Delay Impact days",
            "Delay_Impact", "Delay Impact", "delay_impact_days"
        ], 0)
        if pd.isna(risk_delay_impact_days):
            risk_delay_impact_days = 0
        
        cost_impact_of_risk = _get_column_value(row, [
            "Risk Cost Impact", "Risk_Cost_Impact", "Cost_Impact_of_Risk", "Cost Impact of Risk",
            "cost_impact_of_risk", "CostImpact"
        ], None)
        if cost_impact_of_risk is not None:
            cost_impact_of_risk = _clean_value(cost_impact_of_risk)
        
        # Cost fields for Forensic Intelligence (CPI Engine)
        planned_cost = _get_column_value(row, [
            "Planned_Cost", "Planned Cost", "planned_cost", "PlannedCost", "Budget"
        ], None)
        if planned_cost is not None:
            planned_cost = _clean_value(planned_cost)
        
        actual_cost_to_date = _get_column_value(row, [
            "Actual_Cost_To_Date", "Actual Cost To Date", "actual_cost_to_date", 
            "ActualCostToDate", "Actual Cost", "Actual_Cost"
        ], None)
        if actual_cost_to_date is not None:
            actual_cost_to_date = _clean_value(actual_cost_to_date)
        
        # Dependency fields - handle both "Predecessors" and "Predecessor_ID" formats
        predecessors_str = _get_string_column_value(row, [
            "Predecessors", "Predecessor_ID", "Predecessor ID", "predecessors", 
            "Predecessor", "predecessor_id"
        ]) or ""
        predecessors = [p.strip() for p in str(predecessors_str).split(";") if p.strip()]
        # Also try comma-separated
        if not predecessors:
            predecessors = [p.strip() for p in str(predecessors_str).split(",") if p.strip()]
        
        successors_str = _get_string_column_value(row, [
            "Successors", "Successor_ID", "Successor ID", "successors",
            "Successor", "successor_id"
        ]) or ""
        successors = [s.strip() for s in str(successors_str).split(";") if s.strip()]
        # Also try comma-separated
        if not successors:
            successors = [s.strip() for s in str(successors_str).split(",") if s.strip()]
        
        on_critical_path = _parse_bool_value(_get_column_value(row, [
            "On Critical Path", "On_Critical_Path", "on_critical_path", "OnCriticalPath",
            "Critical Path", "critical_path", "Is_Critical", "Is Critical"
        ], False))
        
        # Resource fields - handle "Resource 1" format
        resource_id = _get_string_column_value(row, [
            "Resource 1", "Resource_1", "Resource_ID", "Resource ID", "resource_id",
            "Resource", "resource", "ResourceID"
        ])
        role = _get_string_column_value(row, [
            "Resource 1 Role", "Resource_1_Role", "Role", "role", "ResourceRole",
            "Resource Role", "Resource_Role"
        ])
        fte_allocation = _get_column_value(row, [
            "Resource 1 FTE Allocation", "Resource_1_FTE_Allocation", "FTE_Allocation", 
            "FTE Allocation", "fte_allocation", "FTEAllocation", "FTE"
        ], 0.0)
        if pd.isna(fte_allocation):
            fte_allocation = 0.0
        
        resource_max_fte = _get_column_value(row, [
            "Resource_Max_FTE", "Resource Max FTE", "resource_max_fte", "MaxFTE",
            "Resource 1 Max FTE", "Resource_1_Max_FTE"
        ], 1.0)
        if pd.isna(resource_max_fte):
            resource_max_fte = 1.0
        
        skill_tags = _get_string_column_value(row, [
            "Resource_Skill_Tags", "Resource Skill Tags", "Skill_Tags", "Skill Tags",
            "skill_tags", "Skills", "skills"
        ])
        
        return Activity(
            activity_id=str(activity_id),
            name=str(name),
            planned_start=planned_start,
            planned_finish=planned_finish,
            baseline_start=baseline_start,
            baseline_finish=baseline_finish,
            planned_duration=planned_duration,
            baseline_duration=baseline_duration,
            actual_start=actual_start,
            actual_finish=actual_finish,
            remaining_duration=remaining_duration,
            percent_complete=percent_complete,
            early_start=early_start,
            early_finish=early_finish,
            late_start=late_start,
            late_finish=late_finish,
            total_float=total_float,
            risk_probability=risk_probability,
            risk_delay_impact_days=risk_delay_impact_days,
            cost_impact_of_risk=cost_impact_of_risk,
            planned_cost=planned_cost,
            actual_cost_to_date=actual_cost_to_date,
            predecessors=predecessors,
            successors=successors,
            on_critical_path=on_critical_path,
            resource_id=resource_id,
            role=role,
            fte_allocation=fte_allocation,
            resource_max_fte=resource_max_fte,
            skill_tags=skill_tags
        )

