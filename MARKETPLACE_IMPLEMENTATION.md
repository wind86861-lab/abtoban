# Marketplace Implementation Guide

## Overview
Complete online marketplace integration into Avtoban Telegram bot, allowing clients to browse products, add to cart, and place orders. Admins can manage products, categories, and orders through the TMA admin panel.

## What's Been Implemented

### 1. Database Models ✅
**File:** `app/db/models.py`

Added 4 new models:
- `Category` - Product categories with multilingual support (uz, ru, en)
- `Product` - Products with pricing, discounts, stock, images
- `CartItem` - Shopping cart items for users
- `MarketOrder` - Customer orders from marketplace
- `MarketOrderItem` - Individual items in orders
- `MarketOrderStatus` - Enum for order statuses (new, processing, completed, cancelled)

Updated `User` model with:
- `cart_items` relationship
- `market_orders` relationship

### 2. Database Migration ✅
**File:** `migrations/versions/007_marketplace_tables.py`

Creates tables:
- `categories` - with parent-child hierarchy support
- `products` - with category FK, multilingual fields
- `cart_items` - user cart storage
- `market_orders` - order headers
- `market_order_items` - order line items

### 3. API Routes ✅
**File:** `app/web/marketplace_routes.py`

Complete REST API with 25+ endpoints:

**Categories:**
- `GET /market-api/categories` - List all categories
- `POST /market-api/categories` - Create category
- `PATCH /market-api/categories/{id}` - Update category
- `PATCH /market-api/categories/{id}/toggle` - Toggle active status
- `DELETE /market-api/categories/{id}` - Delete category

**Products:**
- `GET /market-api/products` - List products (with filters)
- `GET /market-api/products/{id}` - Get product details
- `POST /market-api/products` - Create product
- `PATCH /market-api/products/{id}` - Update product
- `PATCH /market-api/products/{id}/toggle` - Toggle active status
- `DELETE /market-api/products/{id}` - Delete product

**Cart (Client):**
- `GET /market-api/cart/{user_id}` - Get cart items
- `POST /market-api/cart/{user_id}` - Add to cart
- `PATCH /market-api/cart/items/{id}` - Update quantity
- `DELETE /market-api/cart/items/{id}` - Remove from cart
- `DELETE /market-api/cart/{user_id}/clear` - Clear cart

**Orders:**
- `POST /market-api/cart/{user_id}/checkout` - Checkout cart
- `GET /market-api/orders` - List all orders (admin)
- `GET /market-api/orders/{id}` - Get order details
- `PATCH /market-api/orders/{id}/status` - Update order status
- `GET /market-api/users/{user_id}/orders` - Get user's orders

### 4. Telegram Bot Handlers ✅
**File:** `app/bot/handlers/shop.py`

Complete shopping experience for KLIENT role:

**Commands:**
- `/shop` - Open marketplace

**Features:**
- Browse categories
- View products with prices and discounts
- Product detail view with description
- Add to cart (with stock validation)
- View cart with total calculation
- Remove items from cart
- Clear cart
- Checkout process (phone + optional comment)
- View order history

**FSM States:**
- `browsing_categories`
- `browsing_products`
- `viewing_product`
- `viewing_cart`
- `checkout_phone`
- `checkout_comment`

### 5. Integration ✅
**File:** `app/web/app.py`
- Registered `marketplace_router`

**File:** `app/bot/handlers/__init__.py`
- Registered `shop_router`

## What Still Needs to Be Done

### 1. Admin UI in TMA Panel 🔄
Need to add 3 new tabs to `tma_admin.html`:

**Categories Tab:**
- List all categories
- Create/edit/delete categories
- Toggle active status
- Parent-child hierarchy management

**Products Tab:**
- List all products
- Create/edit/delete products
- Upload product images
- Set pricing and discounts
- Manage stock levels
- Toggle active/featured status

