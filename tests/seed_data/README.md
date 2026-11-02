# Seed data — 10 PME tenants

Deterministic fixtures for multi-tenant testing: **10 PME admins**, each owning
**100 customers** and **50 suppliers**.

| File | Rows | Content |
|---|---|---|
| `pme_admins.csv` | 10 | One company + one `PME-Admin` user per row |
| `customers.csv` | 1000 | 100 per admin (600 `company`, 400 `prive`) |
| `suppliers.csv` | 500 | 50 per admin |

Column names match the Mongo documents written by `CustomerModel`,
`SupplierModel` and `UserModel`, so a loader can pass a row straight to
`.create()` after removing the owner column.

## Join key

`customers.csv` and `suppliers.csv` carry an **extra leading column**,
`pme_admin_email`, pointing at the owning row in `pme_admins.csv`. It is not a
model field:

```python
row.pop('pme_admin_email')   # then add company_id
```

Customer and supplier rows must receive a `company_id` (ObjectId) taken from the
tenant's company document — the CSV deliberately contains no ObjectIds.

## Passwords

Passwords in `pme_admins.csv` are **plain text** (`Pme@2027!demo` … `Pme@2036!demo`,
one per tenant). Hash them at import time; never store them as-is:

```python
bcrypt.generate_password_hash(row['password']).decode('utf-8')
```

## Loading with the app's own bulk upload

`/web/customers/bulk-upload` and `/web/suppliers/bulk-upload` already accept CSV
and derive the tenant from the logged-in session. Their header map reads
`type, name, contact, email, phone, address, city, ice/ICE, rc/RC,
paiement_terms / payment_terms`, and unknown headers are ignored — so a filtered
slice uploads directly once the owner column is removed:

```bash
# one tenant's customers, owner column removed -> header + 100 rows
python -c "import csv;r=list(csv.DictReader(open('customers.csv',encoding='utf-8')));o=[{k:v for k,v in x.items() if k!='pme_admin_email'} for x in r if x['pme_admin_email']=='youssef.amrani@atlas-distribution.ma'];w=csv.DictWriter(open('atlas-customers.csv','w',encoding='utf-8',newline=''),fieldnames=list(o[0]));w.writeheader();w.writerows(o)"
```

## Regenerating

```bash
python tests/seed_data/_generate.py
```

Fixed seeds (`random.seed(20261102)` plus a per-tenant seed) make the output
stable across runs, so diffs stay meaningful. Counts, name pools and tenants all
live in `_generate.py`.
