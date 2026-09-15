-- Unity Catalog namespace bootstrap. Replace catalog name per environment.
CREATE CATALOG IF NOT EXISTS oakbridge_dev;

CREATE SCHEMA IF NOT EXISTS oakbridge_dev.bronze_lending;
CREATE SCHEMA IF NOT EXISTS oakbridge_dev.bronze_customer;
CREATE SCHEMA IF NOT EXISTS oakbridge_dev.bronze_treasury;
CREATE SCHEMA IF NOT EXISTS oakbridge_dev.silver_lending;
CREATE SCHEMA IF NOT EXISTS oakbridge_dev.silver_customer;
CREATE SCHEMA IF NOT EXISTS oakbridge_dev.silver_risk;
CREATE SCHEMA IF NOT EXISTS oakbridge_dev.silver_treasury;
CREATE SCHEMA IF NOT EXISTS oakbridge_dev.gold_lending;
CREATE SCHEMA IF NOT EXISTS oakbridge_dev.gold_treasury;
CREATE SCHEMA IF NOT EXISTS oakbridge_dev.ops;
