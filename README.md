# Ficha Técnica — Backend E-commerce API (FastAPI + PostgreSQL/Neon + Vercel)

> Proyecto de laboratorio, consumo de un solo usuario, con autenticación JWT real.
> Despliegue: Vercel (serverless ASGI) + PostgreSQL administrado en Neon.

---

## 0. Stack y decisiones de infraestructura

| Decisión | Elección | Motivo |
|---|---|---|
| Framework | FastAPI | requerido |
| ORM | SQLAlchemy 2.x (modo sync) | simplicidad, no se justifica async para un solo usuario |
| Base de datos | PostgreSQL (Neon, **pooled connection**) | persistencia real en entorno serverless |
| Pool de conexiones | `NullPool` en SQLAlchemy + PgBouncer de Neon | evita agotar conexiones entre invocaciones frías |
| Migraciones | **Ninguna** (Alembic omitido) | laboratorio; se usa `Base.metadata.create_all()` una sola vez vía script manual |
| Auth | JWT (access + refresh) | requerido explícitamente |
| Roles / permisos | **Ninguno** | un solo usuario consumidor; no se modela admin/customer |
| Despliegue | Vercel (`@vercel/python`, entry point ASGI) | requerido |
| Validación | Pydantic v2 (schemas separados de los modelos ORM) | input/output limpio, evita exponer columnas internas |

### Variables de entorno (`.env` / Vercel dashboard)

```
DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/dbname?sslmode=require
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 1. Árbol de directorios completo

```
proyecto/
├── api/
│   └── index.py                     # Entry point ASGI que detecta Vercel
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # Instancia FastAPI(), incluye router v1, CORS, exception handlers
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Settings (pydantic-settings) leyendo env vars
│   │   ├── security.py                # hash_password, verify_password, create_access_token,
│   │   │                              # create_refresh_token, decode_token
│   │   └── exceptions.py              # Excepciones custom (NotFoundError, InsufficientStockError, etc.)
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                    # Base declarativa (declarative_base)
│   │   └── session.py                 # engine, SessionLocal, NullPool config
│   │
│   ├── models/                        # SQLAlchemy ORM — 1 archivo por entidad
│   │   ├── __init__.py                # importa todos los modelos (necesario para create_all)
│   │   ├── user.py
│   │   ├── profile.py
│   │   ├── address.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── cart_item.py
│   │   ├── order.py
│   │   └── order_item.py
│   │
│   ├── schemas/                       # Pydantic — request/response, separados por módulo
│   │   ├── __init__.py
│   │   ├── auth.py                    # RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
│   │   ├── user.py                    # UserOut, UserUpdate, PasswordUpdate
│   │   ├── profile.py                 # ProfileOut, ProfileUpsert
│   │   ├── address.py                 # AddressCreate, AddressUpdate, AddressOut
│   │   ├── category.py                # CategoryCreate, CategoryUpdate, CategoryOut
│   │   ├── product.py                 # ProductCreate, ProductUpdate, ProductOut, ProductStockUpdate
│   │   ├── cart.py                    # CartItemCreate, CartItemUpdate, CartItemOut, CartOut (con totales)
│   │   ├── order.py                   # OrderCreate (checkout), OrderOut, OrderItemOut, OrderStatusUpdate
│   │   └── common.py                  # PaginatedResponse genérico, mensajes de error estándar
│   │
│   ├── deps.py                        # get_db(), get_current_user() — dependencias compartidas
│   │
│   ├── services/                      # Lógica de negocio (no vive en routers ni modelos)
│   │   ├── __init__.py
│   │   ├── auth_service.py            # registro, login, rotación de refresh tokens
│   │   ├── profile_service.py         # upsert de profile (1:1)
│   │   ├── address_service.py         # gestión de is_default exclusivo
│   │   ├── product_service.py         # ajuste de stock, búsqueda/filtros
│   │   ├── cart_service.py            # merge de cantidades, cálculo de totales del carrito
│   │   └── order_service.py           # checkout transaccional, transiciones de estado
│   │
│   └── api/
│       └── v1/
│           ├── __init__.py
│           ├── router.py              # agrega todos los sub-routers con sus prefijos
│           ├── routes_auth.py
│           ├── routes_users.py
│           ├── routes_addresses.py
│           ├── routes_categories.py
│           ├── routes_products.py
│           ├── routes_cart.py
│           └── routes_orders.py
│
├── scripts/
│   └── init_db.py                     # Crea las tablas en Neon (correr manualmente, una vez)
│
├── requirements.txt
├── vercel.json
├── .env.example
└── README.md
```

---

## 2. Módulo: Auth

**Tablas involucradas:** `users`

### Reglas de negocio
- El email es único; intentar registrar uno existente devuelve `409 Conflict`.
- La contraseña se almacena **solo como hash** (argon2 vía `passlib`), nunca en texto plano ni siquiera en logs.
- Login válido devuelve `access_token` (corta duración, ej. 30 min) y `refresh_token` (larga duración, ej. 7 días).
- El `access_token` se usa en el header `Authorization: Bearer <token>` para todos los endpoints protegidos (todos excepto `register`, `login`, `refresh`, y lecturas públicas de catálogo).
- `refresh` valida el refresh token y emite un nuevo access token (rotación simple, sin blacklist por ser laboratorio).
- Al crear un `user`, no se crea automáticamente un `profile` — se crea bajo demanda en `PUT /users/me/profile`.

### Endpoints

| Método | Ruta | Auth | Body | Response |
|---|---|---|---|---|
| POST | `/api/v1/auth/register` | No | `RegisterRequest` | `UserOut` (201) |
| POST | `/api/v1/auth/login` | No | `LoginRequest` | `TokenResponse` (200) |
| POST | `/api/v1/auth/refresh` | No | `RefreshRequest` | `TokenResponse` (200) |

### Estructuras expuestas

```python
# RegisterRequest
{
  "name": str,
  "email": EmailStr,
  "password": str  # min 8 caracteres
}

