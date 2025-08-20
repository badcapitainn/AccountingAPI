# Accounting API - Quick Reference

## Base URL
`http://localhost:8000/api/v1`

## Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/token/` | Get JWT access token |
| `POST` | `/auth/token/refresh/` | Refresh access token |
| `POST` | `/auth/token/verify/` | Verify token validity |

## Account Types
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/account-types/` | List all account types |
| `POST` | `/account-types/` | Create new account type |
| `GET` | `/account-types/{id}/` | Get account type details |
| `PUT` | `/account-types/{id}/` | Update account type |
| `DELETE` | `/account-types/{id}/` | Delete account type |
| `GET` | `/account-types/{id}/accounts/` | Get accounts by type |

## Account Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/account-categories/` | List all account categories |
| `POST` | `/account-categories/` | Create new account category |
| `GET` | `/account-categories/{id}/` | Get category details |
| `PUT` | `/account-categories/{id}/` | Update category |
| `DELETE` | `/account-categories/{id}/` | Delete category |
| `GET` | `/account-categories/{id}/accounts/` | Get accounts in category |
| `GET` | `/account-categories/{id}/subcategories/` | Get subcategories |

## Accounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/accounts/` | List all accounts |
| `POST` | `/accounts/` | Create new account |
| `GET` | `/accounts/{id}/` | Get account details |
| `PUT` | `/accounts/{id}/` | Update account |
| `DELETE` | `/accounts/{id}/` | Delete account |
| `GET` | `/accounts/{id}/balance/` | Get account balance |
| `GET` | `/accounts/{id}/transactions/` | Get account transactions |
| `POST` | `/accounts/{id}/update_balance/` | Update account balance |
| `GET` | `/accounts/chart_of_accounts/` | Get complete chart of accounts |
| `GET` | `/accounts/balance_sheet_accounts/` | Get balance sheet accounts |
| `GET` | `/accounts/income_statement_accounts/` | Get income statement accounts |
| `GET` | `/accounts/bank_accounts/` | Get bank accounts |
| `GET` | `/accounts/cash_accounts/` | Get cash accounts |
| `GET` | `/accounts/reconcilable_accounts/` | Get reconcilable accounts |

## Transaction Types
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/transaction-types/` | List all transaction types |
| `POST` | `/transaction-types/` | Create new transaction type |
| `GET` | `/transaction-types/{id}/` | Get transaction type details |
| `PUT` | `/transaction-types/{id}/` | Update transaction type |
| `DELETE` | `/transaction-types/{id}/` | Delete transaction type |
| `GET` | `/transaction-types/{id}/transactions/` | Get transactions by type |

## Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/transactions/` | List all transactions |
| `POST` | `/transactions/` | Create new transaction |
| `GET` | `/transactions/{id}/` | Get transaction details |
| `PUT` | `/transactions/{id}/` | Update transaction |
| `DELETE` | `/transactions/{id}/` | Delete transaction |
| `POST` | `/transactions/{id}/post_transaction/` | Post transaction to ledger |
| `POST` | `/transactions/{id}/void_transaction/` | Void posted transaction |
| `GET` | `/transactions/{id}/summary/` | Get transaction summary |
| `GET` | `/transactions/{id}/journal_entries/` | Get journal entries |
| `GET` | `/transactions/recent_transactions/` | Get recent transactions |
| `GET` | `/transactions/pending_transactions/` | Get pending transactions |
| `GET` | `/transactions/large_transactions/` | Get large transactions |

## Journal Entries
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/journal-entries/` | List all journal entries |
| `POST` | `/journal-entries/` | Create new journal entry |
| `GET` | `/journal-entries/{id}/` | Get journal entry details |
| `PUT` | `/journal-entries/{id}/` | Update journal entry |
| `DELETE` | `/journal-entries/{id}/` | Delete journal entry |
| `GET` | `/journal-entries/{id}/items/` | Get journal items |
| `GET` | `/journal-entries/{id}/summary/` | Get journal entry summary |

## Report Templates
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/report-templates/` | List all report templates |
| `POST` | `/report-templates/` | Create new report template |
| `GET` | `/report-templates/{id}/` | Get template details |
| `PUT` | `/report-templates/{id}/` | Update template |
| `DELETE` | `/report-templates/{id}/` | Delete template |
| `GET` | `/report-templates/{id}/reports/` | Get reports by template |

## Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/reports/` | List all reports |
| `POST` | `/reports/` | Create new report |
| `GET` | `/reports/{id}/` | Get report details |
| `PUT` | `/reports/{id}/` | Update report |
| `DELETE` | `/reports/{id}/` | Delete report |
| `POST` | `/reports/{id}/generate/` | Generate report |
| `GET` | `/reports/{id}/download/` | Download report |
| `POST` | `/reports/{id}/cancel/` | Cancel report generation |
| `GET` | `/reports/completed_reports/` | Get completed reports |
| `GET` | `/reports/pending_reports/` | Get pending reports |
| `GET` | `/reports/failed_reports/` | Get failed reports |
| `GET` | `/reports/downloadable_reports/` | Get downloadable reports |

## Report Schedules
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/report-schedules/` | List all report schedules |
| `POST` | `/report-schedules/` | Create new schedule |
| `GET` | `/report-schedules/{id}/` | Get schedule details |
| `PUT` | `/report-schedules/{id}/` | Update schedule |
| `DELETE` | `/report-schedules/{id}/` | Delete schedule |
| `POST` | `/report-schedules/{id}/activate/` | Activate schedule |
| `POST` | `/report-schedules/{id}/deactivate/` | Deactivate schedule |
| `POST` | `/report-schedules/{id}/run_now/` | Run schedule immediately |
| `GET` | `/report-schedules/active_schedules/` | Get active schedules |
| `GET` | `/report-schedules/due_schedules/` | Get due schedules |

## System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/` | Get system dashboard |
| `GET` | `/system/health/` | Check system health |

## Cache Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/cache/` | List cache information |
| `POST` | `/cache/clear/` | Clear all cache |
| `POST` | `/cache/clear/{key}/` | Clear specific cache |

## Query Parameters

### Common Filters
- `is_active`: Filter by active status (true/false)
- `start_date`: Filter by start date (YYYY-MM-DD)
- `end_date`: Filter by end date (YYYY-MM-DD)
- `status`: Filter by status
- `format`: Filter by format

### Search
- `search`: Search in name, description, or code fields

### Ordering
- `ordering`: Sort by specific fields (e.g., `-created_at` for descending)

### Pagination
- `page`: Page number
- `page_size`: Items per page

## Response Formats

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

## Authentication Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Rate Limiting
- Default: 1000 requests per hour per user
- Burst: 100 requests per minute per user

## API Versioning
- Current version: v1
- Version included in URL path: `/api/v1/`
- Backward compatibility maintained within major versions
