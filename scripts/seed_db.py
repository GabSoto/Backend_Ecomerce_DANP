"""
Seed script: carga datos ficticios en la base de datos para probar los endpoints.

Uso (desde la raíz del proyecto):
    python -m scripts.init_db     # crea las tablas
    python -m scripts.seed_db     # inserta datos ficticios

Credenciales del usuario de prueba:
    email:    test@example.com
    password: Test1234!
"""

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.address import Address
from app.models.cart_item import CartItem
from app.models.category import Category
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.profile import Profile
from app.models.user import User


def seed():
    # Limpiar y recrear todas las tablas
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tablas recreadas.")

    db = SessionLocal()
    try:
        # ------------------------------------------------------------------
        # 1. Usuario de prueba
        # ------------------------------------------------------------------
        user = User(
            name="Usuario de Prueba",
            email="test@example.com",
            password_hash=hash_password("Test1234!"),
        )
        db.add(user)
        db.flush()
        print(f"Usuario creado -> id={user.id}  email={user.email}")

        # ------------------------------------------------------------------
        # 2. Perfil del usuario
        # ------------------------------------------------------------------
        profile = Profile(
            user_id=user.id,
            first_name="Test",
            last_name="User",
            phone_number="+34 600 123 456",
            avatar_url="https://api.dicebear.com/7.x/initials/svg?seed=Test%20User",
        )
        db.add(profile)
        db.flush()
        print(f"Perfil creado   -> id={profile.id}")

        # ------------------------------------------------------------------
        # 3. Direcciones
        # ------------------------------------------------------------------
        addr_default = Address(
            user_id=user.id,
            street="Calle Mayor 25, 3ºB",
            city="Madrid",
            state="Madrid",
            zip_code="28013",
            is_default=True,
        )
        addr_secondary = Address(
            user_id=user.id,
            street="Avenida de la Playa 10",
            city="Valencia",
            state="Valencia",
            zip_code="46001",
            is_default=False,
        )
        db.add_all([addr_default, addr_secondary])
        db.flush()
        print(f"Direcciones creadas -> default={addr_default.id}  secondary={addr_secondary.id}")

        # ------------------------------------------------------------------
        # 4. Categorías
        # ------------------------------------------------------------------
        categories_data = [
            {"name": "Suplementos",      "description": "Proteínas, creatinas, pre-entrenos y vitaminas"},
            {"name": "Maquinaria",       "description": "Cintas de correr, elípticas, bancas y racks"},
            {"name": "Pesos Libres",     "description": "Mancuernas, barras Olímpicas y discos"},
            {"name": "Ropa Deportiva",   "description": "Camisetas transpirables, leggings, shorts y calzado"},
            {"name": "Accesorios",       "description": "Shakers, straps, cinturones lumbares y bandas"},
        ]
        categories = []
        for cat_data in categories_data:
            cat = Category(**cat_data)
            db.add(cat)
            categories.append(cat)
        db.flush()

        cat_suple, cat_maqui, cat_pesos, cat_ropa, cat_acc = categories
        print(f"Categorías creadas -> {len(categories)}")

        # ------------------------------------------------------------------
        # 5. Productos
        # ------------------------------------------------------------------
        products_data = [
            # Suplementos
            {"name": "Proteína Whey Isolate 1kg", "description": "25g de proteína por servicio, sabor chocolate", "price": 45.99, "stock": 120, "category_id": cat_suple, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Proteina%20Whey%20Isolate%201kg.webp"},
            {"name": "Creatina Monohidratada 300g", "description": "100% pura, mejora fuerza y recuperación masiva", "price": 24.50, "stock": 200, "category_id": cat_suple, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Creatina%20Monohidratada%20300g.webp"},
            {"name": "Pre-Entreno Explosivo", "description": "Fórmula con beta-alanina, cafeína y citrulina malato", "price": 29.99, "stock": 85, "category_id": cat_suple, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Pre-Entreno%20Explosivo.webp"},
            
            # Maquinaria
            {"name": "Cinta de Correr Plegable Pro", "description": "Motor 3.0 HP, pantalla LED, velocidad hasta 18 km/h", "price": 549.00, "stock": 10, "category_id": cat_maqui, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Cinta%20de%20Correr%20Plegable%20Pro.webp"},
            {"name": "Banca de Pesas Multiposición", "description": "Inclinable, declinable y plana, soporte hasta 300kg", "price": 119.90, "stock": 15, "category_id": cat_maqui, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Banca%20de%20Pesas%20Multiposicion.webp"},
            {"name": "Rack de Sentadillas Ajustable", "description": "Acero reforzado con ganchos de seguridad J-Cups", "price": 189.00, "stock": 8, "category_id": cat_maqui, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Rack%20de%20Sentadillas%20Ajustable.webp"},
            
            # Pesos Libres
            {"name": "Set Mancuernas Ajustables 20kg", "description": "Par de mancuernas con discos intercambiables de acero", "price": 79.99, "stock": 45, "category_id": cat_pesos, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Set%20Mancuernas%20Ajustables%2020kg.webp"},
            {"name": "Barra Olímpica de 20kg", "description": "Longitud 2.2m, rodamientos de aguja, carga hasta 450kg", "price": 135.00, "stock": 20, "category_id": cat_pesos, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Barra%20Olimpica%20de%2020kg.webp"},
            {"name": "Disco Bumper 15kg (Par)", "description": "Goma de alta densidad para crossfit y levantamiento olímpico", "price": 95.00, "stock": 30, "category_id": cat_pesos, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Disco%20Bumper%2015kg%20(Par).webp"},
            
            # Ropa Deportiva
            {"name": "Polera de Compresión Dry-Fit", "description": "Absorbe el sudor, ajuste elástico ultra cómodo", "price": 19.99, "stock": 150, "category_id": cat_ropa, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Polera%20de%20Compresion%20DryFit.webp"},
            {"name": "Shorts de Entrenamiento con Licra", "description": "Dos en uno, incluye bolsillo oculto para el celular", "price": 22.50, "stock": 100, "category_id": cat_ropa, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Shorts%20de%20Entrenamiento%20con%20Licra.webp"},
            
            # Accesorios
            {"name": "Shaker Mezclador Antiderrames", "description": "Capacidad 700ml con bola batidora de acero inoxidable", "price": 8.99, "stock": 250, "category_id": cat_acc, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Shaker%20Mezclador%20Antiderrames.webp"},
            {"name": "Cinturón Lumbar de Cuero", "description": "Protección para levantamientos pesados, 4 pulgadas de ancho", "price": 34.99, "stock": 40, "category_id": cat_acc, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Cinturon%20Lumbar%20de%20Cuero.webp"},
            {"name": "Set Bandas de Resistencia (5 niveles)", "description": "Látex natural, ideal para activación y calistenia", "price": 14.99, "stock": 180, "category_id": cat_acc, "imagen_url": "https://npmoytvohrirrmijnwfj.supabase.co/storage/v1/object/public/Images/Set%20Bandas%20de%20Resistencia%20(5%20niveles).webp"},
        ]
        products = []
        for prod_data in products_data:
            prod = Product(
                name=prod_data["name"],
                description=prod_data["description"],
                price=prod_data["price"],
                stock=prod_data["stock"],
                image_url=None,
                category_id=prod_data["category_id"].id,
            )
            db.add(prod)
            products.append(prod)
        db.flush()
        print(f"Productos creados  -> {len(products)}")

        # ------------------------------------------------------------------
        # 6. Carrito del usuario (2 items)
        # ------------------------------------------------------------------
        cart_item_1 = CartItem(user_id=user.id, product_id=products[0].id, quantity=2)
        cart_item_2 = CartItem(user_id=user.id, product_id=products[5].id, quantity=1)
        db.add_all([cart_item_1, cart_item_2])
        db.flush()
        print(f"Carrito creado      -> 2 items ({products[0].name} x2, {products[5].name} x1)")

        # ------------------------------------------------------------------
        # 7. Orden de ejemplo (estado "paid")
        # ------------------------------------------------------------------
        # Productos para la orden (simulando un checkout ya realizado)
        order_prod_1 = products[1]   # Smartwatch
        order_prod_2 = products[6]   # Monitor 27"
        o_qty_1 = 1
        o_qty_2 = 2

        o_subtotal_1 = round(order_prod_1.price * o_qty_1, 2)
        o_subtotal_2 = round(order_prod_2.price * o_qty_2, 2)
        o_subtotal = round(o_subtotal_1 + o_subtotal_2, 2)
        o_taxes = round(o_subtotal * settings.TAX_RATE, 2)
        o_shipping = settings.SHIPPING_COST
        o_total = round(o_subtotal + o_taxes + o_shipping, 2)

        # Descontar stock de los productos de la orden (consistencia)
        order_prod_1.stock -= o_qty_1
        order_prod_2.stock -= o_qty_2

        order = Order(
            user_id=user.id,
            status="paid",
            shipping_address_id=addr_default.id,
            subtotal=o_subtotal,
            taxes=o_taxes,
            shipping_cost=o_shipping,
            total=o_total,
        )
        db.add(order)
        db.flush()

        oi_1 = OrderItem(
            order_id=order.id,
            product_id=order_prod_1.id,
            quantity=o_qty_1,
            unit_price=order_prod_1.price,
            subtotal=o_subtotal_1,
        )
        oi_2 = OrderItem(
            order_id=order.id,
            product_id=order_prod_2.id,
            quantity=o_qty_2,
            unit_price=order_prod_2.price,
            subtotal=o_subtotal_2,
        )
        db.add_all([oi_1, oi_2])
        db.flush()
        print(f"Orden creada        -> id={order.id}  status=paid  total={o_total}")
        print(f"  OrderItems: {order_prod_1.name} x{o_qty_1} = {o_subtotal_1} | {order_prod_2.name} x{o_qty_2} = {o_subtotal_2}")

        # ------------------------------------------------------------------
        # Commit
        # ------------------------------------------------------------------
        db.commit()

        # ------------------------------------------------------------------
        # Resumen
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("SEED COMPLETADO — Datos ficticios cargados")
        print("=" * 60)
        print(f"  Usuario:    {user.email}")
        print(f"  Password:   Test1234!")
        print(f"  UserID:     {user.id}")
        print(f"  Categorías: {len(categories)}")
        print(f"  Productos:  {len(products)}")
        print(f"  Carrito:    2 items")
        print(f"  Orden:      1 (paid)")
        print("=" * 60)
        print("\nArranca el servidor con:")
        print("  uvicorn app.main:app --reload")
        print("Y usa las credenciales de arriba en POST /api/v1/auth/login")

    except Exception as exc:
        db.rollback()
        print(f"ERROR durante el seed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()