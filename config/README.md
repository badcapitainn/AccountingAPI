# Django Accounting API

A comprehensive Django-based accounting system API that provides full-featured financial management capabilities including Chart of Accounts, transaction processing, journal entries, and financial reporting.

## Features

### Core Accounting Features
- **Chart of Accounts Management**: Complete account hierarchy with types, categories, and individual accounts
- **Transaction Processing**: Full double-entry bookkeeping with journal entries and items
- **Financial Reporting**: Balance Sheet, Income Statement, Trial Balance, and General Ledger
- **Audit Trail**: Comprehensive logging of all system activities
- **Multi-tenant Support**: Built-in support for multiple organizations

### API Features
- **RESTful API**: Complete REST API with proper HTTP methods and status codes
- **JWT Authentication**: Secure token-based authentication
- **Comprehensive Documentation**: Auto-generated API documentation with Swagger/OpenAPI
- **Filtering & Search**: Advanced filtering, searching, and ordering capabilities
- **Pagination**: Built-in pagination for large datasets

### Technical Features
- **Django REST Framework**: Modern, flexible API framework
- **PostgreSQL Support**: Production-ready database support
- **Background Tasks**: Celery integration for async operations
- **CORS Support**: Cross-origin resource sharing enabled
- **Comprehensive Testing**: Unit and integration tests

## Project Structure

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
│   └── utils.py             # Utility functions
└── config/                  # Django configuration
    ├── settings.py          # Django settings
    └── urls.py              # Main URL configuration
```

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis (for Celery)

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
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=accounting_db
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
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

## API Endpoints

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

## Usage Examples

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

## Testing

Run the test suite:
```bash
python manage.py test
```

Run with coverage:
```bash
coverage run --source='.' manage.py test
coverage report
```

## Development

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

## Deployment

### Production Settings
Update `settings.py` for production:
- Set `DEBUG = False`
- Configure proper database settings
- Set up static file serving
- Configure logging
- Set up SSL/TLS

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Ensure code style compliance
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs/`
- Review the test files for usage examples 