# LoginRequest
{
  "email": EmailStr,
  "password": str
}

# RefreshRequest
{
  "refresh_token": str
}

# TokenResponse
{
  "access_token": str,
  "refresh_token": str,
  "token_type": "bearer"
}

# UserOut
{
  "id": str,
  "name": str,
  "email": str,
  "created_at": datetime
}
```

### Errores esperados
- `409` email ya registrado.
- `401` credenciales inválidas (login) o refresh token inválido/expirado.

---

## 3. Módulo: Users & Profile

**Tablas involucradas:** `users`, `profiles`

### Reglas de negocio
- `profiles` es 1:1 con `users` (FK única en `profiles.user_id`).
- `GET /users/me` devuelve el usuario **con su profile embebido** (si existe; si no, `profile: null`) para evitar una segunda llamada.
- `PUT /users/me/profile` es un **upsert**: si no existe profile lo crea, si existe lo actualiza completo.
- Cambiar el email en `PATCH /users/me` revalida unicidad igual que en registro.
- `PUT /users/me/password` exige la contraseña actual antes de aceptar la nueva (verificación de hash).

### Endpoints

| Método | Ruta | Auth | Body | Response |
|---|---|---|---|---|
| GET | `/api/v1/users/me` | Sí | — | `UserWithProfileOut` |
| PATCH | `/api/v1/users/me` | Sí | `UserUpdate` | `UserOut` |
| PUT | `/api/v1/users/me/password` | Sí | `PasswordUpdate` | `204 No Content` |
| PUT | `/api/v1/users/me/profile` | Sí | `ProfileUpsert` | `ProfileOut` |

### Estructuras expuestas

```python
# UserUpdate
{
  "name": str | None,
  "email": EmailStr | None
}

# PasswordUpdate
{
  "current_password": str,
  "new_password": str  # min 8 caracteres
}

# ProfileUpsert
{
  "first_name": str,
  "last_name": str,
  "phone_number": str | None,
  "avatar_url": str | None
}

