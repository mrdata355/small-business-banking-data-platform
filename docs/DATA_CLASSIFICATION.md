# Data classification

Generated examples use four practical classifications.

| Classification | Examples | Handling |
|---|---|---|
| Internal | event ids, trace ids, source system | normal authenticated access |
| Confidential | account/application/business ids, product, transaction status | controlled business access |
| Restricted PII | name, email, phone, DOB, address | masking and least-privilege access |
| Highly Restricted | SSN/TIN/EIN equivalents | token only in this project; never raw values |

The repository contains generated values only.
