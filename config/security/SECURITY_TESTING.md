# 🔒 Security Testing Guide

This guide explains how to run security tests for the Accounting API and troubleshoot common issues.

## 🚀 Quick Start

### 1. Simple Security Check (Recommended First Step)

Run the simple security check that doesn't require full Django setup:

```bash
cd config
python simple_security_check.py
```

This will check:
- Environment variables
- Basic security settings
- File permissions
- Required dependencies

### 2. Full Security Test (Requires Django Setup)

If the simple check passes, run the comprehensive security test:

```bash
cd config
python security_test.py
```

## 🛠️ Prerequisites

### Environment Setup

1. **Create a `.env` file** in the `config` directory:
   ```bash
   cp env_example.txt .env
   ```

2. **Update the `.env` file** with your actual values:
   ```bash
   # Database Configuration
   POSTGRES_DB=your_database_name
   POSTGRES_USER=your_username
   POSTGRES_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   
   # Security Settings
   DEBUG=False
   SECRET_KEY=your-super-secret-key-here
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup

1. **PostgreSQL** must be running and accessible
2. **Database** must exist and be accessible with the credentials in `.env`
3. **User** must have appropriate permissions

## 🔍 Troubleshooting

### Common Issues

#### 1. "Apps aren't loaded yet" Error

**Problem**: Django can't load apps during logging configuration
**Solution**: The logging configuration has been simplified to avoid this issue

#### 2. Missing Environment Variables

**Problem**: Required database environment variables are not set
**Solution**: 
```bash
# Check if .env file exists
ls -la config/.env

# Create .env file if missing
cp config/env_example.txt config/.env

# Edit .env file with your values
nano config/.env
```

#### 3. Database Connection Issues

**Problem**: Can't connect to PostgreSQL
**Solution**:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U your_username -d your_database
```

#### 4. Permission Issues

**Problem**: Can't write to logs directory or access files
**Solution**:
```bash
# Create logs directory
mkdir -p config/logs

# Set proper permissions
chmod 755 config/logs
chmod 600 config/.env
```

### Running Tests Step by Step

1. **Start with simple check**:
   ```bash
   python simple_security_check.py
   ```

2. **Fix any issues** found in the simple check

3. **Run full security test**:
   ```bash
   python security_test.py
   ```

4. **Review results** and address any failures

## 📊 Understanding Test Results

### Test Categories

- **✅ PASSED**: Security measures working correctly
- **❌ FAILED**: Critical security issues that must be fixed
- **⚠️ WARNINGS**: Security concerns that should be addressed
- **💡 RECOMMENDATIONS**: Suggestions for improvement

### Security Score

The test calculates a security score based on passed vs. failed tests:
- **80%+**: Excellent security posture
- **60-79%**: Good security posture with room for improvement
- **<60%**: Security improvements needed

## 🔧 Manual Testing

### Security Headers Check

Test if security headers are properly set:

```bash
# Start Django server
python manage.py runserver

# In another terminal, check headers
curl -I http://localhost:8000/api/
```

Look for these security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy`

### Rate Limiting Test

Test API rate limiting:

```bash
# Make multiple rapid requests
for i in {1..70}; do
  curl -s http://localhost:8000/api/ > /dev/null
  echo "Request $i"
done
```

You should see rate limiting kick in around request 60.

## 🚨 Production Security Checklist

Before running security tests in production:

- [ ] `DEBUG=False`
- [ ] Custom `SECRET_KEY` set
- [ ] HTTPS enabled
- [ ] Database SSL connections
- [ ] Secure cookie settings
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security middleware active

## 📞 Getting Help

If you encounter issues:

1. **Check the error message** carefully
2. **Verify environment setup** using simple security check
3. **Review Django logs** for additional details
4. **Check database connectivity**
5. **Verify file permissions**

## 🔗 Additional Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [Security Testing Best Practices](https://restfulapi.net/security-essentials/)

---

**Remember**: Security testing is an ongoing process. Run these tests regularly and after any significant changes to your application.