# ProfileOut
{
  "id": str,
  "first_name": str,
  "last_name": str,
  "phone_number": str | None,
  "avatar_url": str | None,
  "created_at": datetime,
  "updated_at": datetime
}

# UserWithProfileOut
{
  "id": str,
  "name": str,
  "email": str,
  "created_at": datetime,
  "profile": ProfileOut | None
}
```

### Errores esperados
- `404` si se intenta actualizar password sin sesión válida (cubierto por 401 del dep de auth).
- `400` `current_password` no coincide.
- `409` nuevo email ya en uso por otro usuario.

---

## 4. Módulo: Addresses

**Tablas involucradas:** `addresses`

### Reglas de negocio
- Un usuario puede tener múltiples direcciones.
- **Solo una dirección puede ser `is_default = true` por usuario.** Al marcar una nueva como default, el service debe desmarcar las demás en la misma transacción.
- Si el usuario no tiene ninguna dirección y crea la primera, esa se marca automáticamente como default (regla de conveniencia).
- No se puede eliminar una dirección referenciada por una orden existente (`orders.shipping_address_id`) — en su lugar, devolver `409` indicando que está en uso. (Alternativa más simple para laboratorio: permitir el borrado porque `shipping_address_id` puede quedar huérfano; **decisión: bloquear el borrado** para mantener integridad histórica de órdenes).
- Toda dirección pertenece exclusivamente al usuario autenticado; no hay acceso cruzado entre usuarios (aunque sea de un solo usuario, se valida `user_id` por buena práctica y porque el JWT define el alcance).

### Endpoints

| Método | Ruta | Auth | Body | Response |
|---|---|---|---|---|
| GET | `/api/v1/addresses` | Sí | — | `list[AddressOut]` |
| POST | `/api/v1/addresses` | Sí | `AddressCreate` | `AddressOut` (201) |
| GET | `/api/v1/addresses/{address_id}` | Sí | — | `AddressOut` |
| PUT | `/api/v1/addresses/{address_id}` | Sí | `AddressUpdate` | `AddressOut` |
| DELETE | `/api/v1/addresses/{address_id}` | Sí | — | `204` |
| PATCH | `/api/v1/addresses/{address_id}/default` | Sí | — | `AddressOut` |

### Estructuras expuestas

```python
# AddressCreate
{
  "street": str,
  "city": str,
  "state": str,
  "zip_code": str,
  "is_default": bool = False
}

# AddressUpdate  (todos opcionales, PUT parcial-friendly)
{
  "street": str | None,
  "city": str | None,
  "state": str | None,
  "zip_code": str | None
}

# AddressOut
{
  "id": str,
  "street": str,
  "city": str,
  "state": str,
  "zip_code": str,
  "is_default": bool,
  "created_at": datetime
}
```

### Errores esperados
- `404` dirección no existe o no pertenece al usuario.
- `409` al intentar borrar una dirección usada en alguna orden.

---

## 5. Módulo: Categories

**Tablas involucradas:** `categories`

### Reglas de negocio
- `name` es único; duplicado devuelve `409`.
- Lectura pública (no requiere auth) ya que es catálogo; escritura requiere auth (sin distinción de rol, dado que es un solo usuario).
- No se permite eliminar una categoría que tenga productos asociados (`products.category_id`) — devolver `409`. Alternativa: reasignar productos a "sin categoría" antes de borrar (no implementado en este laboratorio, se opta por bloqueo simple).

### Endpoints

| Método | Ruta | Auth | Body | Response |
|---|---|---|---|---|
| GET | `/api/v1/categories` | No | — | `list[CategoryOut]` |
| GET | `/api/v1/categories/{category_id}` | No | — | `CategoryOut` |
| POST | `/api/v1/categories` | Sí | `CategoryCreate` | `CategoryOut` (201) |
| PUT | `/api/v1/categories/{category_id}` | Sí | `CategoryUpdate` | `CategoryOut` |
| DELETE | `/api/v1/categories/{category_id}` | Sí | — | `204` |

### Estructuras expuestas

```python
# CategoryCreate
{
  "name": str,
  "description": str | None,
  "image_url": str | None
}

