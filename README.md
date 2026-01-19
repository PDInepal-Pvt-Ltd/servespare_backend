# ServeIQ Backend System Report
**Generated:** January 19, 2026  
**Version:** 1.0.0  
**Framework:** Django 6.0 + Django REST Framework 3.16

---

## 1. Executive Summary

ServeIQ is a **multi-tenant SaaS backend system** designed for business management operations. It provides comprehensive APIs for user authentication, subscription management, inventory/stock management, sales tracking, cash & bank operations, and audit logging. The system implements role-based access control (RBAC), multi-tenant isolation, and JWT-based authentication.

---

## 2. Technology Stack

### Core Framework
- **Django:** 6.0.1 (LTS)
- **Django REST Framework:** 3.16.1
- **Python Version:** 3.x (Python 3.8+)

### Authentication & Authorization
- **dj-rest-auth:** 5.0.2 (JWT + Session auth)
- **django-allauth:** 65.13.1 (User registration & social auth)
- **djangorestframework_simplejwt:** 5.5.1 (JWT tokens)
- **PyJWT:** 2.10.1

### Database & ORM
- **Default:** SQLite (db.sqlite3) — development
- **Production Ready:** MySQL (PyMySQL 1.1.2)
- **Custom ORM Tools:** django-model-utils 5.0.0 (TimeStampedModel, SoftDeletableModel)

### API Documentation & Schema
- **drf-spectacular:** 0.29.0 (OpenAPI 3.0 schema generation, ReDoc UI)

### Middleware & Cross-Origin
- **django-cors-headers:** 4.9.0 (CORS support)
- **Custom Middleware:** TenantMiddleware, AuditMiddleware

### Filtering & Pagination
- **django-filter:** 25.2 (QuerySet filtering)
- **DRF PageNumberPagination:** 10 items per page (default)

### Media & Files
- **Pillow:** 12.1.0 (Image processing)
- **Static/Media Serving:** Django defaults + media folder

### Utilities
- **python-decouple:** 3.8 (Environment variable management)
- **PyYAML:** 6.0.3 (Config parsing)
- **requests:** 2.32.5 (HTTP client)

---

## 3. Application Architecture

### Installed Apps (12 Local + 8 Third-Party)

#### Third-Party Apps
- `rest_framework` — API framework
- `corsheaders` — CORS support
- `allauth` — Auth system
- `rest_framework_simplejwt` — JWT tokens
- `drf_spectacular` — API documentation
- `django_filters` — Advanced filtering

#### Local Apps (Custom)
1. **apps.base** — Core functionality (middleware, permissions, audit)
2. **apps.users** — User management & authentication
3. **apps.otp** — One-Time Password service
4. **apps.subscription** — Subscription plans & management
5. **apps.tenant** — Multi-tenant isolation
6. **apps.stock_management** — Inventory management
7. **apps.sales** — Sales tracking & orders
8. **apps.cashandbank** — Cash & bank ledger operations
9. **apps.carts** — Shopping cart management
10. **apps.branch** — Branch/location management
11. **apps.message** — Messaging & contact forms
12. **seeds** — Data seeding for development

---

## 4. Core App: `apps.base`

### Purpose
Provides foundational functionality for all apps: authentication, permission management, middleware, pagination, and audit logging.

### Key Components

#### **Models**
- **BaseModel** (Abstract)
  - Inherits: `TimeStampedModel` (auto `created`, `modified`), `SoftDeletableModel` (soft delete support)
  - Fields: `is_active` (Boolean)
  
- **AuditLog**
  - Tracks all user actions: CREATE, UPDATE, DELETE, AUTH
  - Captures: User, Tenant, HTTP method, path, IP, status code, request payload
  - Indexed by: created time, action+entity, method+status code
  - Middleware auto-populates entries

#### **Middleware** ([apps/base/middleware.py](apps/base/middleware.py))
1. **TenantMiddleware** — Extracts tenant from request (header, user, or session) and stores in `request.tenant`
2. **AuditMiddleware** — Logs request/response to AuditLog table

#### **Permissions** ([apps/base/permissions.py](apps/base/permissions.py))
- `IsSuperAdmin` — Full system access
- `IsTenantAdmin` — Manage own tenant + users
- `IsCustomer` — Limited customer actions
- Custom RBAC logic for object-level checks

#### **DRF Configuration** ([apps/base/drf.py](apps/base/drf.py))
- **TenantFilterBackend** — Auto-filters querysets by user's tenant (global filter)
- **Custom Pagination** — PageNumberPagination, 10 items/page default

