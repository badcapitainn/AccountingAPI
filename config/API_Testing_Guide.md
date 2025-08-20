# Accounting API Testing Guide with Postman

## Overview
This guide provides comprehensive testing instructions for the Accounting API using Postman, including sample data, expected responses, and testing workflows.

## Prerequisites
1. **Postman** installed on your machine
2. **Django server** running on `http://localhost:8000`
3. **Database** with sample data (or create test data as you go)

## Setup Instructions

### 1. Import Postman Collection
1. Open Postman
2. Click "Import" button
3. Select the `AccountingAPI_Postman_Collection.json` file
4. The collection will be imported with all endpoints organized by category

### 2. Configure Environment Variables
The collection uses these variables:
- `base_url`: `http://localhost:8000/api/v1`
- `access_token`: JWT access token (auto-populated after authentication)
- `refresh_token`: JWT refresh token (auto-populated after authentication)

## Authentication Flow

### Step 1: Get JWT Token
**Endpoint:** `POST /auth/token/`

**Sample Request:**
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**Expected Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Testing Steps:**
1. Send the request
2. Copy the `access` token value
3. Set it in the collection variable `{{access_token}}`
4. All subsequent requests will automatically include the Authorization header

## Complete Testing Workflow

### Phase 1: Setup Chart of Accounts

#### 1. Create Account Types
**Endpoint:** `POST /account-types/`

**Sample Data:**
```json
{
    "name": "Asset",
    "code": "ASSET",
    "description": "Assets are economic resources owned by the business",
    "normal_balance": "DEBIT"
}
```

