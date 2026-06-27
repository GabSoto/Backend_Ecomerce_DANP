-- =====================================================================
-- E-commerce API — Schema + Seed Data para Supabase SQL Editor
-- =====================================================================
-- Ejecuta este script completo en: Supabase Dashboard → SQL Editor
-- ---------------------------------------------------------------------
-- Usuario de prueba:
--   email:    test@example.com
--   password: Test1234!
-- ---------------------------------------------------------------------

-- =====================================================================
-- 0. Limpieza (orden inverso a las dependencias)
-- =====================================================================

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS addresses CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =====================================================================
-- 1. Creación de tablas (orden de dependencias)
-- =====================================================================

-- ---------------------------------------------------------------- users
CREATE TABLE users (
    id            VARCHAR(36) PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------- profiles
CREATE TABLE profiles (
    id           VARCHAR(36) PRIMARY KEY,
    user_id      VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    first_name   VARCHAR(255) NOT NULL,
    last_name    VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    avatar_url   VARCHAR(500),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------- addresses
CREATE TABLE addresses (
    id         VARCHAR(36) PRIMARY KEY,
    user_id    VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    street     VARCHAR(255) NOT NULL,
    city       VARCHAR(100) NOT NULL,
    state      VARCHAR(100) NOT NULL,
    zip_code   VARCHAR(20)  NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------ categories
CREATE TABLE categories (
    id          VARCHAR(36) PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(500),
    image_url   VARCHAR(500),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------- products
CREATE TABLE products (
    id          VARCHAR(36) PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description VARCHAR(1000),
    price       DOUBLE PRECISION NOT NULL,
    stock       INTEGER NOT NULL DEFAULT 0,
    image_url   VARCHAR(500),
    category_id VARCHAR(36) NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------ cart_items
CREATE TABLE cart_items (
    id         VARCHAR(36) PRIMARY KEY,
    user_id    VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id VARCHAR(36) NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity   INTEGER NOT NULL DEFAULT 1,
    added_at   TIMESTAMPTZ DEFAULT NOW()
);

-- --------------------------------------------------------------- orders
CREATE TABLE orders (
    id                 VARCHAR(36) PRIMARY KEY,
    user_id            VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status             VARCHAR(20) NOT NULL DEFAULT 'pending',
    shipping_address_id VARCHAR(36) NOT NULL REFERENCES addresses(id) ON DELETE RESTRICT,
    subtotal           DOUBLE PRECISION NOT NULL,
    taxes              DOUBLE PRECISION NOT NULL,
    shipping_cost      DOUBLE PRECISION NOT NULL,
    total              DOUBLE PRECISION NOT NULL,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------- order_items
CREATE TABLE order_items (
    id         VARCHAR(36) PRIMARY KEY,
    order_id   VARCHAR(36) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id VARCHAR(36) NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity   INTEGER NOT NULL,
    unit_price DOUBLE PRECISION NOT NULL,
    subtotal   DOUBLE PRECISION NOT NULL
);

-- =====================================================================
-- 2. Función + triggers para updated_at
--    (SQLAlchemy usa onupdate=func.now() a nivel ORM;
--    en PostgreSQL replicamos ese comportamiento con un trigger)
-- =====================================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =====================================================================
-- 3. Datos ficticios (seed)
-- =====================================================================

-- ----------------------------------------------------------------- User
-- password: Test1234!  (hash argon2 generado con passlib)
INSERT INTO users (id, name, email, password_hash) VALUES
('a0000000-0000-4000-8000-000000000001',
 'Usuario de Prueba',
 'test@example.com',
 '$argon2id$v=19$m=65536,t=3,p=4$UspZK8W4N6b03jvHuJey1g$2Um5bvShCv57u8dwuR20TrkU833f5SfIN5L3GkI59Jk');

-- -------------------------------------------------------------- Profile
INSERT INTO profiles (id, user_id, first_name, last_name, phone_number, avatar_url) VALUES
('a0000000-0000-4000-8000-000000000002',
 'a0000000-0000-4000-8000-000000000001',
 'Test', 'User',
 '+34 600 123 456',
 'https://api.dicebear.com/7.x/initials/svg?seed=Test%20User');

-- ------------------------------------------------------------- Addresses
INSERT INTO addresses (id, user_id, street, city, state, zip_code, is_default) VALUES
('a0000000-0000-4000-8000-000000000010',
 'a0000000-0000-4000-8000-000000000001',
 'Calle Mayor 25, 3ºB', 'Madrid', 'Madrid', '28013', TRUE),

('a0000000-0000-4000-8000-000000000011',
 'a0000000-0000-4000-8000-000000000001',
 'Avenida de la Playa 10', 'Valencia', 'Valencia', '46001', FALSE);

-- ------------------------------------------------------------ Categories
INSERT INTO categories (id, name, description) VALUES
('b0000000-0000-4000-8000-000000000001', 'Suplementos', 'Proteínas, creatinas, pre-entrenos y vitaminas'),
('b0000000-0000-4000-8000-000000000002', 'Maquinaria', 'Cintas de correr, elípticas, bancas y racks'),
('b0000000-0000-4000-8000-000000000003', 'Pesos Libres', 'Mancuernas, barras Olímpicas y discos'),
('b0000000-0000-4000-8000-000000000004', 'Ropa Deportiva', 'Camisetas transpirables, leggings, shorts y calzado'),
('b0000000-0000-4000-8000-000000000005', 'Accesorios', 'Shakers, straps, cinturones lumbares y bandas');

-- ------------------------------------------------------------- Products
-- El stock de los productos de la orden ya está descontado
-- (Smartwatch: 30-1=29, Monitor: 15-2=13)
INSERT INTO products (id, name, description, price, stock, category_id, image_url) VALUES
-- Suplementos ('b0000000-0000-4000-8000-000000000001')
('c0000000-0000-4000-8000-000000000001', 'Proteína Whey Isolate 1kg', '25g de proteína por servicio, sabor chocolate', 45.99, 120, 'b0000000-0000-4000-8000-000000000001', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Proteina%20Whey%20Isolate%201kg.webp'),
('c0000000-0000-4000-8000-000000000002', 'Creatina Monohidratada 300g', '100% pura, mejora fuerza y recuperación masiva', 24.50, 200, 'b0000000-0000-4000-8000-000000000001', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Creatina%20Monohidratada%20300g.webp'),
('c0000000-0000-4000-8000-000000000003', 'Pre-Entreno Explosivo', 'Fórmula con beta-alanina, cafeína y citrulina malato', 29.99, 85, 'b0000000-0000-4000-8000-000000000001', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Pre-Entreno%20Explosivo.webp'),

-- Maquinaria ('b0000000-0000-4000-8000-000000000002')
('c0000000-0000-4000-8000-000000000004', 'Cinta de Correr Plegable Pro', 'Motor 3.0 HP, pantalla LED, velocidad hasta 18 km/h', 549.00, 10, 'b0000000-0000-4000-8000-000000000002', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Cinta%20de%20Correr%20Plegable%20Pro.webp'),
('c0000000-0000-4000-8000-000000000005', 'Banca de Pesas Multiposición', 'Inclinable, declinable y plana, soporte hasta 300kg', 119.90, 15, 'b0000000-0000-4000-8000-000000000002', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Banca%20de%20Pesas%20Multiposicion.webp'),
('c0000000-0000-4000-8000-000000000006', 'Rack de Sentadillas Ajustable', 'Acero reforzado con ganchos de seguridad J-Cups', 189.00, 8, 'b0000000-0000-4000-8000-000000000002', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Rack%20de%20Sentadillas%20Ajustable.webp'),

-- Pesos Libres ('b0000000-0000-4000-8000-000000000003')
('c0000000-0000-4000-8000-000000000007', 'Set Mancuernas Ajustables 20kg', 'Par de mancuernas con discos intercambiables de acero', 79.99, 45, 'b0000000-0000-4000-8000-000000000003', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Set%20Mancuernas%20Ajustables%2020kg.webp'),
('c0000000-0000-4000-8000-000000000008', 'Barra Olímpica de 20kg', 'Longitud 2.2m, rodamientos de aguja, carga hasta 450kg', 135.00, 20, 'b0000000-0000-4000-8000-000000000003', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Barra%20Olimpica%20de%2020kg.webp'),
('c0000000-0000-4000-8000-000000000009', 'Disco Bumper 15kg (Par)', 'Goma de alta densidad para crossfit y levantamiento olímpico', 95.00, 30, 'b0000000-0000-4000-8000-000000000003', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Disco%20Bumper%2015kg%20(Par).webp'),

-- Ropa Deportiva ('b0000000-0000-4000-8000-000000000004')
('c0000000-0000-4000-8000-00000000000a', 'Polera de Compresión Dry-Fit', 'Absorbe el sudor, ajuste elástico ultra cómodo', 19.99, 150, 'b0000000-0000-4000-8000-000000000004', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Polera%20de%20Compresion%20DryFit.webp'),
('c0000000-0000-4000-8000-00000000000b', 'Shorts de Entrenamiento con Licra', 'Dos en uno, incluye bolsillo oculto para el celular', 22.50, 100, 'b0000000-0000-4000-8000-000000000004', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Shorts%20de%20Entrenamiento%20con%20Licra.webp'),

-- Accesorios ('b0000000-0000-4000-8000-000000000005')
('c0000000-0000-4000-8000-00000000000c', 'Shaker Mezclador Antiderrames', 'Capacidad 700ml con bola batidora de acero inoxidable', 8.99, 250, 'b0000000-0000-4000-8000-000000000005', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Shaker%20Mezclador%20Antiderrames.webp'),
('c0000000-0000-4000-8000-00000000000d', 'Cinturón Lumbar de Cuero', 'Protección para levantamientos pesados, 4 pulgadas de ancho', 34.99, 40, 'b0000000-0000-4000-8000-000000000005', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Cinturon%20Lumbar%20de%20Cuero.webp'),
('c0000000-0000-4000-8000-00000000000e', 'Set Bandas de Resistencia (5 niveles)', 'Látex natural, ideal para activación y calistenia', 14.99, 180, 'b0000000-0000-4000-8000-000000000005', 'https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Set%20Bandas%20de%20Resistencia%20(5%20niveles).webp');

-- ----------------------------------------------------------- Cart items
INSERT INTO cart_items (id, user_id, product_id, quantity) VALUES
-- Item 1: Agrega 2 unidades de 'Proteína Whey Isolate'
('d0000000-0000-4000-8000-000000000001',
 'a0000000-0000-4000-8000-000000000001',
 'c0000000-0000-4000-8000-000000000001', 2),

-- Item 2: Agrega 1 unidad de 'Rack de Sentadillas Ajustable'
('d0000000-0000-4000-8000-000000000002',
 'a0000000-0000-4000-8000-000000000001',
 'c0000000-0000-4000-8000-000000000006', 1);

-- --------------------------------------------------------------- Orders
-- Orden en estado "paid" (Smartwatch x1 + Monitor x2)
-- subtotal = 129.50 + 498.00 = 627.50
-- taxes    = 627.50 * 0.18 = 112.95
-- shipping = 5.99
-- total    = 627.50 + 112.95 + 5.99 = 746.44
INSERT INTO orders (id, user_id, status, shipping_address_id, subtotal, taxes, shipping_cost, total) VALUES
('e0000000-0000-4000-8000-000000000001',
 'a0000000-0000-4000-8000-000000000001',
 'paid',
 'a0000000-0000-4000-8000-000000000010',
 627.50, 112.95, 5.99, 746.44);

-- ---------------------------------------------------------- Order items
INSERT INTO order_items (id, order_id, product_id, quantity, unit_price, subtotal) VALUES
('f0000000-0000-4000-8000-000000000001',
 'e0000000-0000-4000-8000-000000000001',
 'c0000000-0000-4000-8000-000000000002',  -- Creatina Monohidratada 300g
 1, 129.50, 129.50),

('f0000000-0000-4000-8000-000000000002',
 'e0000000-0000-4000-8000-000000000001',
 'c0000000-0000-4000-8000-000000000007',  -- Set Mancuernas Ajustables 20kg
 2, 249.00, 498.00);

-- =====================================================================
-- 4. Verificación rápida (opcional — descomenta para validar)
-- =====================================================================
-- SELECT 'users'      AS tabla, COUNT(*) AS n FROM users
-- UNION ALL SELECT 'profiles',     COUNT(*) FROM profiles
-- UNION ALL SELECT 'addresses',   COUNT(*) FROM addresses
-- UNION ALL SELECT 'categories',  COUNT(*) FROM categories
-- UNION ALL SELECT 'products',    COUNT(*) FROM products
-- UNION ALL SELECT 'cart_items',  COUNT(*) FROM cart_items
-- UNION ALL SELECT 'orders',      COUNT(*) FROM orders
-- UNION ALL SELECT 'order_items', COUNT(*) FROM order_items;