#### **Serializers** ([apps/base/serializers.py](apps/base/serializers.py))
- Generic serializers for common models (AuditLog, etc.)

---

## 5. User Management: `apps.users`

### Responsibilities
User registration, authentication, profile management, role assignment.

### Features
- **Custom User Model:** `User` (AUTH_USER_MODEL = 'users.User')
- **Roles:** SUPER_ADMIN, ADMIN, TENANT_USER, CUSTOMER
- **JWT Authentication:** 5-hour access token, 7-day refresh token
- **AllAuth Integration:** Email verification, password reset, social auth support

### API Endpoints
```
POST   /api/token/                  # Obtain JWT token pair
POST   /api/token/refresh/          # Refresh access token
POST   /api/token/verify/           # Verify token validity
GET    /api/users/                  # List users (filtered by tenant)
POST   /api/users/                  # Create user
GET    /api/users/{id}/             # Retrieve user
PUT    /api/users/{id}/             # Update user
DELETE /api/users/{id}/             # Soft-delete user
GET    /api/auth/me/                # Get current user profile
POST   /api/auth/logout/            # Blacklist token
```

---

## 6. Multi-Tenancy: `apps.tenant`

### Architecture
**Tenant Isolation Strategy:**
- Each user belongs to exactly ONE tenant (ForeignKey: `User.tenant`)
- All operations are **tenant-scoped** via TenantFilterBackend
- Middleware sets `request.tenant` for permission checks

### Tenant Model ([apps/tenant/models/tenant.py](apps/tenant/models/tenant.py))
```python
class Tenant:
  - business_name (CharField)
  - email (EmailField, unique)
  - phone, pan_number, location (optional)
  - package (FK → SubscriptionPlan)
  - status (pending, approved, rejected)
  - Methods: get_user_count(), can_add_user(), get_admins(), etc.
```

### API Endpoints
```
GET    /api/tenant/                 # List tenants (Super Admin only)
POST   /api/tenant/                 # Create tenant
GET    /api/tenant/{id}/            # Retrieve tenant
PUT    /api/tenant/{id}/            # Update tenant
DELETE /api/tenant/{id}/            # Delete tenant
GET    /api/tenant/{id}/users/      # Get users of tenant
```

---

## 7. Authentication & JWT

### Configuration
**Token Lifetimes:**
- Access Token: **5 hours**
- Refresh Token: **7 days**
- Token Rotation: **Enabled** (refresh tokens rotated, old ones blacklisted)

**Signing Algorithm:** HS256 (HMAC SHA-256)

**Auth Header:** `Authorization: Bearer <token>`

**Whitelist for Schema/Docs:** No auth required for `/api/docs/` and `/api/docs/schema/`

### Flow
1. User POSTs credentials to `/api/token/` → receives `access` + `refresh` tokens
2. User includes `Authorization: Bearer {access}` in requests
3. Middleware validates JWT signature and extracts user
4. When access expires, POST `/api/token/refresh/` with `refresh` token
5. Logout: POST `/api/auth/logout/` to blacklist token

---

## 8. Role-Based Access Control (RBAC)

### Roles & Permissions

| Role | Scope | Permissions |
|------|-------|-------------|
| **SUPER_ADMIN** | Global | Full system access, manage all tenants, all users, all data |
| **ADMIN** | Tenant | Manage own tenant, add/remove users, configure settings, view reports |
| **TENANT_USER** | Tenant | View tenant data, readonly access, manage own profile |
| **CUSTOMER** | Tenant | Browse products, manage cart, place orders, view order history |
| **INVENTORY MANAGER** | Branch |  Manage own Branch, add/remove product, view reports |
| **CASHIER** | Branch |  Manage own Branch's bill,manage the shifts |


### Permission Classes
- `@permission_classes([IsAuthenticated])` — Default (all authenticated)
- `@permission_classes([IsSuperAdmin])` — Super Admin only
- `@permission_classes([IsTenantAdmin])` — Tenant admin + owned resources
- Custom object-level permissions via `has_object_permission()`

---

## 9. Subscription Management: `apps.subscription`

### Responsibilities
Manage subscription plans, tier features, user limits, billing cycles.

### Key Entities
- **SubscriptionPlan** — Plan tiers (Free, Starter, Pro, Enterprise)
  - Fields: name, price, no_of_user (user limit), features (JSONField)
  - Used by Tenant to enforce user seat limits

### API Endpoints
```
GET    /api/subscription/            # List subscription plans
GET    /api/subscription/{id}/       # Retrieve plan details
```

---

## 10. Inventory & Stock Management: `apps.stock_management`

