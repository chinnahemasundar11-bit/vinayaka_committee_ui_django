-- ==============================================================================
-- VINAYAKA YOUTH COMMITTEE - FESTIVAL FUNDS MANAGEMENT SYSTEM
-- PostgreSQL DDL (CREATE TABLE) & DML (INSERT INTO) Master Script for pgAdmin
-- Target Database: Event_finance_DEMO
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 1. Standard Django Auth User & Session Tables
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auth_user (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS django_session (
    session_key VARCHAR(40) NOT NULL PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS django_session_expire_date_a5c62663 ON django_session (expire_date);
CREATE INDEX IF NOT EXISTS django_session_session_key_c0b09045_like ON django_session (session_key varchar_pattern_ops);

-- ------------------------------------------------------------------------------
-- 2. Administration Master Tables
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS administration_site_setting (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'GENERAL',
    description VARCHAR(255) NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS administration_lookup_type (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS administration_lookup_value (
    id SERIAL PRIMARY KEY,
    lookup_type_id INT NOT NULL REFERENCES administration_lookup_type(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    value VARCHAR(150) NOT NULL,
    display_order INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    CONSTRAINT administration_lookup_value_type_code_uniq UNIQUE (lookup_type_id, code)
);

CREATE TABLE IF NOT EXISTS administration_financial_year (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS administration_fund_source (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    receipt_prefix VARCHAR(20) NOT NULL DEFAULT 'RCPT-',
    description TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS administration_expense_category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    requires_approval BOOLEAN NOT NULL DEFAULT FALSE,
    approval_threshold NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS administration_payment_method (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    requires_ref_no BOOLEAN NOT NULL DEFAULT FALSE,
    icon_name VARCHAR(50) NOT NULL DEFAULT 'bi-credit-card',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------------------------
-- 3. Domain Models (Members, Events, Funds, Expenses, Audit Trail)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS members_member (
    id SERIAL PRIMARY KEY,
    member_id VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    mobile_number VARCHAR(15) NOT NULL UNIQUE,
    committee_position VARCHAR(100) NOT NULL,
    system_role VARCHAR(100) NOT NULL DEFAULT 'Committee Member',
    joining_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    address TEXT NULL,
    photo_url VARCHAR(255) NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS events_event (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    venue_location VARCHAR(200) NOT NULL,
    event_date DATE NOT NULL,
    start_time TIME NULL,
    end_time TIME NULL,
    allocated_budget NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    actual_spend NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'Planned',
    description TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS funds_fund_receipt (
    id SERIAL PRIMARY KEY,
    receipt_number VARCHAR(50) NOT NULL UNIQUE,
    donor_name VARCHAR(150) NOT NULL,
    donor_phone VARCHAR(15) NULL,
    amount NUMERIC(12, 2) NOT NULL,
    date_received DATE NOT NULL,
    fund_source_id INT NOT NULL REFERENCES administration_fund_source(id) ON DELETE RESTRICT,
    payment_method_id INT NOT NULL REFERENCES administration_payment_method(id) ON DELETE RESTRICT,
    reference_number VARCHAR(100) NULL,
    remarks TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS expenses_expense_voucher (
    id SERIAL PRIMARY KEY,
    voucher_number VARCHAR(50) NOT NULL UNIQUE,
    vendor_name VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    amount_spent NUMERIC(12, 2) NOT NULL,
    expense_date DATE NOT NULL,
    category_id INT NOT NULL REFERENCES administration_expense_category(id) ON DELETE RESTRICT,
    payment_method_id INT NOT NULL REFERENCES administration_payment_method(id) ON DELETE RESTRICT,
    status VARCHAR(50) NOT NULL DEFAULT 'Approved',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    updated_by_id INT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    deleted_by_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INT NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    object_id VARCHAR(50) NOT NULL,
    details TEXT NULL,
    ip_address INET NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- DML INSERT COMMANDS (SEED DATA)
-- ==============================================================================

-- 1. Default Admin Superuser (Username: 9876543210 / Password: admin123)
INSERT INTO auth_user (id, username, password, first_name, last_name, email, is_superuser, is_staff, is_active, date_joined)
VALUES (1, '9876543210', 'pbkdf2_sha256$1500000$Aa4HyOC3owIvGBTwNo4SlB$YJpi2aCHh3S74uM/aA0AbwG7cdJfxMOi9h/dVCpqWGo=', 'Committee', 'Admin', 'admin@vinayaka.org', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP)
ON CONFLICT (username) DO NOTHING;

-- 2. Site Settings
INSERT INTO administration_site_setting (key, value, category, description, created_at, updated_at, is_deleted)
VALUES 
    ('SITE_NAME', 'Vinayaka Youth Committee', 'GENERAL', 'Main title displayed on header', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    ('SITE_SLOGAN', 'Ganesh Utsav Finance Portal', 'GENERAL', 'Subtitle tagline', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    ('CURRENCY_SYMBOL', '₹', 'FINANCIAL', 'Currency symbol used across UI', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    ('THEME_COLOR', '#8b1e24', 'THEME', 'Primary brand color', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 3. Lookup Types
INSERT INTO administration_lookup_type (id, code, name, description, created_at, updated_at, is_deleted)
VALUES 
    (1, 'COMMITTEE_POSITION', 'Committee Positions', 'Designations held by youth members', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'SYSTEM_ROLE', 'System Access Roles', 'Portal permission roles', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (code) DO NOTHING;

-- 4. Lookup Values
INSERT INTO administration_lookup_value (lookup_type_id, code, value, display_order, is_active, created_at, updated_at, is_deleted)
VALUES 
    (1, 'POS_PRESIDENT', 'President', 1, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (1, 'POS_VICE_PRESIDENT', 'Vice President', 2, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (1, 'POS_SECRETARY', 'Secretary', 3, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (1, 'POS_TREASURER', 'Chief Treasurer', 4, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (1, 'POS_JOINT_TREASURER', 'Joint Treasurer', 5, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (1, 'POS_EVENT_COORD', 'Event Coordinator', 6, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'ROLE_SUPER_ADMIN', 'Super Admin', 1, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'ROLE_TREASURER', 'Treasurer', 2, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'ROLE_MEMBER', 'Committee Member', 3, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'ROLE_AUDITOR', 'Viewer / Public Auditor', 4, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (lookup_type_id, code) DO NOTHING;

-- 5. Financial Years
INSERT INTO administration_financial_year (id, name, start_date, end_date, is_active, is_locked, created_at, updated_at, is_deleted)
VALUES 
    (1, 'FY 2026 - 2027', '2026-04-01', '2027-03-31', TRUE, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'FY 2025 - 2026', '2025-04-01', '2026-03-31', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT DO NOTHING;

-- 6. Fund Sources
INSERT INTO administration_fund_source (id, name, code, receipt_prefix, description, is_active, created_at, updated_at, is_deleted)
VALUES 
    (1, 'Youth Contribution', 'SRC_YOUTH', 'RCPT-YTH-', 'Annual fee collected from youth members', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'Village Household Contribution', 'SRC_VILLAGE', 'RCPT-VLG-', 'Door-to-door village subscriptions', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (3, 'Outside Donors & Well Wishers', 'SRC_DONOR', 'RCPT-DNR-', 'Sponsors and external devotees', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (4, 'Laddu Auction & Prasadam', 'SRC_AUCTION', 'RCPT-AUC-', 'Grand Laddu auction funds', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (code) DO NOTHING;

-- 7. Expense Categories
INSERT INTO administration_expense_category (id, name, code, requires_approval, approval_threshold, is_active, created_at, updated_at, is_deleted)
VALUES 
    (1, 'Idol & Sthapana Pooja', 'EXP_IDOL', TRUE, 10000.00, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'Decorations & Mandapam Set', 'EXP_DECOR', TRUE, 5000.00, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (3, 'Annasantharpana / Prasadam Food', 'EXP_FOOD', TRUE, 15000.00, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (4, 'Lighting & Sound Systems', 'EXP_LIGHTING', FALSE, 0.00, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (5, 'Nimajjanam Procession & Band', 'EXP_NIMAJJANAM', TRUE, 10000.00, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (code) DO NOTHING;

-- 8. Payment Methods
INSERT INTO administration_payment_method (id, name, code, requires_ref_no, icon_name, is_active, created_at, updated_at, is_deleted)
VALUES 
    (1, 'Cash Payment', 'PAY_CASH', FALSE, 'bi-cash-stack', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'UPI / PhonePe / GooglePay', 'PAY_UPI', TRUE, 'bi-qr-code', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (3, 'Bank Transfer (NEFT/IMPS)', 'PAY_BANK', TRUE, 'bi-bank', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (4, 'Cheque', 'PAY_CHEQUE', TRUE, 'bi-card-heading', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (code) DO NOTHING;

-- 9. Committee Members
INSERT INTO members_member (id, member_id, full_name, mobile_number, committee_position, system_role, joining_date, status, created_at, updated_at, is_deleted)
VALUES 
    (1, 'MBR-2026-001', 'K. V. Ramesh', '9876543210', 'President', 'Super Admin', '2026-01-01', 'Active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'MBR-2026-002', 'M. Suresh Kumar', '9876501234', 'Chief Treasurer', 'Treasurer', '2026-01-01', 'Active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (3, 'MBR-2026-003', 'P. Anjaneyulu', '9876512345', 'Secretary', 'Committee Member', '2026-01-15', 'Active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (member_id) DO NOTHING;

-- 10. Festival Events
INSERT INTO events_event (id, event_id, title, venue_location, event_date, start_time, end_time, allocated_budget, actual_spend, status, description, created_at, updated_at, is_deleted)
VALUES 
    (1, 'EVT-2026-001', 'Ganesh Idol Installation & Sthapana', 'Main Temple Mandapam', '2026-08-20', '08:30:00', '12:30:00', 25000.00, 22500.00, 'Planned', 'Grand installation of Ganesha Idol with Veda Mantram pooja', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'EVT-2026-002', 'Grand Annasantharpana (Mahaprasadam)', 'Community Dining Hall', '2026-08-24', '12:00:00', '16:00:00', 45000.00, 42000.00, 'Planned', 'Free community feast organized for over 2,500 devotees', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (event_id) DO NOTHING;

-- 11. Fund Receipts
INSERT INTO funds_fund_receipt (id, receipt_number, donor_name, donor_phone, amount, date_received, fund_source_id, payment_method_id, reference_number, remarks, created_at, updated_at, is_deleted)
VALUES 
    (1, 'RCPT-2026-001', 'Ramesh Kumar', '9876543210', 10000.00, '2026-08-13', 1, 2, 'UPI-88776655', 'Annual Youth Membership Contribution', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'RCPT-2026-002', 'Village Elders', '9876599999', 25000.00, '2026-08-12', 2, 1, '', 'Main Street Village Collection', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (3, 'RCPT-2026-003', 'Suresh Rao', '9876501234', 15000.00, '2026-08-10', 3, 3, 'TXN-998877', 'Special Mahaprasadam Donation', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (receipt_number) DO NOTHING;

-- 12. Expense Vouchers
INSERT INTO expenses_expense_voucher (id, voucher_number, vendor_name, description, amount_spent, expense_date, category_id, payment_method_id, status, created_at, updated_at, is_deleted)
VALUES 
    (1, 'EXP-2026-001', 'Royal Decorators', 'Stage & Mandapam Decoration Flowers & Cloth', 8500.00, '2026-08-12', 2, 1, 'Approved', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (2, 'EXP-2026-002', 'ABC Electricals', '500W Sound System & Festival LED Lights', 12000.00, '2026-08-11', 4, 2, 'Approved', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE),
    (3, 'EXP-2026-003', 'Sri Laxmi Mart', 'Grocery Purchase for Mahaprasadam Cooking', 35000.00, '2026-08-09', 3, 1, 'Approved', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE)
ON CONFLICT (voucher_number) DO NOTHING;

-- 13. Audit Log Initial Entry
INSERT INTO audit_audit_log (user_id, action, model_name, object_id, details, ip_address, timestamp)
VALUES (1, 'SYSTEM_INIT', 'Database', 'SYSTEM', 'Initial PostgreSQL schema and seed data created successfully', '127.0.0.1', CURRENT_TIMESTAMP);

COMMIT;
