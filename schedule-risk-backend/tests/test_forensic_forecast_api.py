"""
Integration tests for Forensic Forecast API endpoint
Tests: API endpoint integration, response format, error handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app

client = TestClient(app)


class TestForensicForecastAPI:
    """Tests for /api/projects/{project_id}/forecast/forensic endpoint"""
    
    @pytest.fixture
    def mock_auth(self):
        """Mock authentication"""
        with patch('api.forecast.get_current_user') as mock_user:
            mock_user.return_value = Mock(id=1, email="test@example.com")
            yield mock_user
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        with patch('api.forecast.get_db') as mock_db:
            yield mock_db
    
    @pytest.fixture
    def mock_activities(self):
        """Mock activities data"""
        from core.models import Activity
        return [
            Activity(
                activity_id="A-001",
                name="Task 1",
                remaining_duration=5.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=[],
                successors=["A-002"]
            ),
            Activity(
                activity_id="A-002",
                name="Task 2",
                remaining_duration=3.0,
                percent_complete=0.0,
                risk_probability=0.0,
                risk_delay_impact_days=0.0,
                predecessors=["A-001"],
                successors=[]
            )
        ]
    
    def test_forensic_forecast_endpoint_structure(self, mock_auth, mock_db, mock_activities):
        """Test that endpoint returns correct structure"""
        with patch('api.forecast.verify_project_ownership'):
            with patch('api.forecast.get_activities', return_value=mock_activities):
                with patch('api.forecast.get_reference_date_for_project', return_value=None):
                    with patch('api.forecast.compute_forensic_forecast') as mock_forecast:
                        mock_forecast.return_value = {
                            "p50": 10,
                            "p80": 12,
                            "p90": 14,
                            "p95": 16,
                            "forensic_modulation_applied": True
                        }
                        
                        response = client.get(
                            "/api/projects/test-project/forecast/forensic",
                            headers={"Authorization": "Bearer test-token"}
                        )
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert "p50" in data
                        assert "p80" in data
                        assert "p90" in data
                        assert "p95" in data
                        assert data["forensic_modulation_applied"] == True
                        assert "forensic_insights" in data
    
    def test_forensic_forecast_insights(self, mock_auth, mock_db, mock_activities):
        """Test that forensic insights are included"""
        with patch('api.forecast.verify_project_ownership'):
            with patch('api.forecast.get_activities', return_value=mock_activities):
                with patch('api.forecast.get_reference_date_for_project', return_value=None):
                    with patch('api.forecast.compute_forensic_forecast') as mock_forecast:
                        mock_forecast.return_value = {
                            "p50": 10,
                            "p80": 12,
                            "p90": 14,
                            "p95": 16,
                            "forensic_modulation_applied": True
                        }
                        
                        response = client.get(
                            "/api/projects/test-project/forecast/forensic",
                            headers={"Authorization": "Bearer test-token"}
                        )
                        
                        assert response.status_code == 200
                        data = response.json()
                        insights = data["forensic_insights"]
                        assert "drift_activities" in insights
                        assert "skill_bottlenecks" in insights
                        assert "high_risk_clusters" in insights
                        assert "bridge_nodes" in insights
    
    def test_forensic_forecast_authentication_required(self):
        """Test that endpoint requires authentication"""
        response = client.get("/api/projects/test-project/forecast/forensic")
        
        # Should return 401 or 403 (authentication required)
        assert response.status_code in [401, 403]
    
    def test_forensic_forecast_project_not_found(self, mock_auth, mock_db):
        """Test error handling for non-existent project"""
        with patch('api.forecast.verify_project_ownership'):
            with patch('api.forecast.get_activities', return_value=[]):
                response = client.get(
                    "/api/projects/non-existent/forecast/forensic",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 404
    
    def test_forensic_forecast_force_recompute(self, mock_auth, mock_db, mock_activities):
        """Test force_recompute parameter"""
        with patch('api.forecast.verify_project_ownership'):
            with patch('api.forecast.get_activities', return_value=mock_activities):
                with patch('api.forecast.get_reference_date_for_project', return_value=None):
                    with patch('api.forecast.get_forecast_cache', return_value=None):
                        with patch('api.forecast.compute_forensic_forecast') as mock_forecast:
                            mock_forecast.return_value = {
                                "p50": 10,
                                "p80": 12,
                                "p90": 14,
                                "p95": 16,
                                "forensic_modulation_applied": True
                            }
                            
                            response = client.get(
                                "/api/projects/test-project/forecast/forensic?force_recompute=true",
                                headers={"Authorization": "Bearer test-token"}
                            )
                            
                            assert response.status_code == 200
                            # Should call compute_forensic_forecast (not use cache)
                            assert mock_forecast.called
    
    def test_forensic_forecast_num_simulations(self, mock_auth, mock_db, mock_activities):
        """Test num_simulations parameter"""
        with patch('api.forecast.verify_project_ownership'):
            with patch('api.forecast.get_activities', return_value=mock_activities):
                with patch('api.forecast.get_reference_date_for_project', return_value=None):
                    with patch('api.forecast.compute_forensic_forecast') as mock_forecast:
                        mock_forecast.return_value = {
                            "p50": 10,
                            "p80": 12,
                            "p90": 14,
                            "p95": 16,
                            "forensic_modulation_applied": True
                        }
                        
                        response = client.get(
                            "/api/projects/test-project/forecast/forensic?num_simulations=5000",
                            headers={"Authorization": "Bearer test-token"}
                        )
                        
                        assert response.status_code == 200
                        # Should pass num_simulations to compute_forensic_forecast
                        call_args = mock_forecast.call_args
                        assert call_args[1]["num_simulations"] == 5000
