"""
Telegram bot handlers for online marketplace (shop) - for KLIENT role
"""
import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.bot.filters import RoleFilter
from app.bot.i18n import ALL_BUTTON_TEXTS
from app.db.models import Category, Product, CartItem, MarketOrder, MarketOrderItem, User, UserRole
from app.db.session import async_session_maker

logger = logging.getLogger(__name__)
router = Router()


class ShopStates(StatesGroup):
    browsing_categories = State()
    browsing_products = State()
    viewing_product = State()
    viewing_cart = State()
    checkout_phone = State()
    checkout_comment = State()


def get_main_shop_keyboard():
    """Main shop menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Mahsulotlar", callback_data="shop:categories")],
        [InlineKeyboardButton(text="🛒 Savat", callback_data="shop:cart")],
        [InlineKeyboardButton(text="📦 Mening buyurtmalarim", callback_data="shop:my_orders")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")],
    ])


def get_categories_keyboard(categories: list):
    """Categories list keyboard."""
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"📁 {cat['name_uz']}",
                callback_data=f"shop:cat:{cat['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="shop:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_products_keyboard(products: list, category_id: int = None):
    """Products list keyboard."""
    buttons = []
    for prod in products:
        price_text = f"{int(prod['price']):,} so'm"
        if prod.get('discount_value'):
            final_price = prod['price']
            if prod['discount_type'] == 'percentage':
                final_price = prod['price'] * (1 - prod['discount_value'] / 100)
            else:
                final_price = max(0, prod['price'] - prod['discount_value'])
            price_text = f"🔥 {int(final_price):,} so'm"
        
        buttons.append([
            InlineKeyboardButton(
                text=f"{prod['name_uz']} - {price_text}",
                callback_data=f"shop:prod:{prod['id']}"
            )
        ])
    
    back_btn = f"shop:cat:{category_id}" if category_id else "shop:categories"
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=back_btn)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_detail_keyboard(product_id: int, in_stock: bool, category_id: int = None):
    """Product detail keyboard with add to cart."""
    buttons = []
    if in_stock:
        buttons.append([
            InlineKeyboardButton(text="➕ Savatga qo'shish", callback_data=f"shop:add:{product_id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="❌ Omborda yo'q", callback_data="noop")
        ])
    
    back_btn = f"shop:cat:{category_id}" if category_id else "shop:categories"
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=back_btn)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cart_keyboard(cart_items: list):
    """Cart items keyboard."""
    buttons = []
    for item in cart_items:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {item['product_name']} ({item['quantity']}x)",
                callback_data=f"shop:remove:{item['id']}"
            )
        ])
    
    if cart_items:
        buttons.append([
            InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="shop:checkout")
        ])
        buttons.append([
            InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="shop:clear_cart")
        ])
    
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="shop:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ══════════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("shop"))
async def cmd_shop(message: Message, state: FSMContext):
    """Open shop main menu."""
    await state.clear()
    await message.answer(
        "🛍 <b>Online Do'kon</b>\n\n"
        "Mahsulotlarni ko'rish, savatga qo'shish va buyurtma berishingiz mumkin.",
        reply_markup=get_main_shop_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_shop", set())))
async def btn_shop(message: Message, state: FSMContext):
    """Open shop from main menu button."""
    await state.clear()
    await message.answer(
        "🛍 <b>Online Do'kon</b>\n\n"
        "Mahsulotlarni ko'rish, savatga qo'shish va buyurtma berishingiz mumkin.",
        reply_markup=get_main_shop_keyboard(),
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACK HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "shop:main")
async def show_shop_main(callback: CallbackQuery, state: FSMContext):
    """Show shop main menu."""
    await state.clear()
    await callback.message.edit_text(
        "🛍 <b>Online Do'kon</b>\n\n"
        "Mahsulotlarni ko'rish, savatga qo'shish va buyurtma berishingiz mumkin.",
        reply_markup=get_main_shop_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "shop:categories")
async def show_categories(callback: CallbackQuery, state: FSMContext):
    """Show product categories."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Category)
            .where(Category.is_active == True, Category.parent_id == None)
            .order_by(Category.order, Category.id)
        )
        categories = result.scalars().all()
        
        cat_list = [
            {
                "id": c.id,
                "name_uz": c.name_uz,
                "name_ru": c.name_ru,
                "name_en": c.name_en,
            }
            for c in categories
        ]
    
    if not cat_list:
        await callback.message.edit_text(
            "❌ Hozircha kategoriyalar mavjud emas.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="shop:main")]
            ])
        )
    else:
        await callback.message.edit_text(
            "📁 <b>Kategoriyalar</b>\n\nKerakli kategoriyani tanlang:",
            reply_markup=get_categories_keyboard(cat_list),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("shop:cat:"))
