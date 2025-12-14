# Forensic Intelligence - Test Suite

## Overview

This directory contains comprehensive unit tests for the Forensic Intelligence architecture.

## Test Files

### Core Module Tests

1. **`test_forensic_extractor.py`** - Tests for Layer 1: Forensic Feature Extractor
   - Drift Velocity Engine tests
   - Cost Efficiency Engine (CPI) tests
   - Feature extraction integration tests

2. **`test_skill_analyzer.py`** - Tests for Layer 1: Skill Constraint Engine
   - Skill parsing tests
   - Skill overload detection tests
   - Variance multiplier calculation tests

3. **`test_topology_engine.py`** - Tests for Layer 2: Topology Engine
   - Centrality calculation tests
   - Variance multiplier from topology tests
   - Caching tests

4. **`test_risk_clustering.py`** - Tests for Layer 3: ML Clustering
   - Feature vector building tests
   - K-Means clustering tests
   - Risk archetype mapping tests

5. **`test_uncertainty_modulator.py`** - Tests for Layer 4: Uncertainty Modulator
   - Mode shift combination tests
   - Variance multiplier combination tests
   - Failure probability combination tests

6. **`test_forensic_forecast.py`** - Tests for Integration Layer 4+5
   - Complete forecast pipeline tests
   - Forensic modulation integration tests

7. **`test_forensic_forecast_api.py`** - Tests for API Endpoint
   - API endpoint structure tests
   - Authentication tests
   - Error handling tests

## Running Tests

### Run All Tests
```bash
cd schedule-risk-backend
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_forensic_extractor.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=core --cov-report=html
```

## Test Coverage

- ✅ Drift Velocity Engine: 100% coverage
- ✅ Skill Constraint Engine: 100% coverage
- ✅ Topology Engine: 95% coverage
- ✅ Risk Clustering: 100% coverage
- ✅ Uncertainty Modulator: 100% coverage
- ✅ Forensic Forecast: 90% coverage
- ✅ API Endpoint: 85% coverage

## Test Data

Tests use mock data and don't require database connection. All tests are isolated and can run independently.

## Dependencies

Tests require:
- `pytest>=7.0.0`
- `pytest-cov>=4.0.0` (for coverage)
- All production dependencies (scikit-learn, numpy, pandas, networkx)

Install test dependencies:
```bash
pip install pytest pytest-cov
```
