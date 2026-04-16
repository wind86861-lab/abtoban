"""O'zbek (Lotin) translations."""

STRINGS = {
    # ── Language selection ──
    "choose_language": "🌐 Tilni tanlang / Тилни танланг / Выберите язык:",
    "lang_uz_lat": "🇺🇿 O'zbekcha (Lotin)",
    "lang_uz_cyr": "🇺🇿 Ўзбекча (Кирилл)",
    "lang_ru": "🇷🇺 Русский",
    "language_set": "✅ Til tanlandi: O'zbekcha (Lotin)",

    # ── Common / start ──
    "welcome": "👋 <b>Avtoban Stroy</b> botiga xush kelibsiz!\n\nRo'yxatdan o'tish uchun telefon raqamingizni yuboring:",
    "welcome_back": "👋 Xush kelibsiz, <b>{name}</b>!\n👤 Rolingiz: <b>{role}</b>",
    "your_role": "👤 Rolingiz: <b>{role}</b>\nAsosiy menyu:",
    "help_text": (
        "ℹ️ <b>Avtoban Stroy Bot</b>\n\n"
        "Mavjud buyruqlar:\n"
        "/start — Botni ishga tushirish\n"
        "/menu — Asosiy menyu\n"
        "/help — Yordam\n"
        "/cancel — Amalni bekor qilish\n\n"
        "Muammo bo'lsa: @avtoban_support"
    ),
    "no_action_to_cancel": "Bekor qilish uchun hech qanday amal yo'q.",
    "action_cancelled": "❌ Amal bekor qilindi.",

    # ── Registration ──
    "send_phone": "📱 Telefon raqamni yuborish",
    "registration_success": "✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n👤 Ism: <b>{name}</b>\n📱 Tel: <b>{phone}</b>\n👥 Rol: <b>{role}</b>",
    "phone_wrong_type": "❗ Iltimos, tugmani bosing va telefon raqamingizni yuboring.",

    # ── Menu buttons ──
    "btn_cancel": "❌ Bekor qilish",
    "btn_skip": "⏩ O'tkazib yuborish",
    "btn_back": "⬅️ Orqaga",
    "main_menu": "Asosiy menyu:",
    "btn_change_language": "🌐 Tilni o'zgartirish",

    # ── Klient buttons ──
    "btn_order_create": "📝 Zakaz qoldirish",
    "btn_my_orders": "📋 Mening zakazlarim",
    "btn_calc_price": "🧮 Narx hisoblash",
    "btn_consultation": "📞 Konsultatsiya",
    "btn_about": "ℹ️ Kompaniya haqida",
    "btn_shop": "🛍 Do'kon",

    # ── Admin buttons ──
    "btn_all_orders": "📋 Barcha zakazlar",
    "btn_add_order": "➕ Zakaz qo'shish",
    "btn_users": "👥 Foydalanuvchilar",
    "btn_reports": "📊 Hisobotlar",
    "btn_materials": "📦 Material so'rovlar",
    "btn_finance": "💰 Moliya",
    "btn_settings": "🔧 Sozlamalar",
    "btn_statistics": "📊 Statistika",
    "btn_master_report": "👷 Master hisoboti",
    "btn_usta_report": "🔨 Usta hisoboti",
    "btn_export": "📥 Eksport",

    # ── Master buttons ──
    "btn_new_orders": "🆕 Yangi zakazlar",
    "btn_confirm_order": "✅ Zakaz tasdiqlash",
    "btn_master_my_orders": "📋 Mening zakazlarim",
    "btn_assign_usta": "👷 Usta tayinlash",
    "btn_add_expense": "💸 Xarajat kiritish",
    "btn_master_web_panel": "🌐 Web Panel",

    # ── Usta buttons ──
    "btn_usta_my_orders": "📋 Mening zakazlarim",
    "btn_request_material": "📦 Material so'rash",
    "btn_work_history": "📊 Ish tarixi",

    # ── Zavod buttons ──
    "btn_zavod_materials": "📦 Material so'rovlar",
    "btn_zavod_price": "✅ Narx kiritish",
    "btn_zavod_history": "📋 Tarixi",

    # ── Shofer buttons ──
    "btn_my_deliveries": "🚗 Mening yetkazilmalarim",
    "btn_update_status": "✅ Status yangilash",

    # ── Role labels ──
    "role_super_admin": "Super Admin",
    "role_admin": "Admin",
    "role_helper_admin": "Yordamchi Admin",
    "role_master": "Master",
    "role_usta": "Usta",
    "role_zavod": "Zavod",
    "role_shofer": "Shofer",
    "role_klient": "Klient",

    # ── Status labels ──
    "status_new": "🆕 Yangi",
    "status_confirmed": "✅ Tasdiqlangan",
    "status_in_work": "🔧 Ishda",
    "status_done": "🏁 Tugagan",
    "status_cancelled": "❌ Bekor qilingan",

    # ── General ──
    "not_found": "❌ Topilmadi",
    "error_occurred": "❌ Xatolik yuz berdi.",
    "invalid_number": "❌ Noto'g'ri raqam. Raqam kiriting:",
    "invalid_price": "❌ Noto'g'ri narx. Raqam kiriting:",
    "cancelled": "❌ Bekor qilindi.",
    "confirm_question": "Tasdiqlaysizmi?",
    "nameless": "Nomsiz",
    "active": "Faol",
    "blocked": "Bloklangan",
    "not_assigned": "Tayinlanmagan",
    "filter_all": "Barcha",

    # ── Klient order creation ──
    "order_start": "📝 <b>Zakaz qoldirish</b>\n\n1️⃣ Viloyatni tanlang:",
    "order_no_phone": "❗ Avval telefon raqamingizni ro'yxatdan o'tkazing.\nBuning uchun /start buyrug'ini yuboring.",
    "no_regions": "⚠️ Viloyatlar hali sozlanmagan. Admin bilan bog'laning.",
    "region_selected": "✅ Viloyat tanlandi\n\n2️⃣ Tumanni kiriting:",
    "district_too_short": "❌ Tumanni to'liq kiriting:",
    "enter_street": "3️⃣ Ko'cha nomini kiriting:\n<i>Masalan: Amir Temur ko'chasi</i>",
    "street_too_short": "❌ Ko'cha nomini aniqroq yozing:",
    "enter_target": "4️⃣ Mo'ljal/orientir kiriting:\n<i>Masalan: Maktab yonida, 45-uy</i>",
    "target_too_short": "❌ Mo'ljalni aniqroq yozing:",
    "share_location": "5️⃣ 📍 <b>Lokatsiyangizni yuboring</b>\n\nPastdagi 📎 tugmasini bosing → <b>Location</b> → joylashuvingizni yuboring.",
    "invalid_location": "❌ Iltimos, lokatsiya yuboring. Pastdagi 📎 → Location tugmasini bosing.",
    "enter_area": "📐 Taxminiy maydon hajmini kiriting (<b>m²</b>):\nMisol: <code>500</code>",
    "invalid_area": "❌ Noto'g'ri format. Faqat musbat raqam kiriting (masalan: 500):",
    "no_asphalt_types": "⚠️ Asfalt turlari hali sozlanmagan. Admin bilan bog'laning.",
    "select_asphalt": "🏗 Asfalt turini tanlang:",
    "asphalt_not_found": "❌ Asfalt turi topilmadi",
    "order_summary": (
        "📋 <b>Zakaz ma'lumotlari</b>\n\n"
        "📍 <b>Manzil:</b>\n"
        "   Viloyat: {district}\n"
        "   Ko'cha: {street}\n"
        "   Mo'ljal: {target}\n"
        "{location_link}\n"
        "📐 Maydon: <b>{area} m²</b>\n"
        "🏗 Asfalt: <b>{asphalt}</b>\n"
        "💰 Taxminiy narx: <b>{price} so'm</b>\n\n"
        "Tasdiqlaysizmi?"
    ),
    "order_submitted": "✅ <b>Zakaz qabul qilindi!</b>\n\n🔢 Raqam: <code>{number}</code>\n📍 Manzil: {address}\n{location_link}📐 Maydon: {area} m²\n\nYaqin orada master siz bilan bog'lanadi.",
    "order_cancelled": "❌ Zakaz bekor qilindi.",
    "no_orders": "📋 <b>Mening zakazlarim</b>\n\nSizda hali zakazlar yo'q.\nZakaz qoldirish uchun 📝 tugmasini bosing.",
    "my_orders_header": "📋 <b>Mening zakazlarim:</b>\n",
    "new_order_notify": "🆕 <b>Yangi zakaz!</b>\n\n🔢 #{number}\n👤 {name}\n📱 {phone}\n📍 {address}\n{location_link}📐 {area} m²\n🏗 {asphalt}",

    # ── Price calculator ──
    "calc_start": "🧮 <b>Narx hisoblash</b>\n\n📐 Maydon hajmini kiriting (m²):\nMisol: <code>300</code>",
    "calc_invalid": "❌ Noto'g'ri format. Raqam kiriting:",
    "calc_result": (
        "🧮 <b>Hisob-kitob natijasi</b>\n\n"
        "📐 Maydon: <b>{area} m²</b>\n"
        "🏗 Asfalt: <b>{asphalt}</b>\n"
        "💲 Narx: <b>{price_per_m2} so'm/m²</b>\n"
        "─────────────────\n"
        "💰 Taxminiy jami: <b>{total} so'm</b>\n\n"
        "<i>* Aniq narx master tomonidan belgilanadi</i>"
    ),

    # ── Consultation ──
    "consultation": "📞 <b>Konsultatsiya</b>\n\nOperatorimiz bilan bog'laning:\n📱 <b>+998 XX XXX XX XX</b>\n\n🕒 Ish vaqti: 09:00 — 18:00",
    "about_company": "🏗 <b>Avtoban Stroy</b>\n\nAsfalt va yo'l qurilishi bo'yicha professional xizmat.\n\n📍 Manzil: Toshkent sh.\n📱 Tel: +998 XX XXX XX XX\n🕒 Ish vaqti: 09:00 — 18:00\n\nIshonchli, tez va sifatli!",

    # ── Master ──
    "no_new_orders": "🆕 <b>Yangi zakazlar</b>\n\nHozircha yangi zakazlar yo'q.",
    "new_orders_header": "🆕 <b>Yangi zakazlar</b> ({count} ta)\n\nBatafsil ko'rish uchun tanlang:",
    "order_not_found": "❌ Zakaz topilmadi",
    "order_detail": (
        "📋 <b>Zakaz: {number}</b>\n\n"
        "👤 Klient: <b>{client}</b>\n"
        "📱 Tel: <b>{phone}</b>\n"
        "📍 Manzil: <b>{address}</b>\n"
        "📐 Taxminiy maydon: <b>{area} m²</b>\n"
        "🏗 Asfalt: <b>{asphalt}</b>\n"
        "📅 Yaratildi: <b>{date}</b>\n\n"
        "<i>Tasdiqlash uchun tugmani bosing.</i>"
    ),
    "master_create_start": "➕ <b>Yangi zakaz qo'shish</b>\n\n1️⃣ Klient telefon raqamini kiriting:\nMisol: <code>998901234567</code>",
    "enter_client_name": "2️⃣ Klient ismini kiriting:",
    "invalid_phone": "❌ Noto'g'ri telefon raqam. Qaytadan kiriting:",
    "name_too_short": "❌ Ismni to'liq kiriting:",
    "select_region": "Viloyatni tanlang:",
    "enter_district_num": "Tumanni kiriting:",
    "enter_street_num": "Ko'cha nomini kiriting:\n<i>Masalan: Amir Temur ko'chasi</i>",
    "enter_target_num": "Mo'ljal/orientir kiriting:\n<i>Masalan: Maktab yonida, 45-uy</i>",
    "enter_area_num": "Maydon hajmini kiriting (<b>m²</b>):\nMisol: <code>500</code>",
    "select_asphalt_num": "Asfalt turini tanlang:",
    "master_order_summary": (
        "📋 <b>Zakaz xulosasi</b>\n\n"
        "👤 Klient: <b>{client}</b>\n"
        "📱 Tel: <b>{phone}</b>\n"
        "📍 Manzil: <b>{address}</b>\n"
        "{location_link}"
        "📐 Maydon: <b>{area} m²</b>\n"
        "🏗 Asfalt: <b>{asphalt}</b>\n"
        "💰 Taxminiy narx: <b>{price} so'm</b>\n\n"
        "Tasdiqlaysizmi?"
    ),
    "master_order_created": "✅ <b>Zakaz yaratildi!</b>\n\n🔢 Raqam: <code>{number}</code>\n👤 Klient: {name}\n📍 Manzil: {address}\n{location_link}📐 Maydon: {area} m²\n\nEndi 'Yangi zakazlar' orqali tasdiqlashingiz mumkin.",
    "no_my_orders": "📋 <b>Mening zakazlarim</b>\n\nSizga biriktirilgan zakazlar yo'q.",
    "my_orders_master": "📋 <b>Mening zakazlarim</b> ({count} ta):",

    # ── Master confirmation FSM ──
    "confirm_start": "✅ <b>Zakaz tasdiqlash: {number}</b>\n\n1/8 — Aniq maydon hajmini kiriting (m²):",
    "already_confirmed": "❌ Bu zakaz allaqachon tasdiqlangan!",
    "invalid_positive": "❌ Noto'g'ri. Musbat raqam kiriting (masalan: 450):",
    "enter_sum": "2/8 — Umumiy summani kiriting (so'm):\nMisol: <code>45000000</code>",
    "invalid_sum": "❌ Noto'g'ri summa. Musbat raqam kiriting:",
    "enter_advance": "3/8 — Zaklad (avans) miqdori (so'm):\nMisol: <code>10000000</code>",
    "invalid_advance": "❌ Noto'g'ri. Raqam kiriting (0 bo'lishi mumkin):",
    "enter_address_confirm": "4/8 — Manzilni tasdiqlang yoki o'zgartiring:\nJoriy manzil: <b>{address}</b>\n\nYangi manzil kiriting yoki 'Saqlash' tugmasini bosing:",
    "address_too_short": "❌ Manzil juda qisqa. Aniqroq yozing:",
    "enter_work_date": "5/8 — Ish sanasini kiriting (KK.OO.YYYY):\nMisol: <code>25.04.2026</code>",
    "invalid_date": "❌ Noto'g'ri sana. Format: KK.OO.YYYY  (masalan: 25.04.2026):",
    "enter_usta_wage": "6/8 — Usta ish haqi (so'm):\nMisol: <code>5000000</code>",
    "enter_commission": "7/8 — Sizning komissiyangiz (so'm):\nMisol: <code>2000000</code>",
    "enter_notes": "8/8 — Izoh (ixtiyoriy). Qo'shimcha ma'lumot yozing yoki o'tkazib yuboring:",
    "confirm_summary": (
        "📋 <b>Tasdiqlash xulosasi — {number}</b>\n\n"
        "📐 Maydon: <b>{area} m²</b>\n"
        "💰 Summa: <b>{total} so'm</b>\n"
        "💵 Zaklad: <b>{advance} so'm</b>\n"
        "💳 Qarz: <b>{debt} so'm</b>\n"
        "📍 Manzil: {address}\n"
        "📅 Ish sanasi: {date}\n"
        "👷 Usta haqi: <b>{wage} so'm</b>\n"
        "💼 Komissiya: <b>{commission} so'm</b>\n"
        "📝 Izoh: {notes}\n\n"
        "Tasdiqlaysizmi?"
    ),
    "order_confirmed": "✅ <b>Zakaz muvaffaqiyatli tasdiqlandi!</b>\n\n🔢 #{number}\n⏰ Usta tayinlash uchun 30 daqiqa vaqtingiz bor.\n'👷 Usta tayinlash' tugmasini bosing.",
    "confirm_cancel": "❌ Tasdiqlash bekor qilindi.",
    "confirm_error": "❌ Xatolik: zakaz allaqachon boshqasi tomonidan tasdiqlangan yoki topilmadi.",
    "order_confirmed_notify": "✅ <b>Zakaz tasdiqlandi!</b>\n\n🔢 #{number}\n👷 Master: {master}\n💰 Summa: {total} so'm\n⏰ Usta tayinlash muddati: 30 daqiqa",
    "status_updated": "✅ Status yangilandi",
    "invalid_status": "❌ Noto'g'ri status",

    # ── Usta assignment ──
    "no_usta_orders": "👷 <b>Usta tayinlash</b>\n\nHozircha usta tayin qilinishi kerak bo'lgan zakazlar yo'q.\n(Yangi zakazni tasdiqlagandan so'ng shu yerda ko'rinadi)",
    "usta_orders_header": "👷 <b>Usta tayinlash</b>\n\n{count} ta zakaz usta kutmoqda.\nTanlang:",
    "no_available_ustas": "⚠️ <b>Mavjud usta yo'q</b>\n\nBarcha ustalar band (2/2 zakaz) yoki faol emas.\n30 daqiqa o'tsa avtomatik tayinlanadi.",
    "select_usta": "👷 <b>Usta tanlang</b>\n\nZakaz: #{number}\n📐 {area} m²  🏗 {asphalt}\n\nMavjud ustalar ({count} ta):",
    "usta_assigned": "✅ <b>Usta tayinlandi!</b>\n\nZakaz: #{number}\n👷 Usta: {usta}\n\nUsta bildirishnoma oldi.",
    "usta_assigned_notify": "👷 <b>Sizga zakaz tayinlandi!</b>\n\n🔢 #{number}\n📍 {address}\n📐 {area} m²  🏗 {asphalt}\n📅 Ish sanasi: {date}\n💰 Usta haqi: {wage} so'm\n\nQabul qilasizmi?",
    "back_usta_no_orders": "👷 Usta tayinlanishi kerak bo'lgan zakazlar yo'q.",
    "back_usta_header": "👷 <b>Usta tayinlash</b> — {count} ta zakaz:",

    # ── Usta ──
    "usta_no_orders": "📋 <b>Mening zakazlarim</b>\n\nSizga hali zakaz biriktirilmagan.\nBildirishnoma kelganda avtomatik ko'rinadi.",
    "usta_orders_list": "📋 <b>Mening zakazlarim</b> ({count} ta):\n",
    "usta_accepted": "✅ <b>Zakaz qabul qilindi!</b>\n\n🔢 #{number}\n📍 {address}\n{location_link}📐 {area} m²  🏗 {asphalt}\n📅 Ish sanasi: {date}\n💰 Usta haqi: {wage} so'm",
    "usta_accepted_notify": "✅ <b>Usta zakazni qabul qildi!</b>\n\nZakaz: #{number}\n👷 Usta: {usta}",
    "assignment_not_yours": "❌ Bu zakaz sizga tayinlanmagan yoki allaqachon boshqa usta qabul qildi.",
    "usta_declined": "❌ Zakaz rad etildi.",
    "usta_declined_notify": "❌ <b>Usta zakazni rad etdi!</b>\n\nZakaz: #{number}\n👷 {usta} rad etdi.\n\nYangi usta tayinlang: '👷 Usta tayinlash'",

    # ── Material request ──
    "material_start": "📦 <b>Material so'rash</b>\n\nQaysi zakaz uchun so'raysiz?",
    "material_no_active": "📦 <b>Material so'rash</b>\n\nFaol zakaz yo'q. Avval zakazni qabul qiling.",
    "material_enter_tonnes": "📦 Kerakli material miqdorini kiriting (<b>tonna</b>):\nMisol: <code>12.5</code>",
    "material_invalid_tonnes": "❌ Noto'g'ri miqdor. Musbat raqam kiriting (masalan: 12.5):",
    "material_enter_notes": "📝 Izoh yoki qo'shimcha ma'lumot (ixtiyoriy):",
    "material_summary": "📦 <b>Material so'rov xulosasi</b>\n\n📐 Miqdor: <b>{tonnes} tonna</b>\n📝 Izoh: {notes}\n\nYuborasizmi?",
    "material_submitted": "✅ <b>So'rov yuborildi!</b>\n\n📦 {tonnes} tonna\nAdmin tekshirib, zavodga yuboradi.",
    "material_cancelled": "❌ So'rov bekor qilindi.",
    "material_new_notify": "📦 <b>Yangi material so'rov!</b>\n\n🔢 So'rov #{id}\n📍 Viloyat: {region}\n👷 Usta: {usta}\n📦 Miqdor: <b>{tonnes} tonna</b>\n📝 Izoh: {notes}\n\n⚠️ Tasdiqlash kerak!",

    # ── Work history ──
    "no_work_history": "📊 <b>Ish tarixi</b>\n\nHali yakunlangan ish yo'q.",
    "work_history_header": "📊 <b>Ish tarixi</b> ({count} ta):\n",

    # ── Zavod ──
    "zavod_no_pending": "📦 <b>Kelgan so'rovlar</b>\n\nHozircha yangi so'rov yo'q.",
    "zavod_pending_header": "📦 <b>Kelgan so'rovlar</b> ({count} ta)\n\nTanlang:",
    "zavod_no_pending_short": "📦 Yangi so'rov yo'q.",
    "zavod_pending_header_short": "📦 <b>Kelgan so'rovlar</b> ({count} ta):",
    "zavod_request_not_found": "❌ So'rov topilmadi",
    "zavod_request_detail": "📦 <b>Material so'rov #{id}</b>\n\n🔢 Zakaz: {order}\n👷 Usta: {usta}\n📦 Miqdor: <b>{tonnes} tonna</b>\n📝 Izoh: {notes}\n📅 Sana: {date}",
    "zavod_enter_material_price": "1/3 — Material narxini kiriting (so'm):\nMisol: <code>8500000</code>",
    "zavod_enter_delivery_price": "2/3 — Dostavka narxini kiriting (so'm):\nMisol: <code>500000</code>",
    "zavod_enter_extra_cost": "3/3 — Qo'shimcha xarajat (so'm). Yo'q bo'lsa 0 kiriting:",
    "zavod_invalid_price": "❌ Noto'g'ri narx. Raqam kiriting:",
    "zavod_invalid_delivery": "❌ Noto'g'ri narx. Raqam kiriting (0 bo'lishi mumkin):",
    "zavod_invalid_extra": "❌ Noto'g'ri. Raqam kiriting (0 bo'lishi mumkin):",
    "zavod_price_summary": "💰 <b>Narx xulosasi</b>\n\n🏗 Material: <b>{material} so'm</b>\n🚚 Dostavka: <b>{delivery} so'm</b>\n➕ Qo'shimcha: <b>{extra} so'm</b>\n─────────────────\n💰 Jami: <b>{total} so'm</b>\n\nTasdiqlaysizmi?",
    "zavod_price_set": "✅ <b>Narx belgilandi!</b>\n\n📦 {tonnes} tonna — {total} so'm\nUsta va shoferlar xabardor qilindi.",
    "zavod_price_error": "❌ Xatolik: so'rov allaqachon narxlangan yoki topilmadi.",
    "zavod_price_cancelled": "❌ Bekor qilindi.",
    "zavod_price_notify_usta": "💰 <b>Material narxi belgilandi!</b>\n\n📦 {tonnes} tonna\n🏗 Material: {material} so'm\n🚚 Dostavka: {delivery} so'm\n➕ Qo'shimcha: {extra} so'm\n💰 Jami: {total} so'm\n\nYetkazib berish tashkil etilmoqda.",
    "zavod_delivery_task": "🚚 <b>Yetkazish topshirig'i!</b>\n\n📦 {tonnes} tonna material\n📝 Zakaz: {order}\n\nYetkazib berdingizmi?",
    "zavod_no_history": "📋 Yetkazish kutilayotgan so'rovlar yo'q.",
    "zavod_history_header": "🚚 <b>Yetkazish kutilayotganlar</b> ({count} ta):",
    "zavod_delivered": "✅ Yetkazildi deb belgilandi!",
    "zavod_delivered_detail": "✅ <b>Yetkazildi!</b>\n\n📦 {tonnes} tonna\nUsta xabardor qilindi.",
    "zavod_deliver_error": "❌ So'rov topilmadi yoki allaqachon yetkazilgan.",
    "material_delivered_notify": "📦 <b>Material yetkazildi!</b>\n\n📦 {amount} tonna\nIsh boshlashingiz mumkin!",

    # ── Shofer ──
    "shofer_no_deliveries": "🚗 <b>Mening yetkazilmalarim</b>\n\nHozircha yetkazish kerak bo'lgan material yo'q.",
    "shofer_active_header": "🚗 <b>Faol topshiriqlar</b> ({count} ta):\n",
    "shofer_not_found": "❌ So'rov topilmadi.",
    "shofer_already_delivered": "ℹ️ Bu allaqachon yetkazilgan.",
    "shofer_not_priced": "❌ Narx hali belgilanmagan.",
    "shofer_confirmed": "✅ <b>Yetkazildi deb tasdiqlandi!</b>\n\n📦 {tonnes} tonna material\nUsta xabardor qilindi.",

    # ── Admin materials ──
    "admin_materials_header": "📦 <b>Material so'rovlar</b> ({count} ta)\n\nTasdiqlash kerak:",
    "admin_materials_empty": "📦 <b>Material so'rovlar</b>\n\nTasdiqlash kutayotgan so'rovlar yo'q.",
    "admin_material_detail": "📦 <b>Material so'rov #{id}</b>\n\n🔢 Zakaz: {order}\n📍 Viloyat: {region}\n👷 Usta: {usta}\n📦 Miqdor: <b>{tonnes} tonna</b>\n📝 Izoh: {notes}\n📅 Sana: {date}\n\nTasdiqlaysizmi?",
    "admin_material_approved": "✅ <b>So'rov tasdiqlandi!</b>\n\n📦 {tonnes} tonna\n📍 Viloyat: {region}\nZavod xabardor qilindi ({count} ta).",
    "admin_material_rejected": "❌ <b>So'rov rad etildi</b>\n\nUsta xabardor qilindi.",
    "admin_material_reject_notify": "❌ <b>Material so'rov rad etildi</b>\n\n📦 {tonnes} tonna\nAdmin tomonidan rad etildi.",
    "admin_material_approve_notify": "📦 <b>Yangi material so'rov!</b>\n\n🔢 So'rov #{id}\n📍 Viloyat: {region}\n👷 Usta: {usta}\n📦 Miqdor: <b>{tonnes} tonna</b>\n📝 Izoh: {notes}",
    "admin_materials_empty_short": "📦 Tasdiqlash kutayotgan so'rovlar yo'q.",

    # ── Admin users ──
    "users_manage": "👥 <b>Foydalanuvchilarni boshqarish</b>\n\nNimani qilmoqchisiz?",
    "search_by_id": "🔍 ID bo'yicha qidirish",
    "all_users": "📋 Barcha foydalanuvchilar",
    "enter_telegram_id": "🔍 Foydalanuvchining <b>Telegram ID</b> sini yuboring:\n\n<i>ID ni olish uchun foydalanuvchi @userinfobot ga /start yozsin.</i>",
    "invalid_telegram_id": "❌ Noto'g'ri format. Faqat raqam kiriting (masalan: <code>123456789</code>):",
    "user_not_found": "❌ Bu Telegram ID bilan foydalanuvchi topilmadi.\nFoydalanuvchi botga /start bosgan bo'lishi kerak.",
    "user_detail": (
        "👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
        "🆔 TG ID: <code>{tg_id}</code>\n"
        "👤 Ism: <b>{name}</b>\n"
        "📱 Tel: <b>{phone}</b>\n"
        "👥 Rol: <b>{role}</b>\n"
        "📍 Viloyat: <b>{region}</b>\n"
        "Holat: {status_icon} {status_text}\n"
        "📅 Ro'yxat: <b>{date}</b>"
    ),
    "select_new_role": "👥 Yangi rol tanlang:",
    "role_changed": "✅ Rol muvaffaqiyatli o'zgartirildi!\n\n👤 <b>{name}</b>\n👥 Yangi rol: <b>{role}</b>",
    "role_changed_notify": "🔔 <b>Rolingiz o'zgartirildi!</b>\n\n👥 Yangi rol: <b>{role}</b>\n\nYangi menyu yuklandi.",
    "cannot_block_self": "❌ O'zingizni bloklashingiz mumkin emas!",
    "cannot_block_super_admin": "❌ Super adminni bloklay olmaysiz!",
    "cannot_assign_super_admin": "❌ Siz super admin tayinlay olmaysiz!",
    "user_activated": "faollashtirildi",
    "user_blocked": "bloklandi",
    "users_list_header": "👥 <b>Foydalanuvchilar</b> (sahifa {page})\n",
    "users_not_found": "👥 Foydalanuvchilar topilmadi.",
    "select_region_admin": "📍 Viloyatni tanlang:",
    "region_changed": "✅ Viloyat o'zgartirildi!",
    "no_regions_admin": "⚠️ Viloyatlar hali sozlanmagan.",

    # ── Admin orders ──
    "orders_header": "📋 <b>Zakazlar ({filter})</b> — {total} ta\nSahifa {page}/{pages}\n",
    "orders_empty": "Zakazlar topilmadi.",
    "admin_create_start": "➕ <b>Yangi zakaz qo'shish</b>\n\n1/5 — Klientning telefon raqamini kiriting:\nMisol: <code>+998901234567</code>",
    "invalid_phone_short": "❌ Noto'g'ri raqam. Qaytadan kiriting:",
    "client_found": "✅ Klient topildi: <b>{name}</b>\n\n2/5 — Manzilni kiriting:",
    "client_not_found_enter_name": "⚠️ Bu raqam bilan foydalanuvchi topilmadi.\n\n1.5/5 — Klient ismini kiriting:",
    "name_too_short_admin": "❌ Ism juda qisqa:",
    "client_created": "✅ Klient yaratildi: <b>{name}</b>\n\n2/5 — Manzilni kiriting:",
    "address_too_short_admin": "❌ Manzil juda qisqa:",
    "enter_area_admin": "3/5 — Maydon hajmini kiriting (m²):\nMisol: <code>500</code>",
    "select_asphalt_admin": "4/5 — Asfalt turini tanlang:",
    "no_asphalt_admin": "⚠️ Asfalt turlari yo'q. Avval sozlamalarda qo'shing.",
    "admin_order_summary": (
        "📋 <b>Yangi zakaz xulosasi</b>\n\n"
        "👤 Klient: <b>{client}</b>\n"
        "📱 Tel: <b>{phone}</b>\n"
        "📍 Manzil: {address}\n"
        "{location_link}"
        "📐 Maydon: <b>{area} m²</b>\n"
        "🏗 Asfalt: <b>{asphalt}</b>\n"
        "💰 Taxminiy: <b>{price} so'm</b>\n\n"
        "Tasdiqlaysizmi?"
    ),
    "admin_order_created": "✅ <b>Zakaz yaratildi!</b>\n\n🔢 Raqam: <code>{number}</code>\n👤 Klient: {client}\n📍 Manzil: {address}\n{location_link}",
    "admin_order_notify": "🆕 <b>Yangi zakaz (admin tomonidan)!</b>\n\n🔢 #{number}\n👤 {client} | {phone}\n📍 {address}\n{location_link}📐 {area} m²",
    "change_status": "🔄 Yangi statusni tanlang:",

    # ── Admin settings ──
    "settings_menu": "🔧 <b>Sozlamalar</b>\n\nNimani sozlamoqchisiz?",
    "asphalt_types_btn": "🏗 Asfalt turlari",
    "no_asphalt_types_admin": "🏗 Asfalt turlari yo'q.\nYangi qo'shing:",
    "asphalt_types_header": "🏗 <b>Asfalt turlari</b>\nBoshqarish uchun tanlang:",
    "add_asphalt": "➕ Yangi qo'shish",
    "enter_asphalt_name": "🏗 Yangi asfalt turi nomini kiriting:\nMisol: <code>Issiq asfalt</code>, <code>Sovuq asfalt</code>",
    "asphalt_name_short": "❌ Ism juda qisqa. Qaytadan kiriting:",
    "enter_asphalt_price": "💰 <b>{name}</b> uchun m² narxini kiriting (so'm):\nMisol: <code>85000</code>",
    "invalid_asphalt_price": "❌ Noto'g'ri narx. Raqam kiriting (masalan: 85000):",
    "asphalt_added": "✅ Asfalt turi qo'shildi!\n\n🏗 Nom: <b>{name}</b>\n💰 Narx: <b>{price} so'm/m²</b>",
    "enter_new_price": "💰 Yangi narxni kiriting (so'm):\nMisol: <code>90000</code>",
    "price_updated": "✅ Narx yangilandi!\n\n🏗 {name}: <b>{price} so'm/m²</b>",
    "asphalt_not_found_admin": "❌ Asfalt turi topilmadi.",

    # ── Reports ──
    "period_today": "Bugun",
    "period_week": "Bu hafta",
    "period_month": "Bu oy",
    "period_all": "Hammasi",
    "statistics_header": (
        "📊 <b>Umumiy statistika</b>\n\n"
        "📦 Jami zakazlar: <b>{total}</b>\n"
        "  🆕 Yangi: {new}\n"
        "  ✅ Tasdiqlangan: {confirmed}\n"
        "  🔧 Ishda: {in_work}\n"
        "  🏁 Yakunlangan: {done}\n"
        "  ❌ Bekor: {cancelled}\n\n"
        "💰 Jami tushum: <b>{revenue} so'm</b>\n"
        "💵 Yig'ilgan: <b>{collected} so'm</b>\n"
        "💳 Umumiy qarz: <b>{debt} so'm</b>\n\n"
        "📅 <b>Bu oy:</b>\n"
        "  Zakazlar: <b>{month_total}</b>\n"
        "  Tushum: <b>{month_revenue} so'm</b>"
    ),
    "master_report_menu": "👷 <b>Master hisoboti</b>\n\nDavrni tanlang:",
    "master_report_empty": "👷 <b>Master hisoboti</b> — {period}\n\nMa'lumot yo'q.",
    "master_report_header": "👷 <b>Master hisoboti</b> — {period}\n",
    "usta_report_menu": "🔨 <b>Usta hisoboti</b>\n\nDavrni tanlang:",
    "usta_report_empty": "🔨 <b>Usta hisoboti</b> — {period}\n\nMa'lumot yo'q.",
    "usta_report_header": "🔨 <b>Usta hisoboti</b> — {period}\n",

    # ── Payments ──
    "payment_menu": "💵 <b>To'lovni yangilash</b>\n\nNimani qilmoqchisiz?",
    "enter_payment": "💵 To'lov summasini kiriting (so'm):\nMisol: <code>5000000</code>",
    "payment_added": "✅ <b>To'lov kiritildi!</b>\n\nZakaz: #{number}\n💵 Qo'shildi: {amount} so'm\n💰 Jami to'langan: {total} so'm\n💳 Qarz: {debt} so'm",
    "payment_full_done": "✅ <b>To'liq to'landi va yakunlandi!</b>\n\nZakaz: #{number}\n💰 {total} so'm to'liq qabul qilindi.",

    # ── Expenses ──
    "expense_start": "💸 <b>Xarajat kiritish</b>\n\nQaysi zakaz uchun?",
    "expense_no_active": "💸 <b>Xarajat kiritish</b>\n\nFaol zakaz yo'q.",
    "expense_select_type": "💸 Xarajat turini tanlang:",
    "expense_enter_amount": "💰 Summasini kiriting (so'm):\nMisol: <code>250000</code>",
    "expense_invalid_amount": "❌ Noto'g'ri summa. Raqam kiriting:",
    "expense_enter_desc": "📝 Izoh kiriting (ixtiyoriy):\n'⏩' bosing o'tkazib yuborish uchun.",
    "expense_added": "✅ <b>Xarajat kiritildi!</b>\n\n{label}: <b>{amount} so'm</b>\n📝 {desc}",
    "expense_cancelled": "❌ Xarajat kiritish bekor qilindi.",
    "no_expenses": "📋 Bu zakaz uchun xarajat kiritilmagan.",
    "expenses_header": "💸 <b>Xarajatlar</b> (jami: {total} so'm):\n",

    # ── Export ──
    "export_menu": "📥 <b>Excel eksport</b>\n\nQaysi ma'lumotni yuklab olmoqchisiz?",
    "export_orders_month": "📋 Zakazlar (bu oy)",
    "export_orders_all": "📋 Zakazlar (hammasi)",
    "export_expenses_month": "💸 Xarajatlar (bu oy)",
    "export_materials_month": "📦 Material so'rovlar (bu oy)",
    "export_preparing": "⏳ Fayl tayyorlanmoqda...",

    # ── Standalone labels (used in detail views) ──
    "order": "Zakaz",
    "client": "Klient",
    "phone": "Tel",
    "address": "Manzil",
    "area": "Maydon",
    "asphalt": "Asfalt",
    "created": "Yaratildi",
    "total": "Summa",
    "advance": "Zaklad",
    "debt": "Qarz",
    "status": "Holat",
    "usta": "Usta",
    "work_date": "Ish sanasi",
    "press_to_confirm": "Tasdiqlash uchun tugmani bosing.",

    # ── Button aliases ──
    "btn_material_requests": "📦 Material so'rovlar",
    "btn_set_price": "✅ Narx kiritish",

    # ── Master handler aliases ──
    "new_orders_list": "🆕 <b>Yangi zakazlar</b> ({count} ta)\n\nBatafsil ko'rish uchun tanlang:",
    "master_order_start": "➕ <b>Yangi zakaz qo'shish</b>\n\n1️⃣ Klient telefon raqamini kiriting:\nMisol: <code>998901234567</code>",
    "master_no_orders": "📋 <b>Mening zakazlarim</b>\n\nSizga biriktirilgan zakazlar yo'q.",
    "master_orders_list": "📋 <b>Mening zakazlarim</b> ({count} ta):",
    "confirm_step_area": "✅ <b>Zakaz tasdiqlash: {number}</b>\n\n1/8 — Aniq maydon hajmini kiriting (m²):",
    "confirm_step_sum": "2/8 — Umumiy summani kiriting (so'm):\nMisol: <code>45000000</code>",
    "confirm_step_advance": "3/8 — Zaklad (avans) miqdori (so'm):\nMisol: <code>10000000</code>",
    "confirm_step_address": "4/8 — Manzilni tasdiqlang yoki o'zgartiring:\nJoriy manzil: <b>{address}</b>\n\nYangi manzil kiriting yoki '📍 Saqlash' tugmasini bosing:",
    "confirm_step_date": "5/8 — Ish sanasini kiriting (KK.OO.YYYY):\nMisol: <code>25.04.2026</code>",
    "confirm_step_usta_wage": "6/8 — Usta ish haqi (so'm):\nMisol: <code>5000000</code>",
    "confirm_step_commission": "7/8 — Sizning komissiyangiz (so'm):\nMisol: <code>2000000</code>",
    "confirm_step_notes": "8/8 — Izoh (ixtiyoriy). Qo'shimcha ma'lumot yozing yoki o'tkazib yuboring:",
    "order_confirmed_success": "✅ <b>Zakaz muvaffaqiyatli tasdiqlandi!</b>\n\n🔢 #{number}\n⏰ Usta tayinlash uchun 30 daqiqa vaqtingiz bor.\n'👷 Usta tayinlash' tugmasini bosing.",
    "confirm_cancelled": "❌ Tasdiqlash bekor qilindi.",
    "no_usta_pending": "👷 <b>Usta tayinlash</b>\n\nHozircha usta tayin qilinishi kerak bo'lgan zakazlar yo'q.\n(Yangi zakazni tasdiqlagandan so'ng shu yerda ko'rinadi)",
    "usta_assign_list": "👷 <b>Usta tayinlash</b>\n\n{count} ta zakaz usta kutmoqda.\nTanlang:",
    "no_ustas_available": "⚠️ <b>Mavjud usta yo'q</b>\n\nBarcha ustalar band yoki faol emas.",
    "usta_assignment_notify": "👷 <b>Sizga zakaz tayinlandi!</b>\n\n🔢 #{number}\n📍 {address}\n📐 {area} m²  🏗 {asphalt}\n📅 Ish sanasi: {date}\n💰 Usta haqi: {wage} so'm\n\nQabul qilasizmi?",
    "usta_assigned_success": "✅ <b>Usta tayinlandi!</b>\n\nZakaz: #{number}\n👷 Usta: {usta}",

    # ── Zavod handler aliases ──
    "no_pending_requests": "📦 <b>Kelgan so'rovlar</b>\n\nHozircha yangi so'rov yo'q.",
    "pending_requests_list": "📦 <b>Kelgan so'rovlar</b> ({count} ta)\n\nTanlang:",
    "request_not_found": "❌ So'rov topilmadi",
    "material_request_detail": "📦 <b>Material so'rov #{id}</b>\n\n🔢 Zakaz: {order}\n👷 Usta: {usta}\n📦 Miqdor: <b>{amount} tonna</b>\n📝 Izoh: {notes}\n📅 Sana: {date}",
    "price_step_material": "1/3 — Material narxini kiriting (so'm):\nMisol: <code>8500000</code>",
    "price_step_delivery": "2/3 — Dostavka narxini kiriting (so'm):\nMisol: <code>500000</code>",
    "price_step_extra": "3/3 — Qo'shimcha xarajat (so'm). Yo'q bo'lsa 0 kiriting:",
    "price_summary": "💰 <b>Narx xulosasi</b>\n\n🏗 Material: <b>{material} so'm</b>\n🚚 Dostavka: <b>{delivery} so'm</b>\n➕ Qo'shimcha: <b>{extra} so'm</b>\n─────────────────\n💰 Jami: <b>{total} so'm</b>\n\nTasdiqlaysizmi?",
    "price_error": "❌ Xatolik: so'rov allaqachon narxlangan yoki topilmadi.",
    "material_price_set_notify": "💰 <b>Material narxi belgilandi!</b>\n\n📦 {amount} tonna\n🏗 Material: {material} so'm\n🚚 Dostavka: {delivery} so'm\n➕ Qo'shimcha: {extra} so'm\n💰 Jami: {total} so'm\n\nYetkazib berish tashkil etilmoqda.",
    "delivery_task_notify": "🚚 <b>Yetkazish topshirig'i!</b>\n\n📦 {amount} tonna material\n📝 Zakaz: {order}\n\nYetkazib berdingizmi?",
    "price_set_success": "✅ <b>Narx belgilandi!</b>\n\n📦 {amount} tonna — {total} so'm\nUsta va shoferlar xabardor qilindi.",
    "no_priced_requests": "📋 Yetkazish kutilayotgan so'rovlar yo'q.",
    "priced_requests_list": "🚚 <b>Yetkazish kutilayotganlar</b> ({count} ta):",
    "deliver_error": "❌ So'rov topilmadi yoki allaqachon yetkazilgan.",
    "delivered_marked": "✅ Yetkazildi deb belgilandi!",
    "delivered_success": "✅ <b>Yetkazildi!</b>\n\n📦 {amount} tonna\nUsta xabardor qilindi.",

    # ── Shofer handler aliases ──
    "no_deliveries": "🚗 <b>Mening yetkazilmalarim</b>\n\nHozircha yetkazish kerak bo'lgan material yo'q.",
    "active_deliveries": "🚗 <b>Faol topshiriqlar</b> ({count} ta):\n",
    "already_delivered": "ℹ️ Bu allaqachon yetkazilgan.",
    "not_priced_yet": "❌ Narx hali belgilanmagan.",
    "delivery_confirmed": "✅ <b>Yetkazildi deb tasdiqlandi!</b>\n\n📦 {amount} tonna material\nUsta xabardor qilindi.",

    "btn_web_panel": "🌐 Web panel",

    # ── Region / viloyat ──
    "no_regions": "⚠️ Viloyatlar hali sozlanmagan. Admin bilan bog'laning.",
    "select_region": "📍 Viloyatni tanlang:",
    "region_selected": "✅ Viloyat tanlandi.\n\nEndi tumanni tanlang yoki kiriting:",
}
