# Django Accounting API

A comprehensive Django-based accounting system API that provides full-featured financial management capabilities including Chart of Accounts, transaction processing, journal entries, and financial reporting. Built with enterprise-grade security and performance optimizations.

## 🚀 Features

### Core Accounting Features
- **Chart of Accounts Management**: Complete account hierarchy with types, categories, and individual accounts
- **Transaction Processing**: Full double-entry bookkeeping with journal entries and items
- **Financial Reporting**: Balance Sheet, Income Statement, Trial Balance, and General Ledger
- **Audit Trail**: Comprehensive logging of all system activities
- **Multi-tenant Support**: Built-in support for multiple organizations

### 🔒 Security Features
- **Enhanced JWT Authentication**: Secure token-based authentication with IP tracking and device fingerprinting
- **Rate Limiting**: API rate limiting with burst and sustained protection
- **Input Validation**: Comprehensive input sanitization and SQL injection protection
- **Security Headers**: XSS protection, CSRF protection, and Content Security Policy
- **Account Lockout**: Automatic account lockout after failed login attempts
- **Audit Logging**: Complete audit trail for compliance and security monitoring
- **Role-Based Access Control**: Granular permissions with custom permission classes

### API Features
- **RESTful API**: Complete REST API with proper HTTP methods and status codes
- **JWT Authentication**: Secure token-based authentication with enhanced security
- **Comprehensive Documentation**: Auto-generated API documentation with Swagger/OpenAPI
- **Filtering & Search**: Advanced filtering, searching, and ordering capabilities
- **Pagination**: Built-in pagination for large datasets
- **Rate Limiting**: Configurable API rate limiting per user and endpoint

### Technical Features
- **Django REST Framework**: Modern, flexible API framework
- **PostgreSQL Support**: Production-ready database support with SSL connections
- **Redis Integration**: Advanced caching, session storage, and rate limiting
- **Background Tasks**: Celery integration for async operations
- **CORS Support**: Cross-origin resource sharing with security controls
- **Comprehensive Testing**: Unit and integration tests
- **Performance Optimization**: Multi-level caching strategy

## 🏗️ Project Structure

```
config/
├── accounting/                 # Core accounting functionality
│   ├── models/                # Database models
│   │   ├── accounts.py       # Account-related models
│   │   ├── transactions.py   # Transaction models
│   │   └── reports.py        # Report models
│   ├── services/             # Business logic services
│   │   ├── transaction_service.py
│   │   └── report_generator.py
│   ├── managers.py           # Custom model managers
│   └── signals.py            # Django signals
├── api/                      # API layer
│   ├── views/               # API views
│   │   ├── accounts.py      # Account endpoints
│   │   ├── transactions.py  # Transaction endpoints
│   │   └── reports.py       # Report endpoints
│   └── serializers/         # API serializers
│       ├── accounts.py
│       ├── transactions.py
│       └── reports.py
├── core/                     # Core system functionality
│   ├── models.py            # Core models (audit, config, etc.)
│   ├── views.py             # Core views
│   ├── permissions.py       # Custom permissions
│   ├── serializers.py       # Custom JWT serializers
│   ├── logging.py           # Security logging utilities
│   └── middleware.py        # Security and audit middleware
└── config/                  # Django configuration
    ├── settings.py          # Django settings with security config
    └── urls.py              # Main URL configuration
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+ (for caching, sessions, and rate limiting)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AccountingAPI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the `config` directory:
   ```env
   # Django Settings
   SECRET_KEY=your-super-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Database Configuration
   POSTGRES_DB=accounting_db
   POSTGRES_USER=your_db_user
   POSTGRES_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   
   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   REDIS_PASSWORD=your_redis_password
   
   # Celery Configuration
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   
   # Security Settings (for development)
   SECURE_SSL_REDIRECT=False
   SESSION_COOKIE_SECURE=False
   CSRF_COOKIE_SECURE=False
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## 🔒 Security Configuration

### Production Security Checklist
- [ ] Set `DEBUG=False`
- [ ] Change default `SECRET_KEY`
- [ ] Enable HTTPS (`SECURE_SSL_REDIRECT=True`)
- [ ] Set secure cookie flags
- [ ] Configure CORS properly
- [ ] Enable security headers
- [ ] Set up rate limiting
- [ ] Configure audit logging