### Responsibilities
Track products, inventory levels, warehouses, stock movements.

### Key Entities
- **Product** — Inventory items (SKU, name, price, qty_on_hand)
- **Warehouse** — Physical locations
- **StockMovement** — In/out transactions (audit trail)

### API Endpoints
```
GET    /api/stock-management/products/         # List products (tenant-scoped)
POST   /api/stock-management/products/         # Create product
PUT    /api/stock-management/products/{id}/    # Update stock
GET    /api/stock-management/warehouses/       # List warehouses
POST   /api/stock-management/movements/        # Log stock movement
```

---

## 11. Sales & Orders: `apps.sales`

### Responsibilities
Process sales, invoices, order tracking, customer transactions.

### Key Entities
- **Order** — Customer purchase (order_date, total, status)
- **OrderItem** — Line items (qty, unit_price, subtotal)
- **Invoice** — Billing document (FK → Order)

### API Endpoints
```
GET    /api/sales/orders/                # List orders
POST   /api/sales/orders/                # Create order
PUT    /api/sales/orders/{id}/           # Update order status
GET    /api/sales/invoices/              # List invoices
POST   /api/sales/invoices/              # Generate invoice
GET    /api/sales/invoices/{id}/pdf/     # Download invoice PDF
```

---

## 12. Cash & Bank Operations: `apps.cashandbank`

### Responsibilities
Manage cash registers, bank accounts, ledger entries, financial transactions.

### Key Entities
- **CashRegister** — POS cash drawer (balance, shift management)
- **BankAccount** — Bank account details
- **Ledger** — Financial transactions (credits, debits)
- **LedgerService** — Business logic for balance calculations

### API Endpoints
```
GET    /api/cash-and-bank/accounts/         # List bank accounts
POST   /api/cash-and-bank/accounts/         # Create account
GET    /api/cash-and-bank/ledger/           # View ledger entries
POST   /api/cash-and-bank/ledger/           # Add transaction
GET    /api/cash-and-bank/balance/          # Get account balance
```

---

## 13. Shopping Carts: `apps.carts`

### Responsibilities
Manage customer shopping carts, session persistence, cart checkout.

### Key Entities
- **Cart** — Customer basket (FK → User, status: active/abandoned)
- **CartItem** — Products in cart (qty, unit_price)

### API Endpoints
```
GET    /api/carts/                      # Get current user's cart
POST   /api/carts/items/                # Add item to cart
PUT    /api/carts/items/{id}/           # Update cart item qty
DELETE /api/carts/items/{id}/           # Remove item from cart
POST   /api/carts/checkout/             # Convert cart to order
```

---

## 14. OTP Service: `apps.otp`

### Responsibilities
Generate, send, and verify one-time passwords for 2FA, password reset.

### Features
- **Throttling:** 10,000 OTP requests/hour (configurable)
- **Expiration:** 15 minutes (default)
- **Delivery:** Email via Django email backend

### API Endpoints
```
POST   /api/otp/send/                   # Request OTP (sent to email)
POST   /api/otp/verify/                 # Verify OTP code
```

---

## 15. Messaging: `apps.message`

### Responsibilities
Contact forms, support inquiries, in-app notifications.

### Key Entities
- **Message/Contact** — User-submitted forms
- **Notification** — System-generated alerts

### API Endpoints
```
POST   /api/messages/contact/           # Submit contact form
GET    /api/messages/notifications/     # List user notifications
PATCH  /api/messages/notifications/{id}/# Mark notification read
```

---

## 16. Branch Management: `apps.branch`

### Responsibilities
Manage business branches/locations, assign staff, link to warehouses.

### Key Entities
- **Branch** — Physical location (name, address, manager)

### API Endpoints
```
GET    /api/branch/                     # List branches (tenant-scoped)
POST   /api/branch/                     # Create branch
PUT    /api/branch/{id}/                # Update branch
DELETE /api/branch/{id}/                # Delete branch
GET    /api/branch/{id}/staff/          # Get branch staff
```

---

## 17. Core URL Configuration

### API Routes Structure ([core/routes/api_urls.py](core/routes/api_urls.py))

```
/api/
├── docs/schema/                         # OpenAPI 3.0 schema
├── docs/                                # ReDoc interactive docs
├── token/                               # JWT token endpoints
├── token/refresh/
├── token/verify/
├── users/                               # User management (ViewSet)
├── auth/                                # Authentication (ViewSet)
├── audit-logs/                          # Audit log viewer
├── otp/                                 # OTP routes
├── messages/                            # Messaging
├── subscription/                        # Subscription plans
├── stock-management/                    # Inventory
├── tenant/                              # Tenant management
├── branch/                              # Branch management
├── sales/                               # Sales & orders
├── cash-and-bank/                       # Financial ops
└── carts/                               # Shopping carts
```

