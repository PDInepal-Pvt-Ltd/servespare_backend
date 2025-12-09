# Stock Management API Documentation

## Base URL
```
/api/stock-management/
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

---

## Endpoints Overview

### Parties
- `/api/stock-management/parties/` - Manage suppliers and customers

### Purchase Orders
- `/api/stock-management/purchase-orders/` - Manage purchase orders
- `/api/stock-management/purchase-order-items/` - Manage purchase order items

### Inventory
- `/api/stock-management/inventory/` - Manage inventory items
- `/api/stock-management/inventory-images/` - Manage inventory images

---

## 1. PARTIES API

### List Parties
**GET** `/api/stock-management/parties/`

**Query Parameters:**
- `party_type` (optional): `supplier` or `customer`
- `customer_type` (optional): `retail_customer`, `retailer`, `workshop`, `distributor`, `wholesaler`
- `is_active` (optional): `true` or `false`
- `search` (optional): Search by party name

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "party_type": "supplier",
    "customer_type": null,
    "party_name": "ABC Suppliers",
    "contact_person": "John Doe",
    "phone": "+1234567890",
    "email": "contact@abcsuppliers.com",
    "address": "123 Main St",
    "city": "New York",
    "state_province": "NY",
    "pan_number": "ABCDE1234F",
    "payment_terms": "30_day_credit",
    "credit_limit": "10000.00",
    "opening_balance": "0.00",
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  }
]
```

### Create Party
**POST** `/api/stock-management/parties/`

**Request Body:**
```json
{
  "party_type": "supplier",
  "party_name": "ABC Suppliers",
  "contact_person": "John Doe",
  "phone": "+1234567890",
  "email": "contact@abcsuppliers.com",
  "address": "123 Main St",
  "city": "New York",
  "state_province": "NY",
  "pan_number": "ABCDE1234F",
  "payment_terms": "30_day_credit",
  "credit_limit": "10000.00",
  "opening_balance": "0.00"
}
```

**Field Descriptions:**
- `party_type` (required): `supplier` or `customer`
- `customer_type` (required if party_type=customer): `retail_customer`, `retailer`, `workshop`, `distributor`, `wholesaler`
- `party_name` (required): Name of the party
- `contact_person` (optional): Contact person name
- `phone` (optional): Phone number
- `email` (optional): Email address
- `address` (optional): Street address
- `city` (optional): City name
- `state_province` (optional): State or province
- `pan_number` (optional): PAN number
- `payment_terms` (optional): `cash`, `cheque`, `7_day_credit`, `15_day_credit`, `30_day_credit`, `45_day_credit` (default: `cash`)
- `credit_limit` (optional): Credit limit (default: 0.00)
- `opening_balance` (optional): Opening balance (default: 0.00)

### Get Suppliers
**GET** `/api/stock-management/parties/suppliers/`

Get all active suppliers.

### Get Customers
**GET** `/api/stock-management/parties/customers/`

Get all active customers.

---

## 2. PURCHASE ORDERS API

### List Purchase Orders
**GET** `/api/stock-management/purchase-orders/`