### Security Features
- **JWT Token Security**: 15-minute access tokens, 2-hour refresh tokens
- **Rate Limiting**: 60 requests/minute burst, 1000 requests/hour sustained
- **Account Protection**: 5 failed login attempts trigger account lockout
- **Input Validation**: Automatic SQL injection and XSS protection
- **Security Headers**: Comprehensive security headers for all responses
- **Audit Logging**: Complete audit trail for compliance

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/token/` - Obtain JWT token
- `POST /api/v1/auth/token/refresh/` - Refresh JWT token
- `POST /api/v1/auth/token/verify/` - Verify JWT token

### Accounts
- `GET /api/v1/accounts/` - List accounts
- `POST /api/v1/accounts/` - Create account
- `GET /api/v1/accounts/{id}/` - Get account details
- `PUT /api/v1/accounts/{id}/` - Update account
- `DELETE /api/v1/accounts/{id}/` - Delete account
- `GET /api/v1/accounts/{id}/balance/` - Get account balance
- `GET /api/v1/accounts/{id}/transactions/` - Get account transactions

### Transactions
- `GET /api/v1/transactions/` - List transactions
- `POST /api/v1/transactions/` - Create transaction
- `GET /api/v1/transactions/{id}/` - Get transaction details
- `POST /api/v1/transactions/{id}/post_transaction/` - Post transaction
- `POST /api/v1/transactions/{id}/void_transaction/` - Void transaction

### Reports
- `GET /api/v1/reports/` - List reports
- `POST /api/v1/reports/` - Create report
- `GET /api/v1/reports/{id}/` - Get report details
- `POST /api/v1/reports/{id}/generate/` - Generate report
- `GET /api/v1/reports/{id}/download/` - Download report

### Documentation
- `GET /api/schema/` - API schema
- `GET /api/docs/` - Swagger UI documentation
- `GET /api/redoc/` - ReDoc documentation

## 🚀 Performance & Caching

### Redis Configuration
The system uses Redis for multiple purposes:
- **Session Storage**: Secure session management
- **API Caching**: Response caching for improved performance
- **Rate Limiting**: Request rate limiting storage
- **Report Caching**: Financial report data caching
- **Transaction Caching**: Transaction summary caching

### Cache Strategies
- **Account Balances**: Cached for 10 minutes
- **Report Data**: Cached for 30 minutes
- **User Permissions**: Cached for 1 hour
- **API Responses**: Configurable TTL per endpoint

## 📝 Usage Examples

### Creating an Account
```python
import requests

# Authenticate
response = requests.post('http://localhost:8000/api/v1/auth/token/', {
    'username': 'admin',
    'password': 'password'
})
token = response.json()['access']

headers = {'Authorization': f'Bearer {token}'}

# Create account
account_data = {
    'account_number': '1000',
    'name': 'Cash',
    'account_type_id': 'uuid-of-asset-type',
    'category_id': 'uuid-of-current-assets',
    'balance_type': 'DEBIT',
    'opening_balance': 10000.00
}

response = requests.post('http://localhost:8000/api/v1/accounts/', 
                        json=account_data, headers=headers)
```

### Creating a Transaction
```python
transaction_data = {
    'description': 'Purchase of office supplies',
    'transaction_date': '2024-01-15',
    'transaction_type_id': 'uuid-of-expense-type',
    'amount': 500.00,
    'journal_entries': [
        {
            'description': 'Office supplies expense',
            'amount': 500.00,
            'items': [
                {
                    'account_id': 'uuid-of-expense-account',
                    'debit_amount': 500.00,
                    'credit_amount': 0.00
                },
                {
                    'account_id': 'uuid-of-cash-account',
                    'debit_amount': 0.00,
                    'credit_amount': 500.00
                }
            ]
        }
    ]
}

response = requests.post('http://localhost:8000/api/v1/transactions/', 
                        json=transaction_data, headers=headers)
```

## 🧪 Testing

### Run Test Suite
```bash
python manage.py test
```

### Run with Coverage
```bash
coverage run --source='.' manage.py test
coverage report
```

### Security Testing
The project includes comprehensive security testing:
- Authentication and authorization tests
- Input validation tests
- Rate limiting tests
- Security header validation
- JWT token security tests

## 🚀 Development

### Code Style
The project uses:
- **Black** for code formatting
- **Flake8** for linting
- **isort** for import sorting

Format code:
```bash
black .
isort .
```

### Adding New Features
1. Create models in appropriate `models.py` files
2. Add serializers in `api/serializers/`
3. Create views in `api/views/`
4. Add URL patterns
5. Write tests
6. Update documentation

### Security Development
When adding new features:
1. Implement proper permission classes
2. Add input validation
3. Include audit logging
4. Test security measures
5. Update security documentation

## 🚀 Deployment

### Production Settings
Update `settings.py` for production:
- Set `DEBUG = False`
- Configure proper database settings with SSL
- Set up Redis with authentication
- Configure secure logging
- Set up SSL/TLS
- Enable security headers
- Configure rate limiting

### Environment Variables
Critical production environment variables:
```env
DEBUG=False
SECRET_KEY=your-super-secret-production-key
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
REDIS_PASSWORD=your_redis_password
POSTGRES_PASSWORD=your_db_password
```

### Docker Deployment
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: accounting_db
      POSTGRES_USER: accounting_user
      POSTGRES_PASSWORD: accounting_password
  
  redis:
    image: redis:6-alpine
    command: redis-server --requirepass your_redis_password
```

## 📚 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (including security tests)
5. Ensure code style compliance
6. Update security documentation if needed
7. Submit a pull request

### Security Contributions
When contributing security-related features:
- Follow OWASP guidelines
- Include comprehensive testing
- Document security implications
- Review with security team

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs/`
- Review the test files for usage examples
- Check security documentation for configuration help

## 🔒 Security Contact

For security-related issues:
- **Security Team**: security@yourdomain.com
- **Emergency Contact**: +1-XXX-XXX-XXXX
- **Escalation Path**: Team Lead → Manager → CTO

---

**⚠️ Important**: This is a financial application handling sensitive data. Always follow security best practices and regularly update security measures. 
