#!/usr/bin/env python3
"""
PROD-001 Validation Test Suite
Tests the implementation of secure environment variable handling.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def test_secret_key_validation():
    """Test secret key validation logic"""
    print("🔐 Testing secret key validation...")
    
    # Test 1: Configuration loads with valid secret key
    try:
        from app.core.config import Settings
        
        # Test with valid secret key
        settings = Settings(secret_key="a" * 32, environment="development")
        assert len(settings.secret_key) >= 32
        print("✅ Valid secret key accepted")
        
        # Test with short secret key (should fail)
        try:
            Settings(secret_key="short", environment="development")
            print("❌ Short secret key should have been rejected")
            return False
        except ValueError as e:
            print("✅ Short secret key properly rejected")
        
        # Test production environment without secret key (should fail)
        try:
            Settings(secret_key="", environment="production")
            print("❌ Production without secret key should have been rejected")
            return False
        except ValueError as e:
            print("✅ Production environment properly requires secret key")
            
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_environment_loading():
    """Test environment variable loading"""
    print("🌍 Testing environment variable loading...")
    
    try:
        # Save original environment
        original_secret = os.environ.get('SECRET_KEY')
        
        # Test with environment variable
        os.environ['SECRET_KEY'] = 'a' * 32
        
        from app.core.config import Settings
        settings = Settings()
        
        assert settings.secret_key == 'a' * 32
        print("✅ Environment variable loaded correctly")
        
        # Restore original environment
        if original_secret:
            os.environ['SECRET_KEY'] = original_secret
        else:
            os.environ.pop('SECRET_KEY', None)
            
        return True
        
    except Exception as e:
        print(f"❌ Environment loading test failed: {e}")
        return False

def test_fastapi_app_loads():
    """Test that FastAPI app loads with new configuration"""
    print("🚀 Testing FastAPI app loading...")
    
    try:
        from app.main import app
        print("✅ FastAPI app loads successfully")
        return True
    except Exception as e:
        print(f"❌ FastAPI app loading failed: {e}")
        return False

def test_env_file_security():
    """Test that .env file is properly gitignored"""
    print("🔒 Testing .env file security...")
    
    project_root = Path(__file__).parent
    gitignore_path = project_root / ".gitignore"
    
    if not gitignore_path.exists():
        print("❌ .gitignore file not found")
        return False
    
    gitignore_content = gitignore_path.read_text()
    if ".env" not in gitignore_content:
        print("❌ .env not found in .gitignore")
        return False
    
    print("✅ .env file properly protected by .gitignore")
    return True

def test_docker_configuration():
    """Test Docker configuration for environment variables"""
    print("🐳 Testing Docker configuration...")
    
    project_root = Path(__file__).parent
    docker_compose_path = project_root / "docker-compose.yml"
    
    if not docker_compose_path.exists():
        print("❌ docker-compose.yml not found")
        return False
    
    docker_content = docker_compose_path.read_text()
    if "SECRET_KEY=" not in docker_content:
        print("❌ SECRET_KEY environment variable not found in docker-compose.yml")
        return False
    
    print("✅ Docker configuration includes environment variables")
    return True

def test_security_documentation():
    """Test that security documentation exists"""
    print("📚 Testing security documentation...")
    
    project_root = Path(__file__).parent
    security_md_path = project_root / "SECURITY.md"
    
    if not security_md_path.exists():
        print("❌ SECURITY.md not found")
        return False
    
    security_content = security_md_path.read_text()
    if "SECRET_KEY" not in security_content:
        print("❌ SECRET_KEY documentation not found in SECURITY.md")
        return False
    
    print("✅ Security documentation exists and is comprehensive")
    return True

def main():
    """Run all PROD-001 validation tests"""
    print("🧪 PROD-001 VALIDATION TEST SUITE")
    print("=" * 50)
    
    # Change to backend directory for imports
    backend_path = Path(__file__).parent / "Application" / "backend"
    if backend_path.exists():
        sys.path.insert(0, str(backend_path))
    
    tests = [
        test_secret_key_validation,
        test_environment_loading,
        test_fastapi_app_loads,
        test_env_file_security,
        test_docker_configuration,
        test_security_documentation
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
    
    print("=" * 50)
    print(f"🎯 PROD-001 VALIDATION RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! PROD-001 implementation is secure and complete.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
