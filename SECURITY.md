# Security Implementation Guide

## Overview

This document outlines the comprehensive security enhancements implemented in Phase 1 of the NBA Stats project. The security measures focus on input validation, data sanitization, rate limiting, admin access controls, and audit logging.

## Security Features Implemented

### 1. Data Sanitization Middleware

**Location**: `app/middleware/sanitization.py`

**Features**:
- **XSS Prevention**: HTML encoding and pattern detection for malicious scripts
- **SQL Injection Protection**: Detection and removal of SQL injection patterns
- **Input Sanitization**: Removal of null bytes, control characters, and dangerous characters
- **Request Size Limits**: Configurable limits for request body size, query parameters, and headers
- **JSON Data Sanitization**: Recursive sanitization of JSON payloads

**Configuration**:
```env
NBA_STATS_SECURITY_MAX_REQUEST_SIZE=10485760  # 10MB
NBA_STATS_SECURITY_MAX_QUERY_PARAMS=50
NBA_STATS_SECURITY_MAX_HEADER_SIZE=8192
NBA_STATS_SECURITY_MAX_STRING_LENGTH=500
```

### 2. Enhanced Rate Limiting

**Location**: `app/core/security.py`

**Features**:
- **General Rate Limiting**: Configurable requests per minute for all endpoints
- **Admin Rate Limiting**: Stricter limits for admin endpoints
- **IP-based Tracking**: Rate limits tracked per client IP
- **Rate Limit Headers**: X-RateLimit-* headers in responses
- **Graceful Degradation**: Clean error responses when limits exceeded

**Configuration**:
```env
NBA_STATS_API_RATE_LIMIT_REQUESTS=100
NBA_STATS_API_RATE_LIMIT_WINDOW=60
NBA_STATS_SECURITY_ADMIN_RATE_LIMIT_REQUESTS=10
NBA_STATS_SECURITY_ADMIN_RATE_LIMIT_WINDOW=60
```

### 3. Admin Access Controls

**Location**: `app/middleware/admin_security.py`

**Features**:
- **API Key Authentication**: Bearer token authentication for admin endpoints
- **Admin-specific Rate Limiting**: Lower limits for admin operations
- **Admin Action Audit Logging**: Comprehensive logging of all admin actions
- **Configurable Admin Access**: Can be enabled/disabled via configuration

**Configuration**:
```env
NBA_STATS_SECURITY_ADMIN_ENABLED=true
NBA_STATS_SECURITY_ADMIN_API_KEY=your-admin-api-key
NBA_STATS_SECURITY_ENABLE_ADMIN_AUDIT_LOGGING=true
```

### 4. Security Headers

**Location**: `app/core/security.py`

**Features**:
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-Frame-Options**: Prevents clickjacking attacks
- **X-XSS-Protection**: Browser XSS protection
- **Referrer-Policy**: Controls referrer information
- **Content-Security-Policy**: CSP for documentation pages

### 5. Input Validation Schemas

**Location**: `app/schemas/validation.py`

**Enhanced Pydantic Models**:
- **Comprehensive Field Validation**: Min/max values, string lengths, patterns
- **Data Type Enforcement**: Strict type checking for all inputs
- **Business Logic Validation**: NBA-specific validation rules
- **Sanitized Search Queries**: XSS and injection protection for search

## Usage Examples

### Admin Endpoint Access

```bash
# With API key
curl -H "Authorization: Bearer your-admin-api-key" \
     http://localhost:8000/api/admin/status

# Trigger data update
curl -X POST \
     -H "Authorization: Bearer your-admin-api-key" \
     http://localhost:8000/api/admin/update/all
```

### Rate Limit Headers

```bash
# Check rate limit status
curl -I http://localhost:8000/api/teams

# Response headers include:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 99
# X-RateLimit-Reset: 1640995200
```

### Input Validation

```bash
# Valid request
curl "http://localhost:8000/api/teams?conference=East&limit=10"

# Invalid request (will return 422)
curl "http://localhost:8000/api/teams?conference=Invalid&limit=10000"
```

## Security Testing

### Automated Security Tests

**Location**: `tests/test_security.py`

**Test Coverage**:
- XSS prevention in query parameters and JSON bodies
- SQL injection prevention
- Request size and parameter limits
- Admin authentication and authorization
- Rate limiting enforcement
- Input validation schema compliance
- Security header presence
- Error handling and response formats

