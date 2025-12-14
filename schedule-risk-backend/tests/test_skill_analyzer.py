"""
Unit tests for Skill Constraint Engine (Layer 1)
Tests: Skill parsing, bottleneck detection, variance calculation
"""

import pytest
from datetime import date
from core.skill_analyzer import (
    parse_skill_tags,
    check_skill_overload,
    get_activity_skill_risk
)
from core.models import Activity


class TestSkillParsing:
    """Tests for skill tag parsing"""
    
    def test_parse_semicolon_separated(self):
        """Test parsing semicolon-separated skills"""
        skills = parse_skill_tags("python;sql;react")
        
        assert len(skills) == 3
        assert "python" in skills
        assert "sql" in skills
        assert "react" in skills
    
    def test_parse_comma_separated(self):
        """Test parsing comma-separated skills"""
        skills = parse_skill_tags("python,sql,react")
        
        assert len(skills) == 3
        assert "python" in skills
        assert "sql" in skills
        assert "react" in skills
    
    def test_parse_single_skill(self):
        """Test parsing single skill"""
        skills = parse_skill_tags("python")
        
        assert len(skills) == 1
        assert "python" in skills
    
    def test_parse_empty_string(self):
        """Test parsing empty string"""
        skills = parse_skill_tags("")
        
        assert len(skills) == 0
    
    def test_parse_none(self):
        """Test parsing None"""
        skills = parse_skill_tags(None)
        
        assert len(skills) == 0
    
    def test_parse_with_whitespace(self):
        """Test parsing with whitespace"""
        skills = parse_skill_tags(" python ; sql ; react ")
        
        assert len(skills) == 3
        assert "python" in skills
        assert "sql" in skills
        assert "react" in skills
    
    def test_parse_case_insensitive(self):
        """Test that skills are lowercased"""
        skills = parse_skill_tags("Python;SQL;React")
        
        assert "python" in skills
        assert "sql" in skills
        assert "react" in skills


class TestSkillOverloadDetection:
    """Tests for skill overload detection"""
    
    def test_no_overload_single_resource(self):
        """Test when resource has capacity"""
        activities = [
            Activity(
                activity_id="A-001",
                name="Task 1",
                resource_id="R001",
                skill_tags="python",
                fte_allocation=0.5,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            ),
            Activity(
                activity_id="A-002",
                name="Task 2",
                resource_id="R001",
                skill_tags="python",
                fte_allocation=0.3,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            )
        ]
        
        result = check_skill_overload(activities)
        
        assert len(result["skill_bottlenecks"]) == 0
        assert len(result["activity_skill_risks"]) == 0
    
    def test_overload_single_skill(self):
        """Test when single skill is overbooked"""
        activities = [
            Activity(
                activity_id="A-001",
                name="Task 1",
                resource_id="R001",
                skill_tags="python",
                fte_allocation=0.6,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            ),
            Activity(
                activity_id="A-002",
                name="Task 2",
                resource_id="R001",
                skill_tags="python",
                fte_allocation=0.7,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            )
        ]
        
        result = check_skill_overload(activities)
        
        assert len(result["skill_bottlenecks"]) > 0
        bottleneck = result["skill_bottlenecks"][0]
        assert bottleneck["skill"] == "python"
        assert bottleneck["resource_id"] == "R001"
        assert bottleneck["overload_pct"] > 100.0
        assert "A-001" in result["activity_skill_risks"]
        assert "A-002" in result["activity_skill_risks"]
    
    def test_overload_multiple_skills(self):
        """Test when resource has multiple skill requirements"""
        activities = [
            Activity(
                activity_id="A-001",
                name="Task 1",
                resource_id="R001",
                skill_tags="python;sql",
                fte_allocation=0.5,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            ),
            Activity(
                activity_id="A-002",
                name="Task 2",
                resource_id="R001",
                skill_tags="python",
                fte_allocation=0.6,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            )
        ]
        
        result = check_skill_overload(activities)
        
        # Python should be overloaded (0.5 + 0.6 = 1.1 > 1.0)
        python_bottleneck = [b for b in result["skill_bottlenecks"] if b["skill"] == "python"]
        assert len(python_bottleneck) > 0
    
    def test_variance_multiplier_calculation(self):
        """Test variance multiplier calculation"""
        activities = [
            Activity(
                activity_id="A-001",
                name="Task 1",
                resource_id="R001",
                skill_tags="python;sql;react",
                fte_allocation=0.4,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            ),
            Activity(
                activity_id="A-002",
                name="Task 2",
                resource_id="R001",
                skill_tags="python",
                fte_allocation=0.7,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            )
        ]
        
        result = check_skill_overload(activities)
        
        # A-001 has 3 skills, A-002 has 1 skill
        # Both should have variance multipliers
        assert "A-001" in result["variance_increase_map"]
        assert "A-002" in result["variance_increase_map"]
        # A-001 should have higher multiplier (more skills)
        assert result["variance_increase_map"]["A-001"] >= result["variance_increase_map"]["A-002"]
    
    def test_no_skill_tags(self):
        """Test activities without skill tags"""
        activities = [
            Activity(
                activity_id="A-001",
                name="Task 1",
                resource_id="R001",
                skill_tags=None,
                fte_allocation=0.5,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            )
        ]
        
        result = check_skill_overload(activities)
        
        assert len(result["skill_bottlenecks"]) == 0
    
    def test_no_resource_id(self):
        """Test activities without resource ID"""
        activities = [
            Activity(
                activity_id="A-001",
                name="Task 1",
                resource_id=None,
                skill_tags="python",
                fte_allocation=0.5,
                resource_max_fte=1.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                planned_start="2026-01-01",
                planned_finish="2026-01-05"
            )
        ]
        
        result = check_skill_overload(activities)
        
        assert len(result["skill_bottlenecks"]) == 0


class TestActivitySkillRisk:
    """Tests for activity skill risk checking"""
    
    def test_get_activity_skill_risk_true(self):
        """Test when activity has skill risk"""
        skill_analysis = {
            "activity_skill_risks": {
                "A-001": ["python", "sql"]
            }
        }
        
        assert get_activity_skill_risk("A-001", skill_analysis) == True
        assert get_activity_skill_risk("A-002", skill_analysis) == False
    
    def test_get_activity_skill_risk_false(self):
        """Test when activity has no skill risk"""
        skill_analysis = {
            "activity_skill_risks": {}
        }
        
        assert get_activity_skill_risk("A-001", skill_analysis) == False
    
    def test_get_activity_skill_risk_empty_analysis(self):
        """Test with empty skill analysis"""
        skill_analysis = {}
        
        assert get_activity_skill_risk("A-001", skill_analysis) == False
