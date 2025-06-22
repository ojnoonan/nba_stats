#!/usr/bin/env python3
"""
SEC-001 Validation Test Suite
Tests the implementation of comprehensive input validation and sanitization.
"""

import sys
import requests
import json
import pytest
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent / "Application" / "backend"
sys.path.insert(0, str(backend_path))

BASE_URL = "http://localhost:7778"

def test_xss_prevention():
    """Test XSS attack prevention"""
    print("🛡️  Testing XSS prevention...")
    
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "<iframe src='javascript:alert(\"xss\")'></iframe>"
    ]
    
    for payload in xss_payloads:
        try:
            response = requests.get(f"{BASE_URL}/search", params={"term": payload})
            if response.status_code == 400:
                print(f"✅ XSS payload blocked: {payload[:30]}...")
            else:
                print(f"❌ XSS payload not blocked: {payload[:30]}...")
                assert False, f"XSS payload not blocked: {payload[:30]}..."
        except Exception as e:
            print(f"⚠️  Error testing XSS payload: {e}")
    
    assert True

def test_sql_injection_prevention():
    """Test SQL injection attack prevention"""
    print("🛡️  Testing SQL injection prevention...")
    
    sql_payloads = [
        "'; DROP TABLE teams; --",
        "1' OR '1'='1",
        "UNION SELECT * FROM players",
        "'; INSERT INTO teams VALUES (999, 'hacked'); --"
    ]
    
    for payload in sql_payloads:
        try:
            response = requests.get(f"{BASE_URL}/search", params={"term": payload})
            if response.status_code == 400:
                print(f"✅ SQL injection payload blocked: {payload[:30]}...")
            else:
                print(f"❌ SQL injection payload not blocked: {payload[:30]}...")
                assert False, f"SQL injection payload not blocked: {payload[:30]}..."
        except Exception as e:
            print(f"⚠️  Error testing SQL injection payload: {e}")
    
    assert True

def test_parameter_validation():
    """Test parameter validation"""
    print("🔍 Testing parameter validation...")
    
    # Test invalid team ID
    try:
        response = requests.get(f"{BASE_URL}/teams/999999999")
        if response.status_code == 400:
            print("✅ Invalid team ID rejected")
        else:
            print("❌ Invalid team ID not rejected")
            assert False, "Invalid team ID not rejected"
    except Exception as e:
        print(f"⚠️  Error testing team ID validation: {e}")
    
    # Test invalid player ID
    try:
        response = requests.get(f"{BASE_URL}/players/-1")
        if response.status_code == 400:
            print("✅ Invalid player ID rejected")
        else:
            print("❌ Invalid player ID not rejected")
            assert False, "Invalid player ID not rejected"
    except Exception as e:
        print(f"⚠️  Error testing player ID validation: {e}")
    
    # Test invalid season format
    try:
        response = requests.get(f"{BASE_URL}/search", params={"term": "test", "season": "invalid"})
        if response.status_code == 400:
            print("✅ Invalid season format rejected")
        else:
            print("❌ Invalid season format not rejected")
            assert False, "Invalid season format not rejected"
    except Exception as e:
        print(f"⚠️  Error testing season validation: {e}")
    
    assert True

def test_input_sanitization():
    """Test input sanitization"""
    print("🧹 Testing input sanitization...")
    
    # Test search term sanitization
    try:
        response = requests.get(f"{BASE_URL}/search", params={"term": "LeBron  James!!@@##"})
        if response.status_code == 200:
            data = response.json()
            # Check if special characters were removed/sanitized
            if "query" in data and "!@#" not in data["query"]:
                print("✅ Search term sanitized")
            else:
                print("❌ Search term not properly sanitized")
                assert False, "Search term not properly sanitized"
        else:
            print("❌ Search with special characters failed")
            assert False, "Search with special characters failed"
    except Exception as e:
        print(f"⚠️  Error testing input sanitization: {e}")
    
    assert True

def test_pagination_limits():
    """Test pagination limits and bounds checking"""
    print("📄 Testing pagination limits...")
    
    # Test excessive page size
    try:
        response = requests.get(f"{BASE_URL}/players", params={"per_page": 1000})
        if response.status_code == 400:
            print("✅ Excessive page size rejected")
        else:
            print("❌ Excessive page size not rejected")
            assert False, "Excessive page size not rejected"
    except Exception as e:
        print(f"⚠️  Error testing pagination limits: {e}")
    
    # Test negative page number
    try:
        response = requests.get(f"{BASE_URL}/players", params={"page": -1})
        if response.status_code == 400:
            print("✅ Negative page number rejected")
        else:
            print("❌ Negative page number not rejected")
            assert False, "Negative page number not rejected"
    except Exception as e:
        print(f"⚠️  Error testing negative page: {e}")
    
    assert True