### Running Security Tests

```bash
# Run all security tests
cd Application/backend
python -m pytest tests/test_security.py -v

# Run specific test categories
python -m pytest tests/test_security.py::TestInputValidation -v
python -m pytest tests/test_security.py::TestAdminSecurity -v
python -m pytest tests/test_security.py::TestRateLimiting -v
```

## Security Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NBA_STATS_SECURITY_ADMIN_ENABLED` | `true` | Enable/disable admin endpoints |
| `NBA_STATS_SECURITY_ADMIN_API_KEY` | `None` | API key for admin access |
| `NBA_STATS_SECURITY_MAX_REQUEST_SIZE` | `10485760` | Max request size (10MB) |
| `NBA_STATS_SECURITY_MAX_QUERY_PARAMS` | `50` | Max query parameters |
| `NBA_STATS_SECURITY_MAX_HEADER_SIZE` | `8192` | Max header size |
| `NBA_STATS_SECURITY_ENABLE_XSS_PROTECTION` | `true` | Enable XSS protection |
| `NBA_STATS_SECURITY_ENABLE_SQL_INJECTION_PROTECTION` | `true` | Enable SQL injection protection |
| `NBA_STATS_API_RATE_LIMIT_REQUESTS` | `100` | General rate limit |
| `NBA_STATS_API_RATE_LIMIT_WINDOW` | `60` | Rate limit window (seconds) |

### Production Security Checklist

- [ ] **Change Default API Keys**: Set strong, unique admin API keys
- [ ] **Enable HTTPS**: Use SSL/TLS in production
- [ ] **Configure CORS**: Restrict origins to known frontend domains
- [ ] **Set Strong Secret Keys**: Use cryptographically secure JWT secrets
- [ ] **Enable Rate Limiting**: Ensure rate limiting is active in production
- [ ] **Monitor Admin Actions**: Review admin audit logs regularly
- [ ] **Update Dependencies**: Keep all security-related packages updated
- [ ] **Database Security**: Ensure database files have proper permissions
- [ ] **Firewall Configuration**: Restrict database and admin endpoint access

## Audit Logging

### Admin Actions Logged

All admin actions are logged with the following information:
- Action performed
- Client IP address
- User agent
- Request path and method
- Timestamp
- Additional details (e.g., component being updated)

### Log Format

```json
{
  "action": "trigger_full_update",
  "ip": "127.0.0.1",
  "user_agent": "curl/7.68.0",
  "path": "/api/admin/update/all",
  "method": "POST",
  "details": null,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Incident Response

### Rate Limit Exceeded
- **Status Code**: 429
- **Response**: `{"error": "RATE_LIMIT_ERROR", "message": "Rate limit exceeded"}`
- **Action**: Client should implement exponential backoff

### Invalid Admin Access
- **Status Code**: 401/403
- **Response**: `{"detail": "Invalid or missing admin API key"}`
- **Action**: Verify API key configuration

### Malicious Input Detected
- **Status Code**: 400
- **Response**: Input is sanitized or rejected
- **Action**: Review input validation rules

### Request Too Large
- **Status Code**: 413
- **Response**: `{"error": "REQUEST_TOO_LARGE", "message": "Request body too large"}`
- **Action**: Reduce request size or increase limits if appropriate

## Future Security Enhancements

### Planned Improvements
1. **Redis Rate Limiting**: Replace in-memory rate limiting with Redis for scalability
2. **JWT Authentication**: Implement user authentication with JWT tokens
3. **OAuth Integration**: Add OAuth2 support for third-party authentication
4. **Advanced Monitoring**: Implement security event monitoring and alerting
5. **WAF Integration**: Add Web Application Firewall for additional protection
6. **Encryption at Rest**: Encrypt sensitive data in the database
7. **API Versioning Security**: Security considerations for API versioning

### Monitoring Recommendations
1. **Log Analysis**: Regular review of admin audit logs
2. **Rate Limit Monitoring**: Track rate limit violations
3. **Error Pattern Analysis**: Monitor for suspicious error patterns
4. **Performance Impact**: Monitor security middleware performance
5. **False Positive Review**: Regularly review input sanitization effectiveness
