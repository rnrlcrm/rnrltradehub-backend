# Validation and Report Export Features

## Overview

This document describes the input validation and report export features implemented in the RNRL TradeHub backend.

## Input Validation

### Validators Module (`validators.py`)

Provides comprehensive validation for Indian business identifiers and contact information:

#### 1. PAN (Permanent Account Number) Validation

**Format**: `AAAAA9999A`
- First 5 characters: Uppercase letters
- Next 4 characters: Digits  
- Last character: Uppercase letter

**Example**: `ABCDE1234F`

```python
from validators import validate_pan, sanitize_pan

# Validate PAN
validate_pan("ABCDE1234F")  # Returns True
validate_pan("ABC123")  # Raises ValidationError

# Sanitize PAN (converts to uppercase, strips whitespace)
pan = sanitize_pan("  abcde1234f  ")  # Returns "ABCDE1234F"
```

#### 2. GSTIN (GST Identification Number) Validation

**Format**: `99AAAAA9999A9Z9`
- First 2 characters: State code (digits)
- Next 10 characters: PAN number
- Next character: Entity number (alphanumeric)
- Next character: 'Z' (constant)
- Last character: Check digit (alphanumeric)

**Example**: `27ABCDE1234F1Z5`

```python
from validators import validate_gstin, sanitize_gstin

# Validate GSTIN
validate_gstin("27ABCDE1234F1Z5")  # Returns True
validate_gstin("INVALID")  # Raises ValidationError
validate_gstin(None)  # Returns True (GSTIN is optional)

# Sanitize GSTIN
gstin = sanitize_gstin("27abcde1234f1z5")  # Returns "27ABCDE1234F1Z5"
```

**Note**: The PAN embedded in GSTIN (characters 3-12) is also validated.

#### 3. Mobile Number Validation

**Accepted Formats**:
- `9876543210` (10 digits)
- `+919876543210` (with +91 prefix)
- `919876543210` (with 91 prefix)
- `+91 98765 43210` (with spaces)
- `98765-43210` (with hyphens)

**Rules**:
- Must be exactly 10 digits after removing prefixes
- Must start with 6, 7, 8, or 9

```python
from validators import validate_mobile, sanitize_mobile

# Validate mobile
validate_mobile("9876543210")  # Returns True
validate_mobile("+91 98765 43210")  # Returns True
validate_mobile("123456")  # Raises ValidationError

# Sanitize mobile (removes +91/91 prefix, spaces, hyphens)
mobile = sanitize_mobile("+91 98765-43210")  # Returns "9876543210"
```

#### 4. Pincode Validation

**Format**: 6 digits (must not start with 0)

**Example**: `110001`, `400001`

```python
from validators import validate_pincode, sanitize_pincode

# Validate pincode
validate_pincode("110001")  # Returns True
validate_pincode("0123456")  # Raises ValidationError
```

#### 5. IFSC Code Validation

**Format**: `AAAA0999999`
- First 4 characters: Bank code (uppercase letters)
- 5th character: 0 (zero)
- Last 6 characters: Branch code (alphanumeric)

**Example**: `SBIN0001234`

```python
from validators import validate_ifsc, sanitize_ifsc

# Validate IFSC
validate_ifsc("SBIN0001234")  # Returns True
validate_ifsc(None)  # Returns True (IFSC is optional)
```

### Automatic Validation in API Schemas

Validation is automatically applied when creating or updating business partners:

```python
# Example API request
POST /api/business-partners/
{
  "bp_code": "BP001",
  "legal_name": "ABC Corp",
  "pan": "ABCDE1234F",  # Auto-validated and sanitized
  "gstin": "27ABCDE1234F1Z5",  # Auto-validated and sanitized
  "contact_phone": "+91 9876543210",  # Auto-validated and sanitized to "9876543210"
  "pincode": "110001",  # Auto-validated
  "bank_ifsc": "SBIN0001234"  # Auto-validated and sanitized
}
```

**Error Response** (if validation fails):

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "pan"],
      "msg": "Value error, Invalid PAN format: ABC123. Expected format: AAAAA9999A (e.g., ABCDE1234F)",
      "input": "ABC123"
    }
  ]
}
```

## Report Export Features

### Report Service (`services/report_service.py`)

Provides functionality to export data in three formats:
1. **CSV** - Comma-Separated Values
2. **Excel** - .xlsx format with styling
3. **PDF** - Formatted PDF reports with tables

#### Supported Export Endpoints

**Business Partners Export**:
- `GET /api/reports/business-partners/csv` - Export to CSV
- `GET /api/reports/business-partners/excel` - Export to Excel
- `GET /api/reports/business-partners/pdf` - Export to PDF

**Sales Contracts Export**:
- `GET /api/reports/sales-contracts/csv` - Export to CSV
- `GET /api/reports/sales-contracts/excel` - Export to Excel
- `GET /api/reports/sales-contracts/pdf` - Export to PDF

**Invoices Export**:
- `GET /api/reports/invoices/csv` - Export to CSV
- `GET /api/reports/invoices/excel` - Export to Excel
- `GET /api/reports/invoices/pdf` - Export to PDF

### Export Examples

#### 1. CSV Export

```bash
# Export all active business partners to CSV
curl -O "http://localhost:8080/api/reports/business-partners/csv?bp_status=ACTIVE"