# CategoryUpdate (todos opcionales)
{
  "name": str | None,
  "description": str | None,
  "image_url": str | None
}

# CategoryOut
{
  "id": str,
  "name": str,
  "description": str | None,
  "image_url": str | None,
  "created_at": datetime
}
```

### Errores esperados
- `404` categoría no existe.
- `409` nombre duplicado, o borrado bloqueado por productos asociados.

---

## 6. Módulo: Products

**Tablas involucradas:** `products`, `categories` (FK)

### Reglas de negocio
- `category_id` debe existir; si no, `422`/`404` según validación.
- `stock` nunca puede ser negativo; cualquier operación que lo lleve por debajo de 0 se rechaza con `409`.
- `price` y `stock` se validan como `>= 0` a nivel de schema (Pydantic `Field(ge=0)`).
- El endpoint de ajuste de stock (`PATCH /products/{id}/stock`) admite delta (`+n` o `-n`) o valor absoluto — **decisión: delta**, porque refleja mejor operaciones reales (entrada/salida de inventario) y evita condiciones de carrera de "leer-luego-escribir" en el cliente.
- Listado público con filtros combinables: por categoría, rango de precio, texto en nombre/descripción, y disponibilidad (`in_stock=true` → `stock > 0`).
- Paginación obligatoria en el listado (`page`, `size`, default `size=20`, máximo `size=100`).

### Endpoints

| Método | Ruta | Auth | Query/Body | Response |
|---|---|---|---|---|
| GET | `/api/v1/products` | No | `?page=&size=&category_id=&q=&min_price=&max_price=&in_stock=` | `PaginatedResponse[ProductOut]` |
| GET | `/api/v1/products/{product_id}` | No | — | `ProductOut` |
| POST | `/api/v1/products` | Sí | `ProductCreate` | `ProductOut` (201) |
| PUT | `/api/v1/products/{product_id}` | Sí | `ProductUpdate` | `ProductOut` |
| PATCH | `/api/v1/products/{product_id}/stock` | Sí | `ProductStockUpdate` | `ProductOut` |
| DELETE | `/api/v1/products/{product_id}` | Sí | — | `204` |

### Estructuras expuestas

```python
# ProductCreate
{
  "name": str,
  "description": str | None,
  "price": float,        # ge=0
  "stock": int = 0,       # ge=0
  "image_url": str | None,
  "category_id": str
}

# ProductUpdate (todos opcionales)
{
  "name": str | None,
  "description": str | None,
  "price": float | None,
  "image_url": str | None,
  "category_id": str | None
}

# ProductStockUpdate
{
  "delta": int   # positivo = ingreso, negativo = salida; valida que stock resultante >= 0
}