async def show_category_products(callback: CallbackQuery, state: FSMContext):
    """Show products in a category."""
    category_id = int(callback.data.split(":")[2])
    
    async with async_session_maker() as session:
        # Get category
        category = await session.get(Category, category_id)
        if not category:
            await callback.answer("Kategoriya topilmadi", show_alert=True)
            return
        
        # Get products
        result = await session.execute(
            select(Product)
            .where(Product.category_id == category_id, Product.is_active == True)
            .order_by(Product.is_featured.desc(), Product.created_at.desc())
        )
        products = result.scalars().all()
        
        prod_list = [
            {
                "id": p.id,
                "name_uz": p.name_uz,
                "price": float(p.price),
                "discount_value": float(p.discount_value) if p.discount_value else None,
                "discount_type": p.discount_type,
            }
            for p in products
        ]
    
    if not prod_list:
        await callback.message.edit_text(
            f"📁 <b>{category.name_uz}</b>\n\n❌ Bu kategoriyada mahsulotlar yo'q.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="shop:categories")]
            ]),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"📁 <b>{category.name_uz}</b>\n\nMahsulotni tanlang:",
            reply_markup=get_products_keyboard(prod_list, category_id),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("shop:prod:"))
async def show_product_detail(callback: CallbackQuery, state: FSMContext):
    """Show product details."""
    product_id = int(callback.data.split(":")[2])
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            await callback.answer("Mahsulot topilmadi", show_alert=True)
            return
        
        # Calculate final price
        price = product.price
        discount_text = ""
        if product.discount_value and product.discount_type:
            if product.discount_type == "percentage":
                final_price = price * (1 - product.discount_value / 100)
                discount_text = f"\n🔥 <b>Chegirma:</b> {int(product.discount_value)}%"
            else:
                final_price = max(Decimal(0), price - product.discount_value)
                discount_text = f"\n🔥 <b>Chegirma:</b> {int(product.discount_value):,} so'm"
            price_text = f"<s>{int(price):,}</s> → <b>{int(final_price):,} so'm</b>"
        else:
            price_text = f"<b>{int(price):,} so'm</b>"
        
        description = product.description_uz or "Ma'lumot yo'q"
        stock_text = f"✅ Omborda: {product.stock} dona" if product.stock > 0 else "❌ Omborda yo'q"
        
        text = (
            f"🛍 <b>{product.name_uz}</b>\n\n"
            f"{description}\n\n"
            f"💰 <b>Narx:</b> {price_text}{discount_text}\n"
            f"{stock_text}\n"
        )
        
        if product.category:
            text += f"📁 <b>Kategoriya:</b> {product.category.name_uz}"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_product_detail_keyboard(
                product_id,
                product.stock > 0,
                product.category_id
            ),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("shop:add:"))
async def add_to_cart(callback: CallbackQuery):
    """Add product to cart."""
    product_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    async with async_session_maker() as session:
        # Get user
        user_result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
            return
        
        # Get product
        product = await session.get(Product, product_id)
        if not product or not product.is_active:
            await callback.answer("Mahsulot topilmadi", show_alert=True)
            return
        
        if product.stock <= 0:
            await callback.answer("❌ Mahsulot omborda yo'q", show_alert=True)
            return
        
        # Check if already in cart
        existing = (
            await session.execute(
                select(CartItem).where(
                    CartItem.user_id == user.id,
                    CartItem.product_id == product_id
                )
            )
        ).scalar_one_or_none()
        
        if existing:
            existing.quantity += 1
            await callback.answer(f"✅ {product.name_uz} miqdori oshirildi", show_alert=True)
        else:
            cart_item = CartItem(user_id=user.id, product_id=product_id, quantity=1)
            session.add(cart_item)
            await callback.answer(f"✅ {product.name_uz} savatga qo'shildi", show_alert=True)
        
        await session.commit()


