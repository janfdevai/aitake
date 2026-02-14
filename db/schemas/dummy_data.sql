-- =============================================================================
-- MVP DUMMY DATA: FastOrder Simplified Version
-- =============================================================================

-- 1. MANAGERS
INSERT INTO managers (manager_id, gcp_uid, full_name, email) VALUES
('a0000000-0000-0000-0000-000000000001', 'gcp_admin_01', 'Alice Admin', 'alice@fastorder.com'),
('a0000000-0000-0000-0000-000000000002', 'gcp_mgr_01', 'Bob Burger', 'bob@burgers.com');

-- 2. BUSINESSES
INSERT INTO businesses (business_id, name, whatsapp_phone_number, address) VALUES
('b0000000-0000-0000-0000-000000000001', 'Burger Kingpin', '+15550100', '123 Fast Lane, Metro City');

-- Link Manager
INSERT INTO business_managers (business_id, manager_id) VALUES
('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002');

-- 3. CATALOG
INSERT INTO menu_items (item_id, business_id, name, price, description) VALUES
('d0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 'Classic Smash', 12.00, 'Juicy beef patty with cheese'),
('d0000000-0000-0000-0000-000000000002', 'b0000000-0000-0000-0000-000000000001', 'Cajun Fries', 5.00, 'Spicy crispy fries');

-- 4. CLIENTS
INSERT INTO clients (client_id, business_id, wa_id, full_name, phone_number) VALUES
('55000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', '1001', 'Nick Newbie', '+11001'),
('55000000-0000-0000-0000-000000000002', 'b0000000-0000-0000-0000-000000000001', '1002', 'Carl Curious', '+11002');

-- 5. ORDERS
-- Active Order
INSERT INTO orders (order_id, client_id, business_id, total_amount, status, delivery_type) VALUES
('66600000-0000-0000-0000-000000000001', '55000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 17.00, 'pending', 'delivery');

INSERT INTO order_items (order_id, item_id, quantity, unit_price, name_snapshot) VALUES
('66600000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001', 1, 12.00, 'Classic Smash'),
('66600000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000002', 1, 5.00, 'Cajun Fries');

-- Past Order
INSERT INTO orders (order_id, client_id, business_id, total_amount, status, delivery_type, ordered_at) VALUES
('66600000-0000-0000-0000-000000000002', '55000000-0000-0000-0000-000000000002', 'b0000000-0000-0000-0000-000000000001', 12.00, 'delivered', 'pickup', NOW() - INTERVAL '1 day');

INSERT INTO order_items (order_id, item_id, quantity, unit_price, name_snapshot) VALUES
('66600000-0000-0000-0000-000000000002', 'd0000000-0000-0000-0000-000000000001', 1, 12.00, 'Classic Smash');