# Security Configuration Guide

## Environment Variables and Secrets Management

### Secret Key Configuration

The application requires a secure `SECRET_KEY` environment variable for cryptographic operations.

#### For Development:
1. Copy `.env.example` to `.env` in the backend directory
2. Generate a secure secret key:
   ```bash
   python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
   ```
3. Add the generated key to your `.env` file

#### For Production:
1. **NEVER** use the default or development secret key in production
2. Generate a secure secret key using:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. Set the `SECRET_KEY` environment variable on your production server
4. Ensure the secret key is at least 32 characters long
5. Store the secret securely (use your cloud provider's secret management service)

### Docker Production Deployment:
1. Create a `.env.production` file with your production secrets
2. Use Docker secrets or your orchestration platform's secret management
3. Set environment variables in your docker-compose.production.yml:
   ```yaml
   environment:
     - SECRET_KEY=${SECRET_KEY}
     - ENVIRONMENT=production
   ```

### Security Best Practices:
- ✅ Never commit `.env` files with real secrets to version control
- ✅ Use different secret keys for different environments
- ✅ Rotate secret keys regularly
- ✅ Use your cloud provider's secret management service in production
- ✅ Monitor for leaked secrets in your codebase
- ❌ Never use default or example secret keys in production
- ❌ Never hardcode secrets in source code
- ❌ Never share secret keys in plain text

### Environment-Specific Configuration:

The application will:
- Generate a random key for development if none is provided (with warning)
- Require an explicit SECRET_KEY in production environments
- Validate that the secret key is at least 32 characters long
- Provide clear error messages for misconfiguration

### If You're Getting Secret Key Errors:
1. Make sure you have a `.env` file in the `Application/backend/` directory
2. Ensure your `SECRET_KEY` is set and at least 32 characters long
3. For production, verify `ENVIRONMENT=production` is set
4. Check that your environment variables are being loaded correctly
