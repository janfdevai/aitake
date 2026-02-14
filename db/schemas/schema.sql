-- =============================================================================
-- MVP SCHEMA: FastOrder Simplified Version
-- Focus: Core ordering flow, WhatsApp bot, and basic CRM.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ENUMS
CREATE TYPE order_status_type AS ENUM ('pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled');
CREATE TYPE fulfillment_type AS ENUM ('delivery', 'pickup');
CREATE TYPE sender_type AS ENUM ('client', 'business', 'bot');

-- 2. CORE INFRASTRUCTURE
-- managers: Stores application users/managers with GCP authentication identity.
CREATE TABLE managers (
    manager_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gcp_uid TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- businesses: Stores business profile, WhatsApp API credentials, and operational status.
CREATE TABLE businesses (
    business_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    whatsapp_phone_number_id TEXT UNIQUE,
    whatsapp_phone_number TEXT,
    whatsapp_access_token TEXT,
    whatsapp_verify_token TEXT,
    address TEXT,
    logo_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- business_managers: Intersection table mapping managers to the businesses they represent.
CREATE TABLE business_managers (
    business_id UUID REFERENCES businesses(business_id) ON DELETE CASCADE,
    manager_id UUID REFERENCES managers(manager_id) ON DELETE CASCADE,
    PRIMARY KEY (business_id, manager_id)
);

-- 3. PRODUCT CATALOG

-- menu_items: Stores the catalog items available for order from a specific business.
CREATE TABLE menu_items (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(business_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    is_available BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. CRM & BOT STATE
-- clients: Stores customer profiles (CRM) linked to their unique WhatsApp ID.
CREATE TABLE clients (
    client_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(business_id) ON DELETE CASCADE,
    wa_id TEXT NOT NULL, -- WhatsApp ID (phone number format)
    full_name TEXT,
    phone_number TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, wa_id)
);

-- 5. ORDERS & FULFILLMENT
-- orders: Stores high-level order information, status, and fulfillment details.
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(client_id) ON DELETE SET NULL,
    business_id UUID REFERENCES businesses(business_id) ON DELETE CASCADE,
    total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    status order_status_type NOT NULL DEFAULT 'pending',
    delivery_type fulfillment_type NOT NULL,
    delivery_address TEXT,
    ordered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- order_items: Stores specific product snapshots and quantities for a given order.
CREATE TABLE order_items (
    order_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(order_id) ON DELETE CASCADE,
    item_id UUID REFERENCES menu_items(item_id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL,
    name_snapshot TEXT -- Store name in case it changes in catalog
);


-- 7. ESSENTIAL INDEXES
CREATE INDEX idx_clients_wa_id ON clients(wa_id);
CREATE INDEX idx_menu_items_business_id ON menu_items(business_id);
CREATE INDEX idx_orders_business_id ON orders(business_id);
CREATE INDEX idx_orders_client_id ON orders(client_id);

-- 6. CONVERSATIONS
-- conversations: Tracks chat threads between businesses and clients.
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(business_id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(client_id) ON DELETE CASCADE,
    last_message TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, client_id)
);

-- messages: Stores individual messages within a conversation.
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    sender_type sender_type NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_business_id ON conversations(business_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);