---

## 18. Security & Middleware Stack

### Middleware Order (from [core/settings.py](core/settings.py))
1. **SecurityMiddleware** — HSTS, XSS protection
2. **CorsMiddleware** — CORS headers (before session)
3. **CommonMiddleware** — Common headers
4. **CsrfViewMiddleware** — CSRF token validation
5. **AuthenticationMiddleware** — User identification
6. **TenantMiddleware** — Extract & set request.tenant
7. **AuditMiddleware** — Log all requests
8. **AccountMiddleware** — django-allauth


### Security Settings
- **CSRF_TRUSTED_ORIGINS:** backend.servespare.xyz, localhost:3000, imspravidhi.vercel.app
- **CORS_ALLOWED_ORIGINS:** localhost:3000, frontend domains, ngrok dev tunnel
- **CORS_ALLOW_CREDENTIALS:** True
- **ALLOWED_HOSTS:** Dev + prod domains listed

### Secrets Management
- `SECRET_KEY` — Loaded from environment, fallback for dev
- `DEBUG` — Environment-controlled (FALSE in production)
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — From .env file

---

## 19. Database Configuration

### Default (Development)
```
Engine:  SQLite (django.db.backends.sqlite3)
File:    db.sqlite3
```

### Production-Ready (MySQL)
```
Engine:   django.db.backends.mysql
Driver:   PyMySQL 1.1.2
Host:     localhost (configurable)
Port:     3306
DB Name:  servesp1_servespare (commented example)
```

### ORM Features
- **Soft Deletes:** Enabled via `SoftDeletableModel` (is_deleted flag, not hard deletion)
- **Timestamps:** Auto `created` + `modified` fields on all BaseModel subclasses
- **Audit Trail:** AuditLog model tracks all user actions
- **Pagination:** Default 10 items/page (DRF PageNumberPagination)

---

## 20. API Documentation & Schema

### OpenAPI 3.0 Integration (drf-spectacular)

**Endpoints:**
- `GET /api/docs/schema/` — Fetch raw OpenAPI 3.0 schema (JSON)
- `GET /api/docs/` — Interactive ReDoc UI (no auth required)