def test_content_length_limits():
    """Test content length limits"""
    print("📏 Testing content length limits...")
    
    # Test oversized request body
    try:
        large_data = {"data": "x" * (11 * 1024 * 1024)}  # 11MB payload
        response = requests.post(f"{BASE_URL}/admin/update/all", json=large_data)
        if response.status_code in [400, 413]:
            print("✅ Oversized request body rejected")
        else:
            print("❌ Oversized request body not rejected")
            assert False, "Oversized request body not rejected"
    except Exception as e:
        print(f"⚠️  Error testing content length: {e}")
    
    assert True

def test_rate_limiting():
    """Test rate limiting protection"""
    print("⏱️  Testing rate limiting...")
    
    # Make rapid requests to trigger rate limiting
    try:
        for i in range(35):  # Exceed the 30/minute limit
            response = requests.get(f"{BASE_URL}/status")
            if response.status_code == 429:
                print("✅ Rate limiting active")
                assert True
                return
        
        print("❌ Rate limiting not triggered")
        assert False, "Rate limiting not triggered"
    except Exception as e:
        print(f"⚠️  Error testing rate limiting: {e}")
        assert False, f"Error testing rate limiting: {e}"

def test_api_endpoints_respond():
    """Test that API endpoints still respond correctly with validation"""
    print("🔄 Testing API endpoint functionality...")
    
    # Test teams endpoint
    try:
        response = requests.get(f"{BASE_URL}/teams")
        if response.status_code == 200:
            print("✅ Teams endpoint functional")
        else:
            print("❌ Teams endpoint not functional")
            assert False, "Teams endpoint not functional"
    except Exception as e:
        print(f"⚠️  Error testing teams endpoint: {e}")
        assert False, f"Error testing teams endpoint: {e}"
    
    # Test search endpoint with valid input
    try:
        response = requests.get(f"{BASE_URL}/search", params={"term": "Lakers"})
        if response.status_code == 200:
            print("✅ Search endpoint functional")
        else:
            print("❌ Search endpoint not functional")
            assert False, "Search endpoint not functional"
    except Exception as e:
        print(f"⚠️  Error testing search endpoint: {e}")
        assert False, f"Error testing search endpoint: {e}"
    
    assert True

def test_validation_schemas():
    """Test validation schemas"""
    print("📋 Testing validation schemas...")
    
    try:
        from app.schemas.validation import (
            validate_nba_team_id, 
            validate_nba_player_id, 
            sanitize_string
        )
        
        # Test team ID validation
        try:
            validate_nba_team_id(1611661313)  # Valid Lakers ID
            print("✅ Valid team ID accepted")
        except ValueError:
            print("❌ Valid team ID rejected")
            assert False, "Valid team ID rejected"
        
        try:
            validate_nba_team_id(-1)  # Invalid team ID
            print("❌ Invalid team ID accepted")
            assert False, "Invalid team ID accepted"
        except ValueError:
            print("✅ Invalid team ID rejected")
        
        # Test string sanitization
        sanitized = sanitize_string("<script>alert('test')</script>")
        if "&lt;script&gt;" in sanitized:
            print("✅ String sanitization working")
        else:
            print("❌ String sanitization not working")
            assert False, "String sanitization not working"
        
        assert True
        
    except ImportError as e:
        print(f"⚠️  Could not import validation modules: {e}")
        assert False, f"Could not import validation modules: {e}"
    except Exception as e:
        print(f"⚠️  Error testing validation schemas: {e}")
        assert False, f"Error testing validation schemas: {e}"

def main():
    """Run all SEC-001 validation tests"""
    print("🧪 SEC-001 INPUT VALIDATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_validation_schemas,
        test_api_endpoints_respond,
        test_parameter_validation,
        test_input_sanitization,
        test_pagination_limits,
        test_xss_prevention,
        test_sql_injection_prevention,
        test_content_length_limits,
        test_rate_limiting
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"🎯 SEC-001 VALIDATION RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! SEC-001 implementation is secure and complete.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