**Query Parameters:**
- `supplier` (optional): Filter by supplier ID
- `status` (optional): `draft`, `ordered`, `received`, `billed`
- `is_active` (optional): `true` or `false`
- `search` (optional): Search by PO number

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "po_number": "PO-001",
    "status": "ordered",
    "supplier": 1,
    "supplier_detail": {
      "id": 1,
      "party_name": "ABC Suppliers",
      ...
    },
    "order_date": "2025-12-08",
    "expected_delivery_date": "2025-12-15",
    "purchase_invoice": null,
    "notes": "Urgent delivery required",
    "terms_and_condition": "Payment within 30 days",
    "items": [
      {
        "id": 1,
        "item_name": "Brake Pads",
        "part_number": "BP-001",
        "quantity": "10.00",
        "unit_price": "25.00",
        "tax": "18.00",
        "subtotal": "250.00",
        "tax_amount": "45.00",
        "total_price": "295.00"
      }
    ],
    "total_amount": "295.00",
    "total_tax": "45.00",
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  }
]
```

### Create Purchase Order
**POST** `/api/stock-management/purchase-orders/`

**Request Body:**
```json
{
  "po_number": "PO-001",
  "status": "draft",
  "supplier": 1,
  "order_date": "2025-12-08",
  "expected_delivery_date": "2025-12-15",
  "notes": "Urgent delivery required",
  "terms_and_condition": "Payment within 30 days"
}
```

### Add Item to Purchase Order
**POST** `/api/stock-management/purchase-orders/{id}/add_item/`

**Request Body:**
```json
{
  "item_name": "Brake Pads",
  "part_number": "BP-001",
  "quantity": "10.00",
  "unit_price": "25.00",
  "tax": "18.00",
  "discount_description": "Bulk order discount"
}
```

### Get Purchase Orders by Status
**GET** `/api/stock-management/purchase-orders/by_status/?status={status}`

---

## 3. PURCHASE ORDER ITEMS API

### List Purchase Order Items
**GET** `/api/stock-management/purchase-order-items/`

**Query Parameters:**
- `purchase_order` (optional): Filter by purchase order ID
- `is_active` (optional): `true` or `false`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "purchase_order": 1,
    "item_name": "Brake Pads",
    "part_number": "BP-001",
    "quantity": "10.00",
    "unit_price": "25.00",
    "tax": "18.00",
    "discount_description": "Bulk order discount",
    "subtotal": "250.00",
    "tax_amount": "45.00",
    "total_price": "295.00",
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  }
]
```

---

## 4. INVENTORY API

### List Inventory Items
**GET** `/api/stock-management/inventory/`

