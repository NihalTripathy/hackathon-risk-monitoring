"""
Manual test runner for Forensic Intelligence tests
Run this if pytest is not available
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_module(module_name, test_classes):
    """Run tests from a module manually"""
    print(f"\n{'='*60}")
    print(f"Testing: {module_name}")
    print(f"{'='*60}")
    
    try:
        module = __import__(f"tests.{module_name}", fromlist=[test_classes])
        passed = 0
        failed = 0
        
        for test_class_name in test_classes:
            test_class = getattr(module, test_class_name)
            test_methods = [m for m in dir(test_class) if m.startswith('test_')]
            
            print(f"\n  {test_class_name}:")
            for test_method in test_methods:
                try:
                    test_instance = test_class()
                    test_method_func = getattr(test_instance, test_method)
                    test_method_func()
                    print(f"    ✅ {test_method}")
                    passed += 1
                except Exception as e:
                    print(f"    ❌ {test_method}: {str(e)[:100]}")
                    failed += 1
        
        print(f"\n  Summary: {passed} passed, {failed} failed")
        return passed, failed
        
    except Exception as e:
        print(f"  ❌ Error loading module: {e}")
        return 0, 1


if __name__ == "__main__":
    print("Forensic Intelligence - Manual Test Runner")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    
    # Test modules
    test_modules = [
        ("test_forensic_extractor", ["TestDriftVelocityEngine", "TestCostEfficiencyEngine", "TestForensicExtractor"]),
        ("test_skill_analyzer", ["TestSkillParsing", "TestSkillOverloadDetection", "TestActivitySkillRisk"]),
        ("test_topology_engine", ["TestTopologyMetrics"]),
        ("test_risk_clustering", ["TestFeatureVectorBuilder", "TestClustering", "TestRiskArchetypes"]),
        ("test_uncertainty_modulator", ["TestUncertaintyModulation"]),
        ("test_forensic_forecast", ["TestForensicForecast"]),
    ]
    
    for module_name, test_classes in test_modules:
        passed, failed = run_test_module(module_name, test_classes)
        total_passed += passed
        total_failed += failed
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")
    print(f"{'='*60}")
    
    if total_failed == 0:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