# ProductOut
{
  "id": str,
  "name": str,
  "description": str | None,
  "price": float,
  "stock": int,
  "image_url": str | None,
  "category_id": str,
  "category_name": str,    # join conveniente para el cliente
  "created_at": datetime,
  "updated_at": datetime
}
```

### Errores esperados
- `404` producto o categoría no existe.
- `409` `delta` dejaría el stock en negativo.
- `409` borrado bloqueado si el producto aparece en `order_items` (integridad histórica) — **decisión: bloquear borrado duro**, sugerir en su lugar dejar `stock = 0` para "descontinuarlo" sin romper historial de órdenes.

---

## 7. Módulo: Cart

**Tablas involucradas:** `cart_items`, `products` (FK)

### Reglas de negocio
- El carrito **no es una entidad propia**: es la colección de `cart_items` del usuario autenticado (no hay tabla `carts`).
- Al agregar un producto que **ya existe** en el carrito del usuario, se **incrementa la cantidad** existente en lugar de crear una fila duplicada (constraint lógica: única combinación `user_id + product_id` activa a la vez).
- Al agregar/actualizar cantidad, se valida contra `products.stock` disponible; si `quantity` solicitada > stock, `409`.
- `GET /cart` devuelve los items **y los totales calculados al vuelo** (no persistidos), usando el precio **actual** del producto (a diferencia de una orden, donde el precio se congela).
- `DELETE /cart` vacía todo el carrito del usuario (usado también internamente tras un checkout exitoso).

### Endpoints

| Método | Ruta | Auth | Body | Response |
|---|---|---|---|---|
| GET | `/api/v1/cart` | Sí | — | `CartOut` |
| POST | `/api/v1/cart/items` | Sí | `CartItemCreate` | `CartItemOut` (201) |
| PUT | `/api/v1/cart/items/{item_id}` | Sí | `CartItemUpdate` | `CartItemOut` |
| DELETE | `/api/v1/cart/items/{item_id}` | Sí | — | `204` |
| DELETE | `/api/v1/cart` | Sí | — | `204` |

### Estructuras expuestas

```python
# CartItemCreate
{
  "product_id": str,
  "quantity": int = 1   # ge=1
}

# CartItemUpdate
{
  "quantity": int   # ge=1
}

# CartItemOut
{
  "id": str,
  "product_id": str,
  "product_name": str,
  "product_image_url": str | None,
  "unit_price": float,      # precio ACTUAL del producto (no congelado)
  "quantity": int,
  "subtotal": float,        # unit_price * quantity
  "added_at": datetime
}

# CartOut
{
  "items": list[CartItemOut],
  "items_count": int,
  "subtotal": float          # suma de todos los subtotales
}
```

### Errores esperados
- `404` producto no existe (al agregar) o item de carrito no existe/no pertenece al usuario.
- `409` cantidad solicitada excede el stock disponible.

---

## 8. Módulo: Orders

**Tablas involucradas:** `orders`, `order_items`, `cart_items`, `products`, `addresses`

### Reglas de negocio (la parte más sensible del sistema)

**Checkout (`POST /orders`)** — operación transaccional que:
1. Lee los `cart_items` del usuario; si está vacío → `400`.
2. Valida que `shipping_address_id` exista y pertenezca al usuario → si no, `404`.
3. Valida stock suficiente para **cada** producto del carrito → si alguno falla, `409` indicando cuál producto.
4. Calcula:
   - `subtotal` = Σ (`quantity * product.price` al momento del checkout)
   - `taxes` = `subtotal * TAX_RATE` (constante configurable, ej. 0.18)
   - `shipping_cost` = regla fija o por tabla simple (ej. flat rate; configurable en `core/config.py`)
   - `total` = `subtotal + taxes + shipping_cost`
5. Crea `orders` con `status = "pending"`.
6. Crea un `order_item` por cada `cart_item`, **congelando** `unit_price` y `subtotal` con el precio del producto en ese instante (independiente de cambios futuros de precio).
7. Descuenta `stock` de cada producto afectado.
8. Vacía el carrito del usuario.
9. Si cualquier paso falla, **rollback completo** — no debe quedar stock descontado sin orden creada, ni orden creada sin descuento de stock.

**Transiciones de estado válidas** (se valida en el service, no se aceptan saltos arbitrarios):

```
pending → paid → processing → shipped → delivered
pending → cancelled
paid → cancelled        (con reposición de stock)
```

- Cancelar una orden en estado `pending` o `paid` repone el `stock` de los productos involucrados.
- No se puede cancelar una orden `shipped` o `delivered`.
- No se puede pasar de `pending` directo a `shipped` (debe respetar la secuencia).

### Endpoints

| Método | Ruta | Auth | Body | Response |
|---|---|---|---|---|
| POST | `/api/v1/orders` | Sí | `OrderCreate` | `OrderOut` (201) |
| GET | `/api/v1/orders` | Sí | `?page=&size=&status=` | `PaginatedResponse[OrderSummaryOut]` |
| GET | `/api/v1/orders/{order_id}` | Sí | — | `OrderOut` (con `order_items`) |
| PATCH | `/api/v1/orders/{order_id}/cancel` | Sí | — | `OrderOut` |
| PATCH | `/api/v1/orders/{order_id}/status` | Sí | `OrderStatusUpdate` | `OrderOut` |

### Estructuras expuestas

```python
# OrderCreate
{
  "shipping_address_id": str
}