# Download: business_partners_20250109_143000.csv
```

**CSV Output**:
```csv
"BP Code","Legal Name","Organization","Business Type","Status","Contact Person","Email","Phone"
"BP001","ABC Corp","ABC Org","BUYER","ACTIVE","John Doe","john@abc.com","9876543210"
"BP002","XYZ Ltd","XYZ Org","SELLER","ACTIVE","Jane Smith","jane@xyz.com","9876543211"
```

#### 2. Excel Export

```bash
# Export sales contracts to Excel
curl -O "http://localhost:8080/api/reports/sales-contracts/excel"

# Download: sales_contracts_20250109_143000.xlsx
```

**Excel Features**:
- ✅ Formatted header row (blue background, white text, bold)
- ✅ Auto-adjusted column widths
- ✅ Proper data type handling (dates, numbers)
- ✅ Named sheets ("Business Partners", "Sales Contracts", etc.)

#### 3. PDF Export

```bash
# Export invoices to PDF
curl -O "http://localhost:8080/api/reports/invoices/pdf?invoice_status=paid"

# Download: invoices_20250109_143000.pdf
```

**PDF Features**:
- ✅ Report title and metadata (generation date, record count)
- ✅ Formatted table with headers
- ✅ Alternating row colors for readability
- ✅ Grid lines
- ✅ Professional styling

### Filtering Options

All export endpoints support filtering:

**Business Partners**:
- `business_type`: BUYER, SELLER, BOTH, AGENT
- `bp_status`: ACTIVE, INACTIVE, DRAFT, etc.

**Sales Contracts**:
- `contract_status`: Active, Completed, Disputed, etc.

**Invoices**:
- `invoice_status`: draft, sent, paid, overdue, etc.

### Example: Export with Filters

```bash
# Export only BUYER type business partners to Excel
curl -O "http://localhost:8080/api/reports/business-partners/excel?business_type=BUYER&bp_status=ACTIVE"

# Export only completed sales contracts to PDF
curl -O "http://localhost:8080/api/reports/sales-contracts/pdf?contract_status=Completed"

# Export only paid invoices to CSV
curl -O "http://localhost:8080/api/reports/invoices/csv?invoice_status=paid"
```

### Using Report Service Programmatically

```python
from services.report_service import ReportService

# Initialize service
report_service = ReportService(db)

# Get data
data = report_service.get_business_partners_data(filters={'status': 'ACTIVE'})

# Export to CSV
csv_content = report_service.export_to_csv(data)

# Export to Excel
excel_bytes = report_service.export_to_excel(data, sheet_name="Active Partners")

# Export to PDF
pdf_bytes = report_service.export_to_pdf(data, title="Active Business Partners")
```

## Dependencies

The following packages are required (added to `requirements.txt`):

```
openpyxl        # For Excel export
reportlab       # For PDF export
python-multipart  # For file upload support
```

Install with:
```bash
pip install -r requirements.txt
```

## Frontend Integration

### No Frontend Changes Required

This backend repository (`rnrltradehub-backend`) contains only the backend API. The frontend is in a separate repository (`rnrltradehub-frontend`).

**To use these features in the frontend:**

1. **Validation**: Automatic - the backend will return validation errors in the response
2. **Report Export**: Add download buttons/links that call the export endpoints

**Example Frontend Integration**:

```typescript
// Download business partners as Excel
const downloadExcel = () => {
  window.location.href = `${API_BASE_URL}/api/reports/business-partners/excel?bp_status=ACTIVE`;
};

// Download invoices as PDF
const downloadPDF = () => {
  window.location.href = `${API_BASE_URL}/api/reports/invoices/pdf?invoice_status=paid`;
};
```

## Error Handling

### Validation Errors

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "gstin"],
      "msg": "Value error, Invalid GSTIN format: 27ABC. Expected format: 99AAAAA9999A9Z9",
      "input": "27ABC"
    }
  ]
}
```

### Export Errors

If export libraries are not installed:

```json
{
  "detail": "openpyxl library is required for Excel export. Install with: pip install openpyxl"
}
```

## Testing Validation

```bash
# Test PAN validation (should fail)
curl -X POST http://localhost:8080/api/business-partners/ \
  -H "Content-Type: application/json" \
  -d '{
    "bp_code": "BP001",
    "legal_name": "Test Corp",
    "pan": "INVALID",
    "contact_phone": "9876543210",
    "contact_email": "test@example.com",
    ...
  }'

# Response: 422 Unprocessable Entity with validation error
```

## Summary

### What Was Added:

1. ✅ **Input Validation** (`validators.py`):
   - PAN format validation (AAAAA9999A)
   - GSTIN format validation (99AAAAA9999A9Z9)
   - Mobile number validation (Indian format)
   - Pincode validation (6 digits)
   - IFSC code validation (AAAA0999999)
   - Email validation (via Pydantic EmailStr)

2. ✅ **Report Export** (`services/report_service.py`, `routes_export.py`):
   - CSV export for all major entities
   - Excel export with professional formatting
   - PDF export with tables and styling
   - 9 export endpoints (3 formats × 3 entities)
   - Filtering support on all exports

3. ✅ **Dependencies** (`requirements.txt`):
   - Added openpyxl for Excel generation
   - Added reportlab for PDF generation
   - Added python-multipart for file uploads

4. ✅ **Documentation**:
   - This comprehensive guide (VALIDATION_AND_EXPORT.md)

### Frontend Impact:

**No changes needed in frontend code.** The backend validates automatically and provides export endpoints that the frontend can call via simple HTTP GET requests.