**Query Parameters:**
- `category` (optional): `local` or `original`
- `vehicle_type` (optional): `two_wheeler` or `four_wheeler`
- `party` (optional): Filter by party/supplier ID
- `is_active` (optional): `true` or `false`
- `low_stock` (optional): `true` to get low stock items
- `search` (optional): Search by item name, part number, or barcode

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "item_name": "Brake Pads Set",
    "category": "original",
    "vehicle_type": "two_wheeler",
    "party": 1,
    "party_detail": {
      "id": 1,
      "party_name": "ABC Suppliers",
      ...
    },
    "part_number": "BP-001",
    "hsn_code": "8708.99.90",
    "quantity": "50.00",
    "min_stock_level": "20.00",
    "price": "25.00",
    "mrp": "35.00",
    "distributor_price": "20.00",
    "wholesale_price": "22.50",
    "retail_pricing": "30.00",
    "storage_location": "Warehouse A, Shelf 5",
    "warranty_period": "12_month",
    "barcode": "1234567890123",
    "vehicle_bike_details": "Compatible with Honda, Yamaha",
    "model": "Universal",
    "type": "Brake System",
    "images": [
      {
        "id": 1,
        "image": "/media/inventory_images/brake_pads.jpg",
        "description": "Front view",
        "is_primary": true
      }
    ],
    "is_low_stock": false,
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  }
]
```

### Create Inventory Item
**POST** `/api/stock-management/inventory/`

**Request Body:**
```json
{
  "item_name": "Brake Pads Set",
  "category": "original",
  "vehicle_type": "two_wheeler",
  "party": 1,
  "part_number": "BP-001",
  "hsn_code": "8708.99.90",
  "quantity": "50.00",
  "min_stock_level": "20.00",
  "price": "25.00",
  "mrp": "35.00",
  "distributor_price": "20.00",
  "wholesale_price": "22.50",
  "retail_pricing": "30.00",
  "storage_location": "Warehouse A, Shelf 5",
  "warranty_period": "12_month",
  "barcode": "1234567890123",
  "vehicle_bike_details": "Compatible with Honda, Yamaha",
  "model": "Universal",
  "type": "Brake System"
}
```

**Pricing Validation:** Distributor < Wholesale < Retail < MRP

**Warranty Period Options:**
- `no_warranty`, `1_month`, `2_month`, `3_month`, `4_month`, `5_month`, `6_month`, `9_month`, `12_month`, `24_month`

### Get Low Stock Items
**GET** `/api/stock-management/inventory/low_stock/`

Get all items where quantity <= min_stock_level.

### Get Inventory by Category
**GET** `/api/stock-management/inventory/by_category/?category={category}`

### Get Inventory by Vehicle Type
**GET** `/api/stock-management/inventory/by_vehicle_type/?vehicle_type={vehicle_type}`

### Add Image to Inventory Item
**POST** `/api/stock-management/inventory/{id}/add_image/`

**Request Body (multipart/form-data):**
```
image: <file>
description: "Front view"
is_primary: true
```

### Bulk Upload Inventory Items
**POST** `/api/stock-management/inventory/bulk_upload/`

Upload multiple inventory items from a CSV file in a single request. This endpoint accepts a CSV file and processes each row to create inventory items.

**Authentication:** Required (JWT Token)

**Content-Type:** `multipart/form-data`

**Request Body:**
```
file: <csv_file>
```

**Request Parameters:**
- `file` (required): CSV file containing inventory data. The file must have a `.csv` extension.

**What to Provide in POST Request:**

When testing this API, you need to provide:

1. **HTTP Method:** `POST`
2. **URL:** `/api/stock-management/inventory/bulk_upload/`
3. **Headers:**
   - `Authorization: Bearer <your_jwt_token>` (Required)
   - `Content-Type: multipart/form-data` (Usually set automatically by the client)
4. **Body (Form Data):**
   - Key: `file`
   - Value: Your CSV file (must have `.csv` extension)

**Quick Testing Checklist:**
- ✅ JWT token in Authorization header
- ✅ CSV file attached with key name `file`
- ✅ CSV file has `.csv` extension
- ✅ CSV file has proper headers (first row)
- ✅ CSV file has at least one data row
- ✅ Required columns are present in CSV

**CSV File Requirements:**
- File format: CSV (Comma-Separated Values)
- Encoding: UTF-8 (BOM is automatically handled)
- First row must contain column headers
- Empty rows are automatically skipped
- Each data row is processed independently

**Required CSV Columns:**
The following columns are mandatory and must be present in your CSV file:

| CSV Column Name | Description | Valid Values |
|----------------|-------------|--------------|
| `Item Name*` or `Item Name` | Name of the inventory item | Any string |
| `Part Number*` or `Part Number` | Part number or SKU | Any string |
| `Category*` or `Category* (local/original)` | Product category | `local` or `original` |
| `Vehicle Type*` or `Vehicle Type* (two_wheeler/four_wheeler)` | Type of vehicle | `two_wheeler` or `four_wheeler` |
| `Quantity*` or `Quantity` | Current stock quantity | Positive number (decimal allowed) |
| `Min Stock Level*` or `Min Stock Level` | Minimum stock level threshold | Positive number (decimal allowed) |
| `Price*` or `Price` | Base/cost price | Positive number (decimal allowed) |
| `MRP*` or `MRP` | Maximum Retail Price | Positive number (decimal allowed) |

**Optional CSV Columns:**
The following columns are optional but can be included:

| CSV Column Name | Description | Valid Values |
|----------------|-------------|--------------|
| `Vehicle Name` | Vehicle/Bike compatibility details | Any string |
| `Bike Model` | Model name | Any string |
| `Bike Type` | Type of vehicle/part | Any string |
| `HSN Code` | HSN Code for tax purposes | Any string |
| `Retail Price` | Retail selling price | Positive number (must be < MRP) |
| `Wholesale Price` | Wholesale selling price | Positive number (must be < Retail Price) |
| `Distributor Price` | Distributor selling price | Positive number (must be < Wholesale Price) |
| `Supplier/Party Name` | Supplier/Party name | Must match existing party name (case-insensitive) |
| `Barcode` | Barcode/UPC code | Unique string (must be unique across all inventory) |
| `Location` | Storage location | Any string |
| `Warranty Period (months)` | Warranty period in months | `0`, `1`, `2`, `3`, `4`, `5`, `6`, `9`, `12`, or `24` |

**CSV Format Example:**
```csv
Item Name*,Part Number*,Category* (local/original),Vehicle Type* (two_wheeler/four_wheeler),Vehicle Name,Bike Model,Bike Type,HSN Code,Quantity*,Min Stock Level*,Price*,MRP*,Retail Price,Wholesale Price,Distributor Price,Supplier/Party Name,Barcode,Location,Warranty Period (months)
Brake Pad - Premium Quality,BP-001,local,two_wheeler,Hero Splendor,Splendor Plus,Commuter,8708.99.90,50,10,150.00,250.00,200.00,180.00,160.00,ABC Suppliers,BP001001,Main Warehouse - Shelf A-12,6
Oil Filter - Standard,OF-002,original,four_wheeler,Maruti Swift,Swift Dzire,Sedan,8421.23.45,100,25,75.00,120.00,100.00,90.00,80.00,XYZ Auto Parts,OF002001,Warehouse B - Shelf C-5,12
Air Filter Element,AF-003,local,two_wheeler,Honda Activa,Activa 6G,Scooter,8421.23.45,75,15,45.00,80.00,65.00,55.00,50.00,ABC Suppliers,AF003001,Warehouse A - Shelf D-3,3
```

**Response Formats:**

**Success Response (All rows imported successfully):**
- **Status Code:** `201 Created`
```json
{
  "total_rows": 3,
  "successful": 3,
  "failed": 0,
  "successful_imports": [
    {
      "row": 2,
      "id": 1,
      "item_name": "Brake Pad - Premium Quality",
      "part_number": "BP-001"
    },
    {
      "row": 3,
      "id": 2,
      "item_name": "Oil Filter - Standard",
      "part_number": "OF-002"
    },
    {
      "row": 4,
      "id": 3,
      "item_name": "Air Filter Element",
      "part_number": "AF-003"
    }
  ],
  "failed_imports": []
}
```

**Partial Success Response (Some rows failed):**
- **Status Code:** `207 Multi-Status`
```json
{
  "total_rows": 5,
  "successful": 3,
  "failed": 2,
  "successful_imports": [
    {
      "row": 2,
      "id": 1,
      "item_name": "Brake Pad - Premium Quality",
      "part_number": "BP-001"
    },
    {
      "row": 3,
      "id": 2,
      "item_name": "Oil Filter - Standard",
      "part_number": "OF-002"
    },
    {
      "row": 5,
      "id": 3,
      "item_name": "Air Filter Element",
      "part_number": "AF-003"
    }
  ],
  "failed_imports": [
    {
      "row": 4,
      "data": {
        "Item Name*": "Test Item",
        "Part Number*": "TEST-001",
        "Category* (local/original)": "invalid",
        "Vehicle Type* (two_wheeler/four_wheeler)": "two_wheeler",
        "Quantity*": "",
        "Min Stock Level*": "10",
        "Price*": "100",
        "MRP*": "150"
      },
      "errors": [
        "Category must be 'local' or 'original', got 'invalid'",
        "Required field 'quantity' is missing"
      ]
    },
    {
      "row": 6,
      "data": {
        "Item Name*": "Duplicate Item",
        "Part Number*": "BP-001",
        "Category* (local/original)": "local",
        "Vehicle Type* (two_wheeler/four_wheeler)": "two_wheeler",
        "Quantity*": "20",
        "Min Stock Level*": "5",
        "Price*": "100",
        "MRP*": "150"
      },
      "errors": {
        "part_number": ["inventory with this part number already exists."]
      }
    }
  ]
}
```

**Error Responses:**

**Missing File:**
- **Status Code:** `400 Bad Request`
```json
{
  "error": "CSV file is required. Please upload a file with key \"file\"."
}
```

**Invalid File Type:**
- **Status Code:** `400 Bad Request`
```json
{
  "error": "Invalid file type. Please upload a CSV file."
}
```

**Empty/Invalid CSV:**
- **Status Code:** `400 Bad Request`
```json
{
  "error": "CSV file is empty or invalid. Please ensure the file has headers and data rows."
}
```

**Validation Rules:**
1. **Category:** Must be exactly `local` or `original` (case-insensitive)
2. **Vehicle Type:** Must be exactly `two_wheeler` or `four_wheeler` (case-insensitive)
3. **Numeric Fields:** Quantity, prices, and stock levels must be valid positive numbers (decimals allowed)
4. **Pricing Hierarchy:** If provided, prices must follow: `Distributor Price < Wholesale Price < Retail Price < MRP`
5. **Party/Supplier:** Must match an existing active party name exactly (case-insensitive lookup)
6. **Barcode:** Must be unique across all inventory items (if provided)
7. **Part Number:** Must be unique across all inventory items
8. **Warranty Period:** If provided as numeric months, must be one of: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `9`, `12`, `24`

**Warranty Period Conversion:**
- Numeric values are automatically converted:
  - `0` → `no_warranty`
  - `1` → `1_month`
  - `2` → `2_month`
  - `3` → `3_month`
  - `4` → `4_month`
  - `5` → `5_month`
  - `6` → `6_month`
  - `9` → `9_month`
  - `12` → `12_month`
  - `24` → `24_month`

**Usage Examples:**

**Using cURL:**
```bash
# Replace YOUR_JWT_TOKEN with your actual JWT token
# Replace inventory_items.csv with your CSV file path
curl -X POST \
  https://your-domain.com/api/stock-management/inventory/bulk_upload/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@inventory_items.csv"
```

**Example with actual values:**
```bash
curl -X POST \
  http://localhost:8000/api/stock-management/inventory/bulk_upload/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -F "file=@/path/to/inventory_items.csv"
```

**Using Python (requests):**
```python
import requests

# Replace with your actual values
url = "https://your-domain.com/api/stock-management/inventory/bulk_upload/"
token = "YOUR_JWT_TOKEN"
csv_file_path = "inventory_items.csv"

headers = {
    "Authorization": f"Bearer {token}"
}

# Open the CSV file and attach it with key name "file"
with open(csv_file_path, "rb") as csv_file:
    files = {
        "file": (csv_file_path, csv_file, "text/csv")
    }
    response = requests.post(url, headers=headers, files=files)
    
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
```

**Using Postman:**
1. **Method:** Select `POST`
2. **URL:** Enter `http://your-domain.com/api/stock-management/inventory/bulk_upload/`
3. **Headers:**
   - Key: `Authorization`
   - Value: `Bearer YOUR_JWT_TOKEN`
4. **Body:**
   - Select `form-data`
   - Add a new key: `file` (type: File)
   - Click "Select Files" and choose your CSV file
5. **Send** the request

**Using JavaScript (fetch):**
```javascript
// Assuming you have a file input element: <input type="file" id="csvFile" />
const fileInput = document.getElementById('csvFile');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file); // Key must be 'file'

fetch('https://your-domain.com/api/stock-management/inventory/bulk_upload/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
    // Don't set Content-Type header - browser will set it automatically with boundary
  },
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Success:', data);
  console.log(`Total rows: ${data.total_rows}`);
  console.log(`Successful: ${data.successful}`);
  console.log(`Failed: ${data.failed}`);
})
.catch(error => console.error('Error:', error));
```

**Using Axios (JavaScript):**
```javascript
import axios from 'axios';

const formData = new FormData();
formData.append('file', csvFile); // csvFile is a File object

axios.post('https://your-domain.com/api/stock-management/inventory/bulk_upload/', formData, {
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'multipart/form-data'
  }
})
.then(response => {
  console.log('Response:', response.data);
})
.catch(error => {
  console.error('Error:', error.response.data);
});
```

**Important Notes:**
- Empty rows are automatically skipped during processing
- Each row is validated independently - failed rows don't prevent successful rows from being imported
- Row numbers in the response correspond to the actual row number in the CSV file (header is row 1)
- Party/Supplier names must exist in the system and be active (case-insensitive matching)
- Barcode values must be unique across all inventory items
- Part numbers must be unique across all inventory items
- The API supports flexible column naming - you can use `Item Name` or `Item Name*`, both will work
- File encoding is automatically handled (UTF-8 with BOM support)
- Large CSV files are processed row-by-row, so partial success is possible

---

## 5. INVENTORY IMAGES API

### List Inventory Images
**GET** `/api/stock-management/inventory-images/`

**Query Parameters:**
- `inventory` (optional): Filter by inventory item ID
- `is_primary` (optional): `true` or `false`
- `is_active` (optional): `true` or `false`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "inventory": 1,
    "image": "/media/inventory_images/brake_pads.jpg",
    "description": "Front view",
    "is_primary": true,
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  }
]
```

### Create Inventory Image
**POST** `/api/stock-management/inventory-images/`

**Request Body (multipart/form-data):**
```
inventory: 1
image: <file>
description: "Front view"
is_primary: true
```

---

## Data Formats

### Party Object
```json
{
  "id": 1,
  "party_type": "supplier|customer",
  "customer_type": "retail_customer|retailer|workshop|distributor|wholesaler (if customer)",
  "party_name": "string (required)",
  "contact_person": "string (optional)",
  "phone": "string (optional)",
  "email": "string (optional)",
  "address": "string (optional)",
  "city": "string (optional)",
  "state_province": "string (optional)",
  "pan_number": "string (optional)",
  "payment_terms": "cash|cheque|7_day_credit|15_day_credit|30_day_credit|45_day_credit",
  "credit_limit": "decimal (default: 0.00)",
  "opening_balance": "decimal (default: 0.00)",
  "is_active": "boolean",
  "created": "datetime",
  "modified": "datetime"
}
```

### Purchase Order Object
```json
{
  "id": 1,
  "po_number": "string (required, unique)",
  "status": "draft|ordered|received|billed",
  "supplier": "integer (FK to Party)",
  "order_date": "date (required)",
  "expected_delivery_date": "date (optional)",
  "purchase_invoice": "file (optional)",
  "notes": "string (optional)",
  "terms_and_condition": "string (optional)",
  "items": [PurchaseOrderItem],
  "total_amount": "decimal (calculated)",
  "total_tax": "decimal (calculated)",
  "is_active": "boolean",
  "created": "datetime",
  "modified": "datetime"
}
```

### Inventory Object
```json
{
  "id": 1,
  "item_name": "string (required)",
  "category": "local|original",
  "vehicle_type": "two_wheeler|four_wheeler",
  "party": "integer (FK to Party, optional)",
  "part_number": "string (optional)",
  "hsn_code": "string (optional)",
  "quantity": "decimal (default: 0.00)",
  "min_stock_level": "decimal (default: 0.00)",
  "price": "decimal",
  "mrp": "decimal",
  "distributor_price": "decimal",
  "wholesale_price": "decimal",
  "retail_pricing": "decimal",
  "storage_location": "string (optional)",
  "warranty_period": "no_warranty|1_month|2_month|...|24_month",
  "barcode": "string (optional, unique)",
  "vehicle_bike_details": "string (optional)",
  "model": "string (optional)",
  "type": "string (optional)",
  "images": [InventoryImage],
  "is_low_stock": "boolean (calculated)",
  "is_active": "boolean",
  "created": "datetime",
  "modified": "datetime"
}
```

---

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