# OrderStatusUpdate
{
  "status": Literal["paid", "processing", "shipped", "delivered"]
}

# OrderItemOut
{
  "id": str,
  "product_id": str,
  "product_name": str,      # snapshot del nombre al momento de la consulta (join)
  "quantity": int,
  "unit_price": float,      # precio CONGELADO al momento de la compra
  "subtotal": float
}

# OrderOut
{
  "id": str,
  "status": str,
  "shipping_address": AddressOut,
  "subtotal": float,
  "taxes": float,
  "shipping_cost": float,
  "total": float,
  "items": list[OrderItemOut],
  "created_at": datetime
}

# OrderSummaryOut  (para el listado, sin items completos)
{
  "id": str,
  "status": str,
  "total": float,
  "items_count": int,
  "created_at": datetime
}
```

### Errores esperados
- `400` carrito vacío al intentar checkout.
- `404` dirección de envío no existe o no pertenece al usuario.
- `409` stock insuficiente para uno o más productos (detalle de cuáles en el body de error).
- `409` transición de estado inválida (ej. intentar `shipped` desde `pending`).
- `409` intento de cancelar una orden `shipped`/`delivered`.

---

## 9. Reglas transversales (aplican a todos los módulos)

- **Scoping por usuario:** todo recurso de `addresses`, `cart_items`, `orders` se filtra siempre por el `user_id` extraído del JWT (`get_current_user`). Nunca se confía en un `user_id` recibido por body/query.
- **IDs:** todos `varchar(36)` (UUID v4 generado en backend al insertar, vía `str(uuid4())`), nunca autoincrementales.
- **Timestamps:** `created_at` se asigna en el servidor (`default=func.now()`); `updated_at` se actualiza en cada UPDATE (`onupdate=func.now()`).
- **Paginación estándar:** query params `page` (default 1) y `size` (default 20, máx 100), respuesta envuelta en:
  ```python
  {
    "items": [...],
    "page": int,
    "size": int,
    "total": int,
    "pages": int
  }
  ```
- **Formato de error estándar:**
  ```python
  {
    "detail": str,          # mensaje legible
    "error_code": str | None  # opcional, para casos como "INSUFFICIENT_STOCK"
  }
  ```
- **CORS:** habilitado de forma abierta (`allow_origins=["*"]`) dado que es un laboratorio de un solo usuario sin frontend productivo definido aún.
- **Sin soft-delete generalizado:** se usa DELETE real salvo en los casos descritos explícitamente (productos/categorías referenciados en órdenes, que se bloquean en vez de eliminarse).

---

## 10. Orden de construcción recomendado

1. `core/config.py`, `db/base.py`, `db/session.py` → infraestructura base.
2. `models/*` (las 8 entidades) → correr `scripts/init_db.py` contra Neon para crear tablas.
3. `core/security.py` + `schemas/auth.py` + `services/auth_service.py` + `routes_auth.py` → validar login/register end-to-end.
4. `deps.py` (`get_current_user`) → desbloquea todos los módulos protegidos.
5. `users` + `profiles` (más simple, 1:1).
6. `addresses` (introduce la regla de "default exclusivo").
7. `categories` → `products` (dependencia FK).
8. `cart` (depende de `products`).
9. `orders` (el más complejo, depende de `cart`, `products`, `addresses`).

---

## 11. requirements.txt sugerido

```
fastapi
uvicorn[standard]
sqlalchemy>=2.0
pydantic>=2.0
pydantic-settings
python-jose[cryptography]
passlib[argon2]
psycopg2-binary
python-multipart
```