**Expected Response:**
```json
{
    "id": "uuid-here",
    "name": "Asset",
    "code": "ASSET",
    "description": "Assets are economic resources owned by the business",
    "normal_balance": "DEBIT",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

**Additional Account Types to Create:**
```json
[
    {
        "name": "Liability",
        "code": "LIABILITY",
        "description": "Liabilities are obligations of the business",
        "normal_balance": "CREDIT"
    },
    {
        "name": "Equity",
        "code": "EQUITY",
        "description": "Owner's equity in the business",
        "normal_balance": "CREDIT"
    },
    {
        "name": "Revenue",
        "code": "REVENUE",
        "description": "Revenue accounts track income from business operations",
        "normal_balance": "CREDIT"
    },
    {
        "name": "Expense",
        "code": "EXPENSE",
        "description": "Expense accounts track business costs",
        "normal_balance": "DEBIT"
    }
]
```

#### 2. Create Account Categories
**Endpoint:** `POST /account-categories/`

**Sample Data:**
```json
{
    "name": "Current Assets",
    "code": "CURRENT_ASSETS",
    "description": "Assets expected to be converted to cash within one year",
    "account_type": "{{asset_account_type_id}}",
    "sort_order": 1
}
```

**Additional Categories to Create:**
```json
[
    {
        "name": "Fixed Assets",
        "code": "FIXED_ASSETS",
        "description": "Long-term assets like buildings and equipment",
        "account_type": "{{asset_account_type_id}}",
        "sort_order": 2
    },
    {
        "name": "Current Liabilities",
        "code": "CURRENT_LIABILITIES",
        "description": "Obligations due within one year",
        "account_type": "{{liability_account_type_id}}",
        "sort_order": 1
    },
    {
        "name": "Long-term Liabilities",
        "code": "LONG_TERM_LIABILITIES",
        "description": "Obligations due beyond one year",
        "account_type": "{{liability_account_type_id}}",
        "sort_order": 2
    },
    {
        "name": "Operating Revenue",
        "code": "OPERATING_REVENUE",
        "description": "Revenue from primary business operations",
        "account_type": "{{revenue_account_type_id}}",
        "sort_order": 1
    },
    {
        "name": "Operating Expenses",
        "code": "OPERATING_EXPENSES",
        "description": "Expenses from primary business operations",
        "account_type": "{{expense_account_type_id}}",
        "sort_order": 1
    }
]
```

#### 3. Create Individual Accounts
**Endpoint:** `POST /accounts/`

**Sample Data:**
```json
{
    "account_number": "1000",
    "name": "Cash",
    "description": "Main cash account",
    "account_type": "{{asset_account_type_id}}",
    "category": "{{current_assets_category_id}}",
    "balance_type": "DEBIT",
    "is_bank_account": false,
    "is_cash_account": true,
    "is_reconcilable": true,
    "sort_order": 1
}
```

**Additional Accounts to Create:**
```json
[
    {
        "account_number": "1100",
        "name": "Accounts Receivable",
        "description": "Amounts owed by customers",
        "account_type": "{{asset_account_type_id}}",
        "category": "{{current_assets_category_id}}",
        "balance_type": "DEBIT",
        "is_bank_account": false,
        "is_cash_account": false,
        "is_reconcilable": true,
        "sort_order": 2
    },
    {
        "account_number": "1500",
        "name": "Equipment",
        "description": "Office equipment and machinery",
        "account_type": "{{asset_account_type_id}}",
        "category": "{{fixed_assets_category_id}}",
        "balance_type": "DEBIT",
        "is_bank_account": false,
        "is_cash_account": false,
        "is_reconcilable": false,
        "sort_order": 3
    },
    {
        "account_number": "2000",
        "name": "Accounts Payable",
        "description": "Amounts owed to suppliers",
        "account_type": "{{liability_account_type_id}}",
        "category": "{{current_liabilities_category_id}}",
        "balance_type": "CREDIT",
        "is_bank_account": false,
        "is_cash_account": false,
        "is_reconcilable": true,
        "sort_order": 1
    },
    {
        "account_number": "3000",
        "name": "Owner's Equity",
        "description": "Owner's investment in the business",
        "account_type": "{{equity_account_type_id}}",
        "category": "{{equity_category_id}}",
        "balance_type": "CREDIT",
        "is_bank_account": false,
        "is_cash_account": false,
        "is_reconcilable": false,
        "sort_order": 1
    },
    {
        "account_number": "4000",
        "name": "Sales Revenue",
        "description": "Revenue from product sales",
        "account_type": "{{revenue_account_type_id}}",
        "category": "{{operating_revenue_category_id}}",
        "balance_type": "CREDIT",
        "is_bank_account": false,
        "is_cash_account": false,
        "is_reconcilable": false,
        "sort_order": 1
    },
    {
        "account_number": "5000",
        "name": "Cost of Goods Sold",
        "description": "Direct costs of producing goods",
        "account_type": "{{expense_account_type_id}}",
        "category": "{{operating_expenses_category_id}}",
        "balance_type": "DEBIT",
        "is_bank_account": false,
        "is_cash_account": false,
        "is_reconcilable": false,
        "sort_order": 1
    }
]
```

### Phase 2: Setup Transaction Types

#### 1. Create Transaction Types
**Endpoint:** `POST /transaction-types/`

**Sample Data:**
```json
{
    "name": "Sale",
    "code": "SALE",
    "description": "Sales transactions"
}
```

**Additional Transaction Types:**
```json
[
    {
        "name": "Purchase",
        "code": "PURCHASE",
        "description": "Purchase transactions"
    },
    {
        "name": "Payment",
        "code": "PAYMENT",
        "description": "Payment transactions"
    },
    {
        "name": "Receipt",
        "code": "RECEIPT",
        "description": "Receipt transactions"
    },
    {
        "name": "Adjustment",
        "code": "ADJUSTMENT",
        "description": "Account adjustments"
    }
]
```

### Phase 3: Create and Post Transactions

#### 1. Create Initial Balance Transaction
**Endpoint:** `POST /transactions/`

**Sample Data:**
```json
{
    "transaction_number": "TXN-001",
    "reference_number": "INIT-001",
    "description": "Initial capital investment",
    "transaction_date": "2024-01-01",
    "amount": 50000.00,
    "transaction_type": "{{adjustment_transaction_type_id}}",
    "status": "PENDING",
    "is_posted": false
}
```

**Expected Response:**
```json
{
    "id": "uuid-here",
    "transaction_number": "TXN-001",
    "reference_number": "INIT-001",
    "description": "Initial capital investment",
    "transaction_date": "2024-01-01",
    "amount": "50000.00",
    "transaction_type": "uuid-here",
    "status": "PENDING",
    "is_posted": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 2. Create Journal Entries
**Endpoint:** `POST /journal-entries/`

**Sample Data (Debit Cash, Credit Owner's Equity):**
```json
{
    "transaction": "{{transaction_id}}",
    "description": "Debit cash, credit owner's equity",
    "amount": 50000.00,
    "sort_order": 1
}
```

#### 3. Post Transaction
**Endpoint:** `POST /transactions/{{transaction_id}}/post_transaction/`

**Expected Response:**
```json
{
    "message": "Transaction posted successfully.",
    "transaction_number": "TXN-001",
    "posted_date": "2024-01-01T00:00:00Z"
}
```

### Phase 4: Create Sample Business Transactions

#### 1. Sales Transaction
**Create Transaction:**
```json
{
    "transaction_number": "TXN-002",
    "reference_number": "SALE-001",
    "description": "Cash sale of products",
    "transaction_date": "2024-01-15",
    "amount": 2500.00,
    "transaction_type": "{{sale_transaction_type_id}}",
    "status": "PENDING",
    "is_posted": false
}
```

**Create Journal Entries:**
```json
[
    {
        "transaction": "{{transaction_id}}",
        "description": "Debit cash",
        "amount": 2500.00,
        "sort_order": 1
    },
    {
        "transaction": "{{transaction_id}}",
        "description": "Credit sales revenue",
        "amount": 2500.00,
        "sort_order": 2
    }
]
```

#### 2. Purchase Transaction
**Create Transaction:**
```json
{
    "transaction_number": "TXN-003",
    "reference_number": "PURCH-001",
    "description": "Purchase of inventory on credit",
    "transaction_date": "2024-01-20",
    "amount": 1500.00,
    "transaction_type": "{{purchase_transaction_type_id}}",
    "status": "PENDING",
    "is_posted": false
}
```

**Create Journal Entries:**
```json
[
    {
        "transaction": "{{transaction_id}}",
        "description": "Debit inventory",
        "amount": 1500.00,
        "sort_order": 1
    },
    {
        "transaction": "{{transaction_id}}",
        "description": "Credit accounts payable",
        "amount": 1500.00,
        "sort_order": 2
    }
]
```

### Phase 5: Generate Reports

#### 1. Create Report Template
**Endpoint:** `POST /report-templates/`

**Sample Data:**
```json
{
    "name": "Monthly Balance Sheet",
    "description": "Standard monthly balance sheet template",
    "report_type": "BALANCE_SHEET",
    "template_data": {
        "sections": ["assets", "liabilities", "equity"]
    },
    "sort_order": 1
}
```

#### 2. Create Report
**Endpoint:** `POST /reports/`

**Sample Data:**
```json
{
    "name": "January 2024 Balance Sheet",
    "description": "Balance sheet as of January 31, 2024",
    "template": "{{balance_sheet_template_id}}",
    "parameters": {
        "as_of_date": "2024-01-31"
    },
    "filters": {},
    "format": "PDF"
}
```

#### 3. Generate Report
**Endpoint:** `POST /reports/{{report_id}}/generate/`

**Expected Response:**
```json
{
    "message": "Report generated successfully.",
    "report_number": "RPT-001",
    "status": "COMPLETED"
}
```

## Testing Scenarios

### Scenario 1: Complete Accounting Cycle
1. Create chart of accounts
2. Record initial investment
3. Record sales transactions
4. Record expenses
5. Generate financial reports
6. Verify account balances

### Scenario 2: Error Handling
1. Try to create duplicate account numbers
2. Try to post invalid transactions
3. Try to access unauthorized endpoints
4. Test with expired tokens

### Scenario 3: Data Validation
1. Test required field validation
2. Test data type validation
3. Test business rule validation
4. Test constraint validation

## Expected Response Formats

### Success Responses
- **200 OK**: Resource retrieved successfully
- **201 Created**: Resource created successfully
- **204 No Content**: Operation completed successfully

### Error Responses
- **400 Bad Request**: Invalid data or business rule violation
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Common Error Response Format
```json
{
    "error": "Error message description",
    "detail": "Additional error details if available"
}
```

## Testing Tips

1. **Start with Authentication**: Always get a valid token first
2. **Use Variables**: Store IDs from created resources in collection variables
3. **Test in Order**: Follow the workflow phases for logical testing
4. **Verify Responses**: Check that created resources match your input
5. **Test Edge Cases**: Try invalid data, missing fields, and boundary conditions
6. **Monitor Logs**: Check Django server logs for any errors
7. **Use Filters**: Test query parameters and filtering functionality
8. **Test Pagination**: For endpoints that return lists, test pagination

## Troubleshooting

### Common Issues
1. **Authentication Errors**: Check token validity and expiration
2. **Permission Errors**: Verify user has required permissions
3. **Validation Errors**: Check required fields and data formats
4. **Database Errors**: Ensure database is running and accessible
5. **Server Errors**: Check Django server logs for detailed error information

### Debug Steps
1. Verify server is running on correct port
2. Check database connection
3. Validate request format and headers
4. Review server logs for detailed error messages
5. Test with simpler requests first

## Sample Data Summary

### Account Types (5)
- Asset, Liability, Equity, Revenue, Expense

### Account Categories (6)
- Current Assets, Fixed Assets, Current Liabilities, Long-term Liabilities, Operating Revenue, Operating Expenses

### Individual Accounts (7)
- Cash, Accounts Receivable, Equipment, Accounts Payable, Owner's Equity, Sales Revenue, Cost of Goods Sold

### Transaction Types (5)
- Sale, Purchase, Payment, Receipt, Adjustment

### Sample Transactions (3)
- Initial investment, Sales transaction, Purchase transaction

This comprehensive testing approach will validate all major functionality of your Accounting API and ensure it works correctly in real-world scenarios.