**Features:**
- Auto-generated from ViewSet docstrings & serializers
- ReDoc theme customized (primary color: #32329f)
- Expandable responses (200, 201 by default)
- Sample request/response payloads shown

---

## 21. Configuration Files & Environment

### Environment Variables ([env.example](env.example))
```bash
# Django Core
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# JWT Tokens
JWT_ACCESS_TOKEN_LIFETIME=60          # minutes
JWT_REFRESH_TOKEN_LIFETIME=7          # days
```

### Settings Modules
- [core/settings.py](core/settings.py) — Main settings file
- [core/configuration/apps.py](core/configuration/apps.py) — INSTALLED_APPS lists
- [core/configuration/rest.py](core/configuration/rest.py) — DRF + drf-spectacular config
- [core/configuration/auth.py](core/configuration/auth.py) — JWT, AllAuth, SIMPLE_JWT settings

---

## 22. Email Configuration

### SMTP Setup
```
Host:     smtp.gmail.com
Port:     587
TLS:      Enabled
Auth:     Gmail App Password (recommended, not main password)
From:     noreply@serveiq.com (configurable)
```

### Email Backend
- **Development:** Console backend (emails printed to stdout if no SMTP creds)
- **Production:** SMTP backend (real emails sent)

### Use Cases
- User registration confirmation
- Password reset
- OTP delivery
- Admin notifications



## 23. Data Seeding & Fixtures

### Seeds App ([seeds/](seeds/))
- **seed_data.json** — Initial sample data (users, tenants, products, orders)
- **management/commands/** — Custom Django commands to populate DB
- Purpose: Bootstrap development environment with realistic test data

### Load Seeds
```bash
python manage.py loaddata seeds/seed_data.json
# OR custom command
python manage.py seed_db
```

## 24. Deployment & Runtime

### Requirements
```
Python 3.8+
Django 6.0.1
DRF 3.16.1
MySQL (or SQLite for dev)
```

### Installation
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Production Checklist
- [ ] DEBUG = False in .env
- [ ] SECRET_KEY randomized and secured
- [ ] ALLOWED_HOSTS updated for production domain
- [ ] Database migrated to MySQL (not SQLite)
- [ ] Email SMTP credentials configured
- [ ] JWT token lifetimes adjusted (optional)
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Use WSGI server (Gunicorn, uWSGI) with reverse proxy (Nginx)

### Media & Static Files
```
/static/          — CSS, JS, images (collectstatic destination)
/media/           — User uploads (profile pics, inventory images)
/staticfiles/     — Production collected statics
```

---

## 25. Key Integrations & Features

### Multi-Tenancy
✅ Tenant isolation at middleware level  
✅ Automatic queryset filtering per tenant  
✅ Per-tenant user limits via subscription  
✅ Audit logging per tenant  

### Authentication
✅ JWT tokens (5hr access, 7d refresh)  
✅ Token rotation & blacklisting  
✅ Social auth via AllAuth  
✅ Email verification  

### RBAC
✅ 4 role types (Super Admin, Admin, Tenant User, Customer)  
✅ Object-level permission checks  
✅ Tenant-aware authorization  

### API Docs
✅ OpenAPI 3.0 schema auto-generated  
✅ Interactive ReDoc UI  
✅ Postman collections  

### Audit & Compliance
✅ Full request/response logging via AuditLog  
✅ Soft deletes (data retention)  
✅ IP tracking & user agent capture  
✅ Indexed by action, entity, timestamp  

### Scalability
✅ Pagination (10/page default)  
✅ Database indexing on frequently filtered fields  
✅ Async email delivery support (with Celery, optional)  
✅ DRF caching support (optional)  

---

## 26. Notable Patterns & Best Practices

1. **BaseModel Abstract Class** — All domain models inherit from BaseModel for consistent timestamps & soft deletes
2. **TenantFilterBackend** — Global DRF filter ensures tenant isolation at query level
3. **DRY Permissions** — Reusable permission classes (IsSuperAdmin, IsTenantAdmin) across views
4. **Middleware for Cross-Cutting Concerns** — TenantMiddleware, AuditMiddleware decouple auth & logging from business logic
5. **Separated Configuration** — Settings split into modular config files (apps.py, rest.py, auth.py) for maintainability
6. **Signal-Based Triggers** — Apps use Django signals for post-save, pre-delete hooks (e.g., ledger updates on order creation)
7. **Service Layer Pattern** — Business logic in dedicated `*_service.py` files (e.g., LedgerService) separate from views

---

## 27. API Response Format

### Standard Success Response
```json
{
  "status": 200,
  "data": { ... },
  "message": "Success"
}
```

### Paginated Response
```json
{
  "count": 50,
  "next": "http://api.example.com/users/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

### Error Response
```json
{
  "detail": "Not found."
}
```
or
```json
{
  "field_name": ["Error message"]
}
```

---

## 28. Summary Table

| Component | Tech | Purpose |
|-----------|------|---------|
| Framework | Django 6.0 | Web framework |
| API | DRF 3.16 | REST API builder |
| Auth | JWT + AllAuth | Token & user management |
| Tenancy | Custom Middleware | Multi-tenant isolation |
| RBAC | Custom Permission Classes | Role-based access |
| Docs | drf-spectacular | OpenAPI 3.0 schema |
| Database | SQLite/MySQL | Data persistence |
| Logging | AuditLog Model | Request tracking |
| Email | SMTP (Gmail) | Notifications & OTP |
| Media | Pillow + Django | Image processing |

---

## 29. Getting Started for New Developers

### 1. Clone & Setup
```bash
git clone <repo>
cd servespare_backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp env.example .env
# Edit .env with your local settings
```

### 3. Initialize Database
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata seeds/seed_data.json  # Optional
```

### 4. Run Server
```bash
python manage.py runserver
# Visit http://localhost:8000/api/docs/
```

### 5. Explore API
- ReDoc Docs: http://localhost:8000/api/docs/ or https://backend.servespare.xyz/api/docs/
- OpenAPI Schema: http://localhost:8000/api/docs/schema/
- Test endpoints via Postman collections in docs/postman_collections/

---

## 30. Common Workflows

### Add a New API Endpoint
1. Create model in `apps/myapp/models.py`
2. Create serializer in `apps/myapp/serializers.py`
3. Create viewset in `apps/myapp/views.py`
4. Register route in `apps/myapp/urls.py`
5. Add to `core/routes/api_urls.py`

### Create a New App
```bash
python manage.py startapp myapp apps/
# Add to INSTALLED_APPS in core/configuration/apps.py
# Create models.py, serializers.py, views.py, urls.py
# Run migrations: python manage.py makemigrations && python manage.py migrate
```

### Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py migrate apps.users 0001_initial  # Specific app/migration
```

---

**End of Report** 