**Market Orders Tab:**
- List all marketplace orders
- View order details
- Update order status (new → processing → completed/cancelled)
- Filter by status

### 2. Image Upload Support 🔄
Need to implement:
- File upload endpoint in `marketplace_routes.py`
- Image storage (local or cloud)
- Multiple image support for products
- Image display in bot and admin panel

### 3. Client Menu Integration 🔄
Update `app/bot/handlers/klient.py`:
- Add "🛍 Do'kon" button to main menu
- Link to `/shop` command

### 4. Admin Notifications 🔄
When new order is placed:
- Notify admins via Telegram
- Show order details
- Quick action buttons

### 5. Testing & Deployment 🔄
- Run migration on server: `alembic upgrade head`
- Test all API endpoints
- Test bot shopping flow
- Test admin panel management
- Seed initial categories and products

## Database Schema

```sql
-- Categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name_uz VARCHAR(255) NOT NULL,
    name_ru VARCHAR(255) NOT NULL,
    name_en VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    image VARCHAR(500),
    "order" INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Products
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name_uz VARCHAR(500) NOT NULL,
    name_ru VARCHAR(500) NOT NULL,
    name_en VARCHAR(500) NOT NULL,
    description_uz TEXT,
    description_ru TEXT,
    description_en TEXT,
    price NUMERIC(12,2) NOT NULL,
    discount_value NUMERIC(12,2),
    discount_type VARCHAR(20), -- 'percentage' or 'fixed'
    category_id INTEGER REFERENCES categories(id),
    images TEXT, -- comma-separated URLs
    stock INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Cart Items
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Market Orders
CREATE TABLE market_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    customer_name VARCHAR(255),
    customer_phone VARCHAR(50) NOT NULL,
    total_price NUMERIC(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'new', -- new, processing, completed, cancelled
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Market Order Items
CREATE TABLE market_order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES market_orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name VARCHAR(500) NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    quantity INTEGER NOT NULL,
    image VARCHAR(500)
);
```

## Usage Examples

### For Clients (via Telegram Bot)
1. Send `/shop` command
2. Browse categories
3. View products
4. Add items to cart
5. View cart
6. Checkout (enter phone + optional comment)
7. Receive order confirmation

### For Admins (via TMA Panel)
1. Open admin panel
2. Go to "Products" tab
3. Create categories
4. Add products with images, prices, stock
5. Monitor orders in "Market Orders" tab
6. Update order statuses

## API Examples

### Create Category
```bash
POST /market-api/categories
{
  "name_uz": "Qurilish materiallari",
  "name_ru": "Строительные материалы",
  "name_en": "Construction Materials",
  "order": 1
}
```

### Create Product
```bash
POST /market-api/products
{
  "name_uz": "Asfalt M-100",
  "name_ru": "Асфальт M-100",
  "name_en": "Asphalt M-100",
  "description_uz": "Yuqori sifatli asfalt",
  "price": 150000,
  "discount_value": 10,
  "discount_type": "percentage",
  "category_id": 1,
  "stock": 100,
  "is_featured": true
}
```

### Checkout
```bash
POST /market-api/cart/123/checkout
{
  "customer_phone": "+998901234567",
  "comment": "Iltimos tezroq yetkazib bering"
}
```

## Next Steps

1. **Complete Admin UI** - Add marketplace tabs to `tma_admin.html`
2. **Add Image Upload** - Implement file upload for product images
3. **Integrate with Client Menu** - Add shop button to klient main menu
4. **Run Migration** - Deploy database changes to server
5. **Seed Data** - Add initial categories and products
6. **Test End-to-End** - Full shopping flow from bot to admin panel
7. **Deploy** - Push to production and restart services

## Notes

- All prices are in Uzbek Som (UZS)
- Multilingual support (Uzbek, Russian, English)
- Discount types: percentage or fixed amount
- Stock management included
- Order status workflow: new → processing → completed/cancelled
- Cart persists across sessions
- Admin can manage everything via TMA panel
