# Seed Data Guide

## Overview

The `seed_data.py` script populates the RNRL TradeHub database with realistic sample data for development, testing, and demonstration purposes.

## Prerequisites

- Database should be initialized (tables created)
- Python dependencies installed (`pip install -r requirements.txt`)
- Database connection configured in `.env` file

## Running the Seed Script

```bash
python seed_data.py
```

## What Gets Created

### Master Data (Configuration)

#### Organizations (1)
- **RNRL Trading Company Pvt Ltd**
  - PAN: AAACR5555K
  - GSTIN: 27AAACR5555K1Z5
  - Location: Mumbai, Maharashtra

#### Financial Years (2)
- Previous year (2023-24) - Closed
- Current year (2024-25) - Active

#### Roles & Permissions (3 roles)
1. **Admin** - Full system access
   - All modules: Create, Read, Update, Delete, Approve, Share
2. **Sales** - Sales team access
   - Sales Contracts: Create, Read, Update, Share
   - Business Partners: Create, Read, Update, Share
   - Invoices/Payments: Read only
3. **Accounts** - Accounts team access
   - Invoices: Full access
   - Payments: Full access
   - Commissions: Full access
   - Contracts: Read and Approve only

#### Users (3)
| Name | Email | Password | Role |
|------|-------|----------|------|
| Admin User | admin@rnrl.com | admin123 | Admin |
| Sales Manager | sales@rnrl.com | sales123 | Sales |
| Accounts Manager | accounts@rnrl.com | accounts123 | Accounts |

#### GST Rates (4)
- 0% - Nil Rate (HSN: 0000)
- 5% - Cotton (HSN: 5201)
- 12% - Standard Rate (HSN: 5202)
- 18% - Services (HSN: 5203)

#### Locations (6)
- Mumbai, Maharashtra
- Nagpur, Maharashtra
- Ahmedabad, Gujarat
- Rajkot, Gujarat
- Ludhiana, Punjab
- Sirsa, Haryana

#### Commission Structures (4)
- Standard 2% - Percentage based
- Premium 3% - Percentage based
- Fixed ₹50 per bale - Per bale
- Fixed ₹75 per bale - Per bale

#### CCI Terms (1)
Standard CCI Terms 2024 with:
- Contract period: 90 days
- EMD payment: 7 days
- Cash discount: 2%
- Carrying charges: Tiered (0.5% for 30 days, 1% for 60 days)
- Late lifting charges: Tiered structure

#### Master Data Items (11)
- **Varieties**: Shankar-6, MCU-5, DCH-32
- **Trade Types**: Spot, Forward, Ready
- **Bargain Types**: Ex-Gin, Delivery
- **Quality Parameters**: Staple Length, Micronaire, Trash %

#### Structured Terms (8)
- **Payment Terms**: Immediate, 7 Days, 15 Days, 30 Days
- **Delivery Terms**: Immediate, 7 Days, 15 Days, 30 Days

### Transactional Data

#### Business Partners (4)

1. **ABC Textiles Pvt Ltd** (BP001)
   - Type: BUYER
   - Status: ACTIVE
   - Location: Ahmedabad, Gujarat
   - Contact: Rajesh Kumar

2. **XYZ Cotton Traders** (BP002)
   - Type: SELLER
   - Status: ACTIVE
   - Location: Rajkot, Gujarat
   - Contact: Suresh Patel

3. **PQR Trading Company** (BP003)
   - Type: BOTH (Buyer & Seller)
   - Status: ACTIVE
   - Location: Mumbai, Maharashtra
   - Contact: Amit Shah

4. **LMN Commission Agents** (AG001)
   - Type: AGENT
   - Status: ACTIVE
   - Location: Ludhiana, Punjab
   - Contact: Vikram Singh

#### Sales Contracts (5)

5 sales contracts are created with:
- Mix of Spot and Forward trades
- Varieties: Shankar-6, MCU-5, DCH-32
- Quantities: 100-300 bales
- Rates: ₹5,000-5,400 per bale
- Statuses: 3 Active, 2 Completed
- Includes quality specifications (staple length, micronaire, trash %)
- Agent commission included

#### Invoices (4)

4 invoices created for the contracts:
- 2 Paid invoices
- 1 Partially Paid invoice
- 1 Unpaid invoice
- Amounts include 5% GST

#### Payments (3)

3 payment records:
- 2 Full payments
- 1 Partial payment (50%)
- Method: Bank Transfer
- Linked to respective invoices

#### Commissions (3)

3 commission records for agent:
- 1 Paid commission
- 2 Due commissions
- Calculated at 2% of contract value
- Linked to contracts with agents

#### Disputes (1)

1 open dispute:
- Reason: Quality specifications not met
- Status: Open
- Linked to a contract
- Date raised: 5 days ago

### Compliance & System Data

#### Email Templates (2)
- Contract Created Notification
- Invoice Generated Notification

#### Data Retention Policies (3)
- Sales Contracts: 10 years retention
- Invoices: 10 years retention
- Payments: 7 years retention

## Testing the Data

After running the seed script, you can test the APIs:

```bash
# Start the server
python main.py

# Test endpoints
curl http://localhost:8080/api/business-partners/
curl http://localhost:8080/api/sales-contracts/
curl http://localhost:8080/api/invoices/
curl http://localhost:8080/api/payments/
curl http://localhost:8080/api/commissions/
curl http://localhost:8080/api/disputes/
curl http://localhost:8080/api/users/
curl http://localhost:8080/api/roles/
curl http://localhost:8080/api/gst-rates/
curl http://localhost:8080/api/locations/
```

## Accessing the API Documentation

Once the server is running:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Re-running the Seed Script

**Warning**: The seed script will fail if data already exists (due to unique constraints). To re-run:

```bash
# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE rnrltradehub;"
sudo -u postgres psql -c "CREATE DATABASE rnrltradehub;"
sudo -u postgres psql -d rnrltradehub -c "GRANT ALL ON SCHEMA public TO rnrluser;"

# Run the application to create tables
python main.py &
sleep 5
pkill -f "python main.py"

# Run seed script
python seed_data.py
```

## Customizing Sample Data

You can modify the seed script to:
- Add more business partners
- Create additional contracts
- Add different varieties or locations
- Change commission rates
- Add more users and roles

Simply edit the `seed_data.py` file and modify the data in the respective functions.

## Data Summary

After seeding, the database contains:
- **1** Organization
- **2** Financial Years
- **3** Roles with granular permissions
- **3** Users (different roles)
- **4** Business Partners
- **5** Sales Contracts
- **4** Invoices
- **3** Payments
- **3** Commissions
- **1** Dispute
- **4** GST Rates
- **6** Locations
- **4** Commission Structures
- **1** CCI Term configuration
- **11** Master Data Items
- **8** Structured Terms
- **4** System Settings
- **2** Email Templates
- **3** Data Retention Policies

Total: **60+ records** across all tables with proper relationships!

## Next Steps

After seeding:
1. Login with any of the test user credentials
2. Explore the API using Swagger UI
3. Test CRUD operations on different entities
4. Verify business logic and validations
5. Test role-based access control
6. Explore compliance and GDPR features