@router.callback_query(F.data == "shop:cart")
async def show_cart(callback: CallbackQuery):
    """Show shopping cart."""
    user_id = callback.from_user.id
    
    async with async_session_maker() as session:
        # Get user
        user_result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
            return
        
        # Get cart items
        cart_items = (
            await session.execute(
                select(CartItem)
                .options(selectinload(CartItem.product))
                .where(CartItem.user_id == user.id)
            )
        ).scalars().all()
        
        if not cart_items:
            await callback.message.edit_text(
                "🛒 <b>Savat bo'sh</b>\n\n"
                "Mahsulotlarni ko'rish uchun 'Mahsulotlar' tugmasini bosing.",
                reply_markup=get_main_shop_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        total = Decimal(0)
        items_list = []
        
        for item in cart_items:
            if item.product and item.product.is_active:
                price = item.product.price
                if item.product.discount_value and item.product.discount_type:
                    if item.product.discount_type == "percentage":
                        price = price * (1 - item.product.discount_value / 100)
                    else:
                        price = max(Decimal(0), price - item.product.discount_value)
                
                subtotal = price * item.quantity
                total += subtotal
                
                items_list.append({
                    "id": item.id,
                    "product_name": item.product.name_uz,
                    "price": price,
                    "quantity": item.quantity,
                    "subtotal": subtotal,
                })
        
        if not items_list:
            await callback.message.edit_text(
                "🛒 <b>Savat bo'sh</b>",
                reply_markup=get_main_shop_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        text = "🛒 <b>Sizning savatiz</b>\n\n"
        for item in items_list:
            text += f"• {item['product_name']}\n"
            text += f"  {item['quantity']} x {int(item['price']):,} = {int(item['subtotal']):,} so'm\n\n"
        
        text += f"💰 <b>Jami:</b> {int(total):,} so'm"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_cart_keyboard(items_list),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("shop:remove:"))
async def remove_from_cart(callback: CallbackQuery):
    """Remove item from cart."""
    cart_item_id = int(callback.data.split(":")[2])
    
    async with async_session_maker() as session:
        cart_item = await session.get(CartItem, cart_item_id)
        if cart_item:
            await session.delete(cart_item)
            await session.commit()
            await callback.answer("✅ Mahsulot savatdan o'chirildi")
            # Refresh cart view
            await show_cart(callback)
        else:
            await callback.answer("Mahsulot topilmadi", show_alert=True)


@router.callback_query(F.data == "shop:clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Clear all items from cart."""
    user_id = callback.from_user.id
    
    async with async_session_maker() as session:
        user_result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
            return
        
        await session.execute(
            select(CartItem).where(CartItem.user_id == user.id)
        )
        
        from sqlalchemy import delete
        await session.execute(delete(CartItem).where(CartItem.user_id == user.id))
        await session.commit()
    
    await callback.message.edit_text(
        "✅ Savat tozalandi",
        reply_markup=get_main_shop_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "shop:checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Start checkout process."""
    await callback.message.edit_text(
        "📱 <b>Buyurtma berish</b>\n\n"
        "Telefon raqamingizni kiriting (masalan: +998901234567):",
        parse_mode="HTML"
    )
    await state.set_state(ShopStates.checkout_phone)
    await callback.answer()


@router.message(ShopStates.checkout_phone)
async def process_checkout_phone(message: Message, state: FSMContext):
    """Process phone number for checkout."""
    phone = message.text.strip()
    
    if not phone.startswith("+998") or len(phone) != 13:
        await message.answer(
            "❌ Noto'g'ri format. Telefon raqamni +998901234567 formatida kiriting."
        )
        return
    
    await state.update_data(phone=phone)
    await message.answer(
        "💬 <b>Izoh (ixtiyoriy)</b>\n\n"
        "Buyurtmaga izoh qoldiring yoki /skip tugmasini bosing:",
        parse_mode="HTML"
    )
    await state.set_state(ShopStates.checkout_comment)


@router.message(ShopStates.checkout_comment)
async def process_checkout_comment(message: Message, state: FSMContext):
    """Process comment and complete checkout."""
    comment = None if message.text == "/skip" else message.text.strip()
    data = await state.get_data()
    phone = data.get("phone")
    user_id = message.from_user.id
    
    async with async_session_maker() as session:
        # Get user
        user_result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            await message.answer("❌ Foydalanuvchi topilmadi")
            await state.clear()
            return
        
        # Get cart items
        cart_items = (
            await session.execute(
                select(CartItem)
                .options(selectinload(CartItem.product))
                .where(CartItem.user_id == user.id)
            )
        ).scalars().all()
        
        if not cart_items:
            await message.answer("❌ Savat bo'sh")
            await state.clear()
            return
        
        # Calculate total and create order items
        total = Decimal(0)
        order_items = []
        
        for item in cart_items:
            if not item.product or not item.product.is_active:
                continue
            
            price = item.product.price
            if item.product.discount_value and item.product.discount_type:
                if item.product.discount_type == "percentage":
                    price = price * (1 - item.product.discount_value / 100)
                else:
                    price = max(Decimal(0), price - item.product.discount_value)
            
            subtotal = price * item.quantity
            total += subtotal
            
            order_items.append(
                MarketOrderItem(
                    product_id=item.product.id,
                    product_name=item.product.name_uz,
                    price=price,
                    quantity=item.quantity,
                    image=item.product.images.split(",")[0] if item.product.images else None,
                )
            )
        
        if not order_items:
            await message.answer("❌ Savat bo'sh")
            await state.clear()
            return
        
        # Create order
        order = MarketOrder(
            user_id=user.id,
            customer_name=user.full_name,
            customer_phone=phone,
            total_price=total,
            comment=comment,
            items=order_items,
        )
        session.add(order)
        
        # Clear cart
        from sqlalchemy import delete as sql_delete
        await session.execute(sql_delete(CartItem).where(CartItem.user_id == user.id))
        
        await session.commit()
        await session.refresh(order)
        
        await message.answer(
            f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
            f"📦 Buyurtma raqami: #{order.id}\n"
            f"💰 Jami: {int(total):,} so'm\n"
            f"📱 Telefon: {phone}\n\n"
            f"Tez orada siz bilan bog'lanamiz!",
            reply_markup=get_main_shop_keyboard(),
            parse_mode="HTML"
        )
    
    await state.clear()


@router.callback_query(F.data == "shop:my_orders")
async def show_my_orders(callback: CallbackQuery):
    """Show user's orders."""
    user_id = callback.from_user.id
    
    async with async_session_maker() as session:
        user_result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
            return
        
        orders = (
            await session.execute(
                select(MarketOrder)
                .options(selectinload(MarketOrder.items))
                .where(MarketOrder.user_id == user.id)
                .order_by(MarketOrder.created_at.desc())
                .limit(10)
            )
        ).scalars().all()
        
        if not orders:
            await callback.message.edit_text(
                "📦 <b>Sizda buyurtmalar yo'q</b>",
                reply_markup=get_main_shop_keyboard(),
                parse_mode="HTML"
            )
        else:
            text = "📦 <b>Mening buyurtmalarim</b>\n\n"
            for order in orders:
                status_emoji = {
                    "new": "🆕",
                    "processing": "⏳",
                    "completed": "✅",
                    "cancelled": "❌"
                }.get(order.status.value, "")
                
                text += (
                    f"{status_emoji} <b>Buyurtma #{order.id}</b>\n"
                    f"💰 {int(order.total_price):,} so'm\n"
                    f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                )
            
            await callback.message.edit_text(
                text,
                reply_markup=get_main_shop_keyboard(),
                parse_mode="HTML"
            )
    
    await callback.answer()
