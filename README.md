# Avtoban Stroy — Telegram Bot

Asfalt va yo'l qurilishi zakazlarini avtomatlashtirish tizimi.

## Texnologiyalar

| Qatlam | Stack |
|--------|-------|
| Bot | aiogram 3.7 |
| DB | PostgreSQL 16 + SQLAlchemy 2 |
| Queue | Celery + Redis 7 |
| Migrate | Alembic |
| Deploy | Docker Compose |

## Tezkor ishga tushirish

### 1. Konfiguratsiya

```bash
cp .env.example .env
# .env faylini to'ldiring: BOT_TOKEN, POSTGRES_PASSWORD, SUPER_ADMIN_IDS
```

### 2. Migratsiya va ishga tushirish

```bash
make build
make migrate
make up
make logs
```

### 3. Local ishlab chiqish (Docker'siz)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Postgres va Redis ni alohida ishga tushiring, keyin:
alembic upgrade head
python -m app.main
```

## Loyiha tuzilmasi

```
app/
├── config.py              # Pydantic settings (.env orqali)
├── main.py                # Entry point
├── celery_app.py          # Celery konfiguratsiyasi
├── tasks.py               # Celery tasks (stub — 3-bosqich)
├── db/
│   ├── models.py          # SQLAlchemy ORM modellari
│   └── session.py         # Async engine va session_maker
├── services/
│   └── user_service.py    # Foydalanuvchi CRUD + audit log
└── bot/
    ├── loader.py           # Bot, Dispatcher, RedisStorage
    ├── filters.py          # RoleFilter, ActiveUserFilter
    ├── middlewares/
    │   ├── db.py           # Session har so'rovda ochadi/yopadi
    │   ├── auth.py         # get_or_create user, super_admin auto-promote
    │   └── audit.py        # Har amal logga yoziladi
    ├── keyboards/
    │   └── menus.py        # Har rol uchun klaviatura
    ├── states/
    │   └── registration.py # FSM: telefon, rol tanlash
    └── handlers/
        ├── common.py       # /start /menu /help /cancel
        ├── registration.py # Telefon olish FSM
        ├── klient.py       # Klient menyusi
        ├── master.py       # Master menyusi
        ├── usta.py         # Usta menyusi
        ├── zavod.py        # Zavod menyusi
        ├── shofer.py       # Shofer menyusi
        └── admin/
            └── role_management.py  # Rol berish, bloklash, ro'yxat
```

## Rollar

| Rol | Tavsif |
|-----|--------|
| `super_admin` | To'liq kirish. `.env` dagi `SUPER_ADMIN_IDS` orqali avtomatik |
| `admin` | Barcha zakazlar, moliya, rol boshqaruvi |
| `helper_admin` | Zakazlar va foydalanuvchilar (moliyasiz) |
| `master` | O'z zakazlari, usta tayinlash |
| `usta` | Tayinlangan zakazlar, material so'rash |
| `zavod` | Material so'rovlari, narx kiritish |
| `shofer` | Yetkazilmalar |
| `klient` | Zakaz qoldirish, status ko'rish |

## Middleware ketma-ketligi

```
DbSessionMiddleware  →  AuthMiddleware  →  AuditMiddleware  →  Handler
```

## Bosqichlar

| Bosqich | Funksiyalar | Holat |
|---------|-------------|-------|
| 1 | Infra, DB, Auth, Rol boshqaruvi, Menyular | ✅ |
| 2 | Klient zakaz, Master tasdiqlash, Status mashinasi | ⏳ |
| 3 | Usta engine, 30-daqiqa Celery timer | ⏳ |
| 4 | Moliya, Zavod flow, Bildirishnomalar | ⏳ |
| 5 | Admin panel, Hisobotlar, Excel, Deploy | ⏳ |

## Foydali buyruqlar

```bash
make up            # Ishga tushirish
make down          # To'xtatish
make logs          # Bot loglarini ko'rish
make migrate       # DB migratsiyasini qo'llash
make shell-db      # PostgreSQL shellga kirish
make migrate-create msg="add_column_xyz"  # Yangi migratsiya
```
