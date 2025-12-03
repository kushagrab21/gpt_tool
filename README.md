# CA Super Tool

Unified Accounting Reasoning Engine (UARE) for CA-Auto v1.0

## Overview

The CA Super Tool is a full-stack Python application that provides a unified API for various accounting and tax-related tasks. It uses a dispatcher-based architecture to route tasks to specialized engines through the UARE core pipeline.

## Features

- Single API endpoint: `POST /api/ca_super_tool`
- **UARE Core Pipeline**: Normalization → Fractal Expansion → Invariant Enforcement → Dispatch
- Dispatcher-based architecture for task routing
- Fractal expansion and invariant enforcement layers
- Modular engine design for easy expansion
- Clean, documented codebase
- Deterministic capsule generation for audit trails

## Project Structure

```
ca_super_tool/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── Dockerfile             # Docker configuration for deployment
├── render.yaml            # Render.com deployment blueprint
├── start.sh              # Production start script
├── engine/                # Engine modules
│   ├── __init__.py
│   ├── dispatcher.py      # Task dispatcher
│   ├── normalize.py       # Input normalization
│   ├── fractal.py         # Fractal expansion
│   ├── invariants.py      # Invariant enforcement
│   ├── gst_reconcile.py   # GST reconciliation engine
│   ├── tds_classifier.py  # TDS classification engine
│   ├── sales_invoice.py   # Sales invoice engine
│   ├── tax_audit.py       # Tax audit engine
│   ├── auto_entries.py    # Auto entries engine
│   └── inventory.py       # Inventory engine
├── schemas/               # JSON schemas
│   ├── __init__.py
│   └── tool_schema.json   # Tool schema definition
└── tests/                 # Test files
    ├── __init__.py
    ├── sample_inputs/     # Sample test inputs
    └── sample_requests.py # Sample API requests
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI) will be available at `http://localhost:8000/docs`

## Deploying to Render

The CA Super Tool can be deployed to Render.com for free using Docker.

### Prerequisites

1. Push this project to a GitHub repository
2. Have a Render.com account (free tier available)

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to https://dashboard.render.com
   - Click "New → Web Service"
   - Select your GitHub repository
   - Configure the service:
     - **Name**: `ca-super-tool` (or your preferred name)
     - **Runtime**: Docker
     - **Dockerfile Path**: `/Dockerfile`
     - **Branch**: `main`
     - **Plan**: Free
     - **Health Check Path**: `/docs`
   - Add environment variables (optional, defaults are set):
     - `PYTHONUNBUFFERED=1`
     - `UVICORN_PORT=8000`
   - Click "Create Web Service"

3. **Wait for Deployment**
   - Render will build and deploy your service
   - The first deployment may take 5-10 minutes
   - You'll see the deployment logs in real-time

### After Deployment

Once deployed, your API will be available at:
- **API Endpoint**: `https://<your-service-name>.onrender.com/api/ca_super_tool`
- **Swagger UI**: `https://<your-service-name>.onrender.com/docs`
- **Health Check**: `https://<your-service-name>.onrender.com/docs` (used by Render)

### Using Render Blueprint (Alternative)

If you prefer using the `render.yaml` blueprint:

1. Push your code with `render.yaml` to GitHub
2. Go to Render Dashboard → "New → Blueprint"
3. Select your repository
4. Render will automatically detect and use `render.yaml`
5. Click "Apply" to deploy

### Notes

- **Free Tier**: Render free tier includes:
  - 750 hours/month of runtime
  - Services spin down after 15 minutes of inactivity
  - First request after spin-down may take 30-60 seconds
- **Auto-Deploy**: Services auto-deploy on every push to the connected branch
- **Logs**: Access deployment and runtime logs from the Render dashboard
- **Environment Variables**: Can be set in the Render dashboard or via `render.yaml`

### Local Testing with Docker

You can test the Docker setup locally:

```bash
# Build the image
docker build -t ca-super-tool .

# Run the container
docker run -p 8000:8000 ca-super-tool

# Test the API
curl http://localhost:8000/docs
```

## UARE Core Pipeline

Every request passes through the UARE (Unified Accounting Reasoning Engine) core pipeline:

### Layer 0: Normalization
- Ensures keys are strings
- Converts numbers to float for consistency
- Converts dates to ISO format
- Strips whitespace in strings
- Removes null/None values

### Layer 1: Fractal Expansion
Creates a three-level structure:
- **micro**: Original normalized data (unchanged)
- **meso**: Intermediate-level summary (placeholder for future expansion)
- **macro**: High-level summary (placeholder for future expansion)

### Layer 2: Invariant Enforcement
Runs four core invariant checks (IC1-IC4):
- **IC1**: micro exists
- **IC2**: micro/meso/macro keys exist
- **IC3**: no empty keys
- **IC4**: data types valid

### Layer 3: Dispatch
Routes the task to the appropriate specialized engine, passing `fractal['micro']` as input.

### Layer 4: Structured Response
Wraps the result with metadata including:
- Engine result
- Capsule hash (SHA256)
- Invariant status
- Fractal structure metadata

## API Usage

### Endpoint: `POST /api/ca_super_tool`

**Request Body:**
```json
{
  "task": "gst_reconcile_3b_books",
  "data": {
    "period": "2024-01",
    "gstin": "29ABCDE1234F1Z5",
    "books_data": {
      "total_sales": 1000000.00,
      "output_tax": 180000.00
    }
  },
  "settings": {
    "strict_mode": false,
    "tolerance": 0.01
  }
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "result": {
      "engine": "gst_reconcile_3b_books",
      "received": { ... }
    },
    "metadata": {
      "capsule": "sha256_hash_string",
      "invariants_passed": true,
      "invariant_report": {
        "ic1": { "passed": true, "message": "micro key exists" },
        "ic2": { "passed": true, "message": "All required keys exist" },
        "ic3": { "passed": true, "message": "No empty keys found" },
        "ic4": { "passed": true, "message": "All data types valid" }
      },
      "fractal_structure": {
        "has_micro": true,
        "has_meso": true,
        "has_macro": true
      }
    },
    "engine_version": "1.0.0"
  },
  "capsule": "sha256_hash_string"
}
```

## Supported Tasks

- `sales_invoice_prepare` - Prepare sales invoices
- `auto_gst_fetch_and_map` - Auto-fetch and map GST data
- `tds_liability` - Calculate TDS liability (see TDS Engine section below)
- `auto_entries` - Generate automatic journal entries (see Auto Entries Engine section below)
- `tax_audit` - Perform tax audit
- `gst_reconcile_2b_3b` - GST reconciliation (2B vs 3B)
- `gst_reconcile_3b_books` - GST reconciliation (3B vs books)
- `gst_reconcile_3b_r1` - GST reconciliation (3B vs R1)

## TDS Liability Engine

The TDS Liability Engine automatically classifies payments into TDS sections, applies thresholds, and computes TDS amounts.

### Features

- **Section Detection**: Automatically maps nature of payment to TDS section (194C, 194J, 194I, 194H, 194Q)
- **Threshold Checking**: Aggregates by party+section+FY and checks if threshold exceeded
- **Rate Calculation**: Applies appropriate TDS rates based on section and payee type
- **PAN Handling**: Applies higher rates when PAN is not available
- **Multi-level Output**: Returns micro (transaction-level), meso (party/section aggregates), and macro (summary) data

### Sample Request

```json
{
  "task": "tds_liability",
  "data": {
    "transactions": [
      {
        "txn_id": "TXN001",
        "date": "2024-04-15",
        "party_name": "ABC Services",
        "party_pan": "ABCDE1234F",
        "party_type": "RESIDENT",
        "nature_of_payment": "PROFESSIONAL_FEES",
        "amount": 50000.0,
        "is_pan_available": true,
        "is_individual_or_huf": false,
        "fy": "2024-25"
      },
      {
        "txn_id": "TXN002",
        "date": "2024-04-20",
        "party_name": "XYZ Contractors",
        "party_pan": "XYZAB5678G",
        "party_type": "RESIDENT",
        "nature_of_payment": "CONTRACT",
        "amount": 150000.0,
        "is_pan_available": true,
        "is_individual_or_huf": true,
        "fy": "2024-25"
      }
    ]
  },
  "settings": {
    "default_fy": "2024-25"
  }
}
```

### Response Structure

The engine returns:
- **micro**: Detailed transaction-level outputs with TDS calculations
- **meso**: Aggregates by party and by section
- **macro**: Overall summary with flags and totals

## Auto Journal Entry Engine

The Auto Journal Entry Engine generates journal entry suggestions from TDS and GST engine outputs, ready for import into Tally or other accounting systems.

### Features

- **TDS Entry Generation**: Creates journal entries from TDS liability calculations
- **GST Entry Generation**: Creates adjustment entries from GST reconciliation differences
- **Configurable Ledgers**: Supports custom ledger names via configuration
- **Entry Tagging**: Tags entries as "ENTRY_READY" or "REVIEW_REQUIRED"
- **Transaction Linking**: Links journal entries to underlying transaction IDs
- **Batch Suggestions**: Identifies small entries that can be batched

### Workflow

1. **Step 1**: Call TDS or GST engine to get liability/reconciliation results
2. **Step 2**: Feed the result into `auto_entries` to generate journal entries

### Sample Request (TDS → Auto Entries)

```json
{
  "task": "auto_entries",
  "data": {
    "source": "tds_liability",
    "payload": {
      "micro": {
        "transactions": [
          {
            "txn_id": "TXN001",
            "fy": "2024-25",
            "section": "194J",
            "party_pan": "ABCDE1234F",
            "party_name": "ABC Services",
            "gross_amount": 50000.0,
            "tds_amount": 5000.0
          }
        ]
      },
      "meso": {
        "by_party": [
          {
            "fy": "2024-25",
            "section": "194J",
            "party_pan": "ABCDE1234F",
            "party_name": "ABC Services",
            "total_gross": 50000.0,
            "total_tds": 5000.0,
            "txn_count": 1
          }
        ]
      }
    },
    "config": {
      "tds_payable_ledger": "TDS Payable",
      "tds_expense_ledger": "TDS Expense",
      "default_date": "2024-04-30",
      "entry_prefix": "AUTO"
    }
  },
  "settings": {}
}
```

