"""Synthetic business data. Fictional — any resemblance to real entities is
coincidental. Stable IDs so demos and screenshots reproduce exactly."""

CUSTOMERS = [
    {"id": "CUST-1001", "name": "Acme Robotics", "email": "ops@acme-robotics.example",
     "tier": "enterprise", "region": "us-east", "lifetime_value": 184000, "created_at": "2024-02-11"},
    {"id": "CUST-1002", "name": "Bluefin Logistics", "email": "support@bluefin.example",
     "tier": "growth", "region": "eu-west", "lifetime_value": 52000, "created_at": "2024-05-03"},
    {"id": "CUST-1003", "name": "Cedar Health", "email": "it@cedarhealth.example",
     "tier": "enterprise", "region": "us-west", "lifetime_value": 220500, "created_at": "2023-11-19"},
    {"id": "CUST-1004", "name": "Dalton Media", "email": "hello@daltonmedia.example",
     "tier": "starter", "region": "us-east", "lifetime_value": 8600, "created_at": "2025-01-22"},
    {"id": "CUST-1005", "name": "Everpeak Outdoors", "email": "care@everpeak.example",
     "tier": "growth", "region": "apac", "lifetime_value": 41200, "created_at": "2024-08-30"},
]

ORDERS = [
    {"id": "ORD-5001", "customer_id": "CUST-1001", "status": "shipped", "total": 12400,
     "items": ["Arm controller x4", "Service plan"], "created_at": "2025-09-14"},
    {"id": "ORD-5002", "customer_id": "CUST-1002", "status": "processing", "total": 3100,
     "items": ["Route optimizer seat x10"], "created_at": "2025-10-02"},
    {"id": "ORD-5003", "customer_id": "CUST-1003", "status": "delayed", "total": 58000,
     "items": ["Compliance module", "Onboarding"], "created_at": "2025-10-19"},
    {"id": "ORD-5004", "customer_id": "CUST-1001", "status": "delivered", "total": 900,
     "items": ["Spare sensor kit"], "created_at": "2025-08-01"},
    {"id": "ORD-5005", "customer_id": "CUST-1005", "status": "cancelled", "total": 2200,
     "items": ["Trail app annual"], "created_at": "2025-07-11"},
]

TICKETS = [
    {"id": "TCK-9001", "customer_id": "CUST-1003", "subject": "Deployment delayed past SLA",
     "priority": "high", "status": "open", "created_at": "2025-10-21"},
    {"id": "TCK-9002", "customer_id": "CUST-1002", "subject": "Billing discrepancy on renewal",
     "priority": "normal", "status": "open", "created_at": "2025-10-18"},
]

CRM = [
    {"customer_id": "CUST-1001", "stage": "expansion", "notes": "Evaluating second-site rollout.",
     "owner": "A. Rivera", "updated_at": "2025-10-10"},
    {"customer_id": "CUST-1002", "stage": "renewal", "notes": "Renewal in 30 days; billing issue open.",
     "owner": "J. Okafor", "updated_at": "2025-10-18"},
    {"customer_id": "CUST-1003", "stage": "at_risk", "notes": "SLA breach; exec escalation.",
     "owner": "A. Rivera", "updated_at": "2025-10-21"},
    {"customer_id": "CUST-1004", "stage": "onboarding", "notes": "First 30 days.",
     "owner": "M. Chen", "updated_at": "2025-02-01"},
    {"customer_id": "CUST-1005", "stage": "renewal", "notes": "Downgrade risk after cancellation.",
     "owner": "J. Okafor", "updated_at": "2025-09-01"},
]
