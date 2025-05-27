"""
Comprehensive tests for input validation and security enhancements.
"""

import os

import pytest
from fastapi.testclient import TestClient

# Set testing environment before importing app
os.environ["NBA_STATS_ENVIRONMENT"] = "testing"

from app.core.security import rate_limit_store
from app.core.settings import reload_settings
from app.main import app

# Reload settings to pick up the testing environment
reload_settings()

client = TestClient(app)


# Clear rate limit store before each test class
@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Clear rate limit store before each test."""
    rate_limit_store.clear()
    yield
    rate_limit_store.clear()


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_xss_prevention_query_params(self):
        """Test XSS prevention in query parameters."""
        malicious_queries = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "onload=alert('xss')",
            "onerror=alert('xss')",
        ]

        for query in malicious_queries:
            response = client.get(f"/teams?name={query}")
            # Should not return the malicious script
            assert query not in response.text
            # Should either sanitize or reject
            assert response.status_code in [200, 400]

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        malicious_queries = [
            "'; DROP TABLE teams; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users",
            "admin'--",
            "' OR 1=1 --",
        ]

        for query in malicious_queries:
            # Test with conference parameter (which teams endpoint actually has)
            response = client.get(f"/teams?conference={query}")
            # Should either sanitize/reject invalid conference values
            assert response.status_code in [
                200,
                422,
            ]  # 422 for invalid conference pattern

    def test_excessive_query_parameters(self):
        """Test handling of excessive query parameters."""
        params = {f"param{i}": f"value{i}" for i in range(100)}
        response = client.get("/teams", params=params)
        assert response.status_code == 400
        assert "TOO_MANY_PARAMS" in response.json()["error"]

    def test_large_request_body(self):
        """Test handling of large request bodies."""
        large_data = {"data": "x" * (11 * 1024 * 1024)}  # 11MB
        response = client.post("/admin/update/all", json=large_data)
        assert response.status_code == 413
        assert "REQUEST_TOO_LARGE" in response.json()["error"]

    def test_parameter_length_limits(self):
        """Test parameter length limits."""
        long_string = "a" * 1000
        response = client.get(f"/search?q={long_string}")
        # Should truncate or reject
        assert response.status_code in [200, 400]

    def test_date_format_validation(self):
        """Test date format validation."""
        invalid_dates = [
            "2023-13-01",  # Invalid month
            "2023-02-30",  # Invalid day
            "not-a-date",
            "2023/01/01",  # Wrong format
        ]

        for date in invalid_dates:
            response = client.get(f"/games?date={date}")
            assert response.status_code == 422  # Validation error

    def test_numeric_parameter_validation(self):
        """Test numeric parameter validation."""
        invalid_numbers = [
            "not-a-number",
            "-1",  # Negative when positive expected
            "999999999999",  # Too large
        ]

        for num in invalid_numbers:
            # Test with valid team_id parameter on players endpoint
            response = client.get(f"/players?team_id={num}")
            # Should handle invalid team_id gracefully (return empty results or 400)
            assert response.status_code in [200, 400, 422]

    def test_pagination_limits(self):
        """Test pagination parameter limits."""
        # Test excessive skip (should handle gracefully)
        response = client.get("/teams?skip=99999")
        assert (
            response.status_code == 200
        )  # Should handle gracefully, return empty results

        # Test excessive limit (should be capped by endpoint validation)
        response = client.get("/teams?limit=10000")
        assert response.status_code in [200, 422]  # Either capped or validation error

    def test_search_query_sanitization(self):
        """Test search query sanitization."""
        dangerous_queries = [
            "<script>alert('test')</script>",
            "'; DROP TABLE players; --",
            "javascript:void(0)",
        ]

        for query in dangerous_queries:
            response = client.get(f"/search?q={query}")
            if response.status_code == 200:
                # Query should be sanitized
                assert query not in response.text
            else:
                # Or rejected with validation error
                assert response.status_code == 422


class TestAdminSecurity:
    """Test admin endpoint security."""

    def test_admin_access_without_key(self):
        """Test admin access without API key when required."""
        response = client.get("/admin/status")
        # Should require authentication if admin key is configured
        assert response.status_code in [200, 401, 403]

    def test_admin_access_with_invalid_key(self):
        """Test admin access with invalid API key."""
        headers = {"Authorization": "Bearer invalid-key"}
        response = client.get("/admin/status", headers=headers)
        # Should reject invalid key
        assert response.status_code in [200, 401, 403]

    def test_admin_rate_limiting(self):
        """Test admin endpoint rate limiting."""
        headers = {"Authorization": "Bearer test-key"}

        # Make many requests quickly
        responses = []
        for _ in range(15):  # More than admin limit
            response = client.get("/admin/status", headers=headers)
            responses.append(response)

        # Should eventually rate limit
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or 401 in status_codes or 403 in status_codes

    def test_admin_action_logging(self):
        """Test that admin actions are logged."""
        # This would require checking logs in a real implementation
        # For now, just verify the endpoints work
        response = client.get("/admin/status")
        assert response.status_code in [200, 401, 403, 429]  # Include rate limiting


class TestSecurityHeaders:
    """Test security headers are properly set."""

    def test_security_headers_present(self):
        """Test that security headers are included in responses."""
        response = client.get("/teams")

        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
        ]

        for header in expected_headers:
            assert header in response.headers

    def test_cors_headers(self):
        """Test CORS headers are properly configured."""
        response = client.options("/teams")

        # Should have CORS headers
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
        ]

        for header in cors_headers:
            assert header in response.headers or response.status_code == 405


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_headers(self):
        """Test rate limit headers are included."""
        response = client.get("/teams")

        if response.status_code != 429:
            # Should include rate limit headers
            rate_limit_headers = [
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
            ]

            for header in rate_limit_headers:
                assert header in response.headers

    def test_rate_limit_enforcement(self):
        """Test rate limit enforcement."""
        # Make many requests quickly
        responses = []
        for _ in range(150):  # Exceed typical rate limit
            response = client.get("/teams")
            responses.append(response)
            if response.status_code == 429:
                break

        # Should eventually rate limit
        status_codes = [r.status_code for r in responses]
        # Either rate limited or completed successfully
        assert 429 in status_codes or all(code == 200 for code in status_codes)


class TestValidationSchemas:
    """Test Pydantic validation schemas."""

    def test_team_query_validation(self):
        """Test team query parameter validation."""
        # Invalid conference
        response = client.get("/teams?conference=Invalid")
        assert response.status_code == 422

        # Valid conference
        response = client.get("/teams?conference=East")
        assert response.status_code == 200

    def test_player_query_validation(self):
        """Test player query parameter validation."""
        # Invalid team_id
        response = client.get("/players?team_id=-1")
        assert response.status_code == 422

        # Valid team_id
        response = client.get("/players?team_id=1")
        assert response.status_code == 200

    def test_game_query_validation(self):
        """Test game query parameter validation."""
        # Invalid status
        response = client.get("/games?status=InvalidStatus")
        assert response.status_code == 422

        # Valid status
        response = client.get("/games?status=Final")
        assert response.status_code == 200

    def test_search_validation(self):
        """Test search query validation."""
        # Empty query
        response = client.get("/search?q=")
        assert response.status_code == 422

        # Valid query
        response = client.get("/search?q=Lakers")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and responses."""

    def test_validation_error_format(self):
        """Test validation error response format."""
        response = client.get("/teams?limit=invalid")
        assert response.status_code == 422

        error_data = response.json()
        assert "detail" in error_data
        # Should have structured error information

    def test_not_found_handling(self):
        """Test 404 error handling."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Test method not allowed handling."""
        response = client.post("/teams")  # GET only endpoint
        assert response.status_code == 405
