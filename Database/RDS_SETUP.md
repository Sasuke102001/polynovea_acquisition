# AWS RDS Setup — Polynovea Module 2

## Instance Spec (from handover)
- Engine: PostgreSQL 16
- Class: db.t3.micro (Single-AZ, no Multi-AZ)
- Storage: 15 GB gp2
- Region: ap-south-1 (Mumbai)
- Publicly Accessible: NO
- VPC: default

---

## Step 1 — Create the RDS Instance

1. Go to → https://console.aws.amazon.com/rds
2. Click **Create database**
3. Choose:
   - Engine: **PostgreSQL**
   - Version: **16.x** (latest 16)
   - Template: **Free tier** (auto-selects db.t3.micro)
4. Settings:
   - DB instance identifier: `polynovea-module2`
   - Master username: `polynovea_admin`
   - Master password: *(choose a strong password, save it)*
5. Instance configuration:
   - DB instance class: **db.t3.micro** — do NOT upgrade
6. Storage:
   - Allocated storage: **15 GB**
   - Storage autoscaling: **disabled** (avoids surprise costs)
7. Connectivity:
   - VPC: **Default VPC**
   - Subnet group: **default**
   - Public access: **No**
   - VPC security group: Create new → name it `polynovea-rds-sg`
8. Database options:
   - Initial database name: `polynovea_module2`
9. Click **Create database** — takes ~5 minutes

---

## Step 2 — Security Group (Allow Your Machine In)

1. Go to → EC2 → Security Groups → find `polynovea-rds-sg`
2. Edit inbound rules → Add rule:
   - Type: **PostgreSQL**
   - Port: **5432**
   - Source: **My IP** (your current IP)
3. Save rules

> If running the pipeline from a server/EC2 later: add that instance's security group as a source instead of your IP.

---

## Step 3 — Get Your Endpoint

1. Go to RDS → Databases → `polynovea-module2`
2. Copy the **Endpoint** — looks like:
   `polynovea-module2.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com`

---

## Step 4 — Set Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```
PG_HOST=polynovea-module2.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com
PG_PORT=5432
PG_DB=polynovea_module2
PG_USER=polynovea_admin
PG_PASSWORD=your_password
```

Load the env file before running scripts:

**Windows (PowerShell):**
```powershell
Get-Content .\.env | ForEach-Object {
    if ($_ -match '^([^#][^=]*)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}
```

**Mac/Linux (bash):**
```bash
export $(grep -v '^#' .env | xargs)
```

---

## Step 5 — Install psycopg2

```bash
pip install psycopg2-binary python-dotenv
```

---

## Step 6 — Run Schema (001_init_schema.sql)

Connect with psql and run the schema file:

```bash
psql -h $PG_HOST -U polynovea_admin -d polynovea_module2 -f sql/001_init_schema.sql
```

Or from PowerShell:
```powershell
psql -h $env:PG_HOST -U polynovea_admin -d polynovea_module2 -f sql\001_init_schema.sql
```

Expected output: a series of `CREATE TABLE` and `CREATE INDEX` lines, no errors.

---

## Step 7 — Run the Data Pipeline

From the `Database/` folder:

```bash
# Load everything (takes ~5-10 min for 6,007 venues)
python scripts/run_pipeline.py

# If something fails at step 4, resume from there:
python scripts/run_pipeline.py --from 4

# Test a single script:
python scripts/run_pipeline.py --only 2
```

Expected final output:
```
========================================================
  ALL SCRIPTS COMPLETE
========================================================
  Venues loaded   : ~6,007
  Patterns        : ~150-200 across 4 cities
  Interventions   : ~20,000+
  Similarity pairs: ~100,000+
  Survey responses: ~45
========================================================
```

---

## Step 8 — Apply for AWS Activate Founders ($1,000)

Do this immediately — it takes 1-2 weeks to approve:
https://aws.amazon.com/activate/founders/

Requirements: have a startup, use AWS. You qualify.
This gives $1,000 in credits on top of your existing free tier.

---

## Step 9 — Set Billing Alert

1. Go to → AWS Billing → Budgets
2. Create budget → Monthly cost budget
3. Set threshold: **$50/month**
4. Alert to your email

With db.t3.micro + private VPC + light usage, you should stay under $10/month.

---

## Estimated Costs (ap-south-1)

| Item | Cost |
|------|------|
| db.t3.micro (720 hrs/month) | ~$13/month |
| Storage 15 GB gp2 | ~$1.73/month |
| Data transfer (internal) | $0 |
| Public IPv4 (disabled) | $0 |
| **Total** | **~$15/month** |

With free tier (first 12 months) + Activate credits: effectively $0 until mid-2027.