### Response Structure

The engine returns:
- **entries**: List of journal entry suggestions with debit/credit accounts, amounts, narrations, and tags
- **summary**: Total entries, total amount, and breakdown by type
- **flags**: Warnings and suggestions (e.g., entries that can be batched, missing ledger configs)

### Entry Structure

Each journal entry includes:
- `entry_id`: Unique identifier (e.g., "AUTO-TDS-001")
- `date`: Entry date
- `entry_type`: "TDS", "GST", or "ADJUSTMENT"
- `debit_account`: Debit ledger name
- `credit_account`: Credit ledger name
- `amount`: Entry amount
- `narration`: Descriptive narration
- `tags`: Array of tags (e.g., ["AUTO", "ENTRY_READY", "TDS"])
- `linked_txn_ids`: Array of related transaction IDs
- `meta`: Additional metadata (FY, section, party details, etc.)

## Sales Invoice Engine

The Sales Invoice Engine prepares complete sales invoices with GST computation, classification, and mapping hints for GSTR-3B and GSTR-1.

### Features

- **GST Computation**: Automatically calculates CGST/SGST for intra-state and IGST for inter-state supplies
- **Invoice Classification**: Determines B2B vs B2C and INTRA vs INTER supply types
- **Line-level Tax**: Computes tax for each line item with discount handling
- **Rounding Support**: Configurable rounding modes (NEAREST, UP, DOWN)
- **GST Mapping**: Provides hints for GSTR-3B table mapping and GSTR-1 section classification
- **Validation Flags**: Automatic flags for missing GSTIN, exempt items, rounding adjustments

### Supply Type & Invoice Type

- **Supply Type**:
  - `INTRA`: Customer and seller are in the same state (CGST + SGST)
  - `INTER`: Customer and seller are in different states (IGST)

- **Invoice Type**:
  - `B2B`: Customer has GSTIN (business-to-business)
  - `B2C`: Customer does not have GSTIN (business-to-consumer)

### Sample Request

```json
{
  "task": "sales_invoice_prepare",
  "data": {
    "customer": {
      "name": "ABC Pvt Ltd",
      "gstin": "07AAAAA0000A1Z5",
      "state_code": "07",
      "place_of_supply": "07",
      "billing_address": "123 Main St",
      "shipping_address": "123 Main St"
    },
    "seller": {
      "gstin": "09BBBBB0000B1Z6",
      "state_code": "09",
      "legal_name": "XYZ Traders"
    },
    "lines": [
      {
        "sku": "ITEM001",
        "description": "Widget",
        "quantity": 10,
        "unit_price": 100.0,
        "discount": 0.0,
        "hsn": "8409",
        "tax_rate": 18.0,
        "is_exempt": false
      }
    ],
    "config": {
      "default_tax_rate": 18.0,
      "rounding_mode": "NEAREST",
      "invoice_prefix": "INV",
      "default_currency": "INR",
      "invoice_date": "2024-04-30",
      "invoice_number_seed": 1
    }
  },
  "settings": {}
}
```

### Response Structure

The engine returns:
- **invoice**: Complete invoice structure with:
  - Invoice metadata (number, date, currency, supply type, invoice type)
  - Customer and seller details
  - Line items with computed tax values
  - Totals (taxable, IGST, CGST, SGST, CESS, invoice value)
  - GST mapping hints for 3B and R1
- **flags**: Warnings and information (missing GSTIN, exempt items, rounding adjustments, etc.)

### Invoice Structure

Each invoice includes:
- `invoice_number`: Generated or provided invoice number
- `invoice_date`: Invoice date
- `currency`: Currency code (default: INR)
- `supply_type`: "INTRA" or "INTER"
- `invoice_type`: "B2B" or "B2C"
- `customer`: Customer details
- `seller`: Seller details
- `lines`: Array of line items with computed values
- `totals`: Invoice totals with rounding adjustment
- `gst_mapping`: Hints for GSTR-3B (table 3.1(a)) and GSTR-1 (B2B/B2C section)

### Line Item Structure

Each line item includes:
- `line_no`: Line number
- `sku`: SKU code
- `description`: Item description
- `quantity`: Quantity
- `unit_price`: Unit price
- `discount`: Discount amount
- `taxable_value`: Taxable value after discount
- `tax_rate`: Tax rate in percent
- `igst`: IGST amount
- `cgst`: CGST amount
- `sgst`: SGST amount
- `cess`: CESS amount
- `hsn`: HSN code

## Development

This is the initial scaffolding version. All engines are placeholders and will be implemented iteratively.

## License

Proprietary - CA-Auto v1.0

