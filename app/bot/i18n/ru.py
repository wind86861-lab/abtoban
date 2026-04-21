"""Русский translations."""

STRINGS = {
    # ── Language selection ──
    "choose_language": "🌐 Выберите язык / Tilni tanlang / Тилни танланг:",
    "lang_uz_lat": "🇺🇿 O'zbekcha (Lotin)",
    "lang_uz_cyr": "🇺🇿 Ўзбекча (Кирилл)",
    "lang_ru": "🇷🇺 Русский",
    "language_set": "✅ Язык выбран: Русский",

    # ── Common / start ──
    "welcome": "👋 Добро пожаловать в бот <b>Avtoban Stroy</b>!\n\nДля регистрации отправьте свой номер телефона:",
    "welcome_back": "👋 Добро пожаловать, <b>{name}</b>!\n👤 Ваша роль: <b>{role}</b>",
    "your_role": "👤 Ваша роль: <b>{role}</b>\nГлавное меню:",
    "help_text": (
        "ℹ️ <b>Avtoban Stroy Bot</b>\n\n"
        "Доступные команды:\n"
        "/start — Запустить бота\n"
        "/menu — Главное меню\n"
        "/help — Помощь\n"
        "/cancel — Отменить действие\n\n"
        "Проблемы: @avtoban_support"
    ),
    "no_action_to_cancel": "Нечего отменять.",
    "action_cancelled": "❌ Действие отменено.",

    # ── Registration ──
    "send_phone": "📱 Отправить номер телефона",
    "registration_success": "✅ Регистрация прошла успешно!\n\n👤 Имя: <b>{name}</b>\n📱 Тел: <b>{phone}</b>\n👥 Роль: <b>{role}</b>",
    "phone_wrong_type": "❗ Пожалуйста, нажмите кнопку и отправьте свой номер телефона.",

    # ── Menu buttons ──
    "btn_cancel": "❌ Отменить",
    "btn_skip": "⏩ Пропустить",
    "btn_back": "⬅️ Назад",
    "main_menu": "Главное меню:",
    "btn_change_language": "🌐 Сменить язык",

    # ── Klient buttons ──
    "btn_order_create": "📝 Оставить заказ",
    "btn_my_orders": "📋 Мои заказы",
    "btn_calc_price": "🧮 Рассчитать цену",
    "btn_consultation": "📞 Консультация",
    "btn_about": "ℹ️ О компании",
    "btn_shop": "🛍 Магазин",

    # ── Admin buttons ──
    "btn_all_orders": "📋 Все заказы",
    "btn_add_order": "➕ Добавить заказ",
    "btn_users": "👥 Пользователи",
    "btn_reports": "📊 Отчёты",
    "btn_materials": "📦 Заявки на материалы",
    "btn_finance": "💰 Финансы",
    "btn_settings": "🔧 Настройки",
    "btn_statistics": "📊 Статистика",
    "btn_master_report": "👷 Отчёт мастеров",
    "btn_usta_report": "🔨 Отчёт мастеров-исполнителей",
    "btn_export": "📥 Экспорт",

    # ── Master buttons ──
    "btn_new_orders": "🆕 Новые заказы",
    "btn_confirm_order": "✅ Подтвердить заказ",
    "btn_master_my_orders": "📋 Мои заказы",
    "btn_assign_usta": "👷 Назначить мастера",
    "btn_add_expense": "💸 Добавить расход",
    "btn_master_web_panel": "🌐 Веб Панель",
    "btn_change_password": "⚙️ Изменить Пароль",

    # ── Usta buttons ──
    "btn_usta_my_orders": "📋 Мои заказы",
    "btn_request_material": "📦 Запросить материал",
    "btn_work_history": "📊 История работ",

    # ── Zavod buttons ──
    "btn_zavod_materials": "📦 Заявки на материалы",
    "btn_zavod_price": "✅ Указать цену",
    "btn_zavod_history": "📋 История",

    # ── Shofer buttons ──
    "btn_my_deliveries": "🚗 Мои доставки",
    "btn_update_status": "✅ Обновить статус",

    # ── Role labels ──
    "role_super_admin": "Супер Админ",
    "role_admin": "Админ",
    "role_helper_admin": "Помощник Админа",
    "role_master": "Мастер",
    "role_usta": "Мастер-исполнитель",
    "role_zavod": "Завод",
    "role_shofer": "Водитель",
    "role_klient": "Клиент",

    # ── Status labels ──
    "status_new": "🆕 Новый",
    "status_confirmed": "✅ Подтверждён",
    "status_in_work": "🔧 В работе",
    "status_done": "🏁 Завершён",
    "status_cancelled": "❌ Отменён",

    # ── General ──
    "not_found": "❌ Не найдено",
    "error_occurred": "❌ Произошла ошибка.",
    "invalid_number": "❌ Неправильное число. Введите число:",
    "invalid_price": "❌ Неправильная цена. Введите число:",
    "cancelled": "❌ Отменено.",
    "confirm_question": "Подтверждаете?",
    "nameless": "Без имени",
    "active": "Активен",
    "blocked": "Заблокирован",
    "not_assigned": "Не назначен",
    "filter_all": "Все",

    # ── Klient order creation ──
    "order_start": "📝 <b>Оставить заказ</b>\n\n1️⃣ Выберите область:",
    "order_no_phone": "❗ Сначала зарегистрируйте свой номер телефона.\nДля этого отправьте /start.",
    "no_regions": "⚠️ Области ещё не настроены. Свяжитесь с админом.",
    "region_selected": "✅ Область выбрана\n\n2️⃣ Введите район:",
    "district_too_short": "❌ Введите район полностью:",
    "enter_street": "3️⃣ Введите название улицы:\n<i>Например: ул. Амира Темура</i>",
    "street_too_short": "❌ Укажите улицу точнее:",
    "enter_target": "4️⃣ Введите ориентир:\n<i>Например: рядом со школой, дом 45</i>",
    "target_too_short": "❌ Укажите ориентир точнее:",
    "share_location": "5️⃣ 📍 <b>Отправьте вашу локацию</b>\n\nНажмите 📎 внизу → <b>Location</b> → отправьте своё местоположение.",
    "invalid_location": "❌ Пожалуйста, отправьте локацию. Нажмите 📎 → Location.",
    "enter_area": "📐 Введите примерную площадь (<b>м²</b>):\nПример: <code>500</code>",
    "invalid_area": "❌ Неправильный формат. Введите положительное число (например: 500):",
    "no_asphalt_types": "⚠️ Типы асфальта ещё не настроены. Свяжитесь с админом.",
    "select_asphalt": "🏗 Выберите тип асфальта:",
    "asphalt_not_found": "❌ Тип асфальта не найден",
    "order_summary": (
        "📋 <b>Данные заказа</b>\n\n"
        "📍 <b>Адрес:</b>\n"
        "   Район: {district}\n"
        "   Улица: {street}\n"
        "   Ориентир: {target}\n"
        "{location_link}\n"
        "📐 Площадь: <b>{area} м²</b>\n"
        "🏗 Асфальт: <b>{asphalt}</b>\n"
        "💰 Ориентировочная цена: <b>{price} сум</b>\n\n"
        "Подтверждаете?"
    ),
    "order_submitted": "✅ <b>Заказ принят!</b>\n\n🔢 Номер: <code>{number}</code>\n📍 Адрес: {address}\n{location_link}📐 Площадь: {area} м²\n\nВ ближайшее время мастер с вами свяжется.",
    "order_cancelled": "❌ Заказ отменён.",
    "no_orders": "📋 <b>Мои заказы</b>\n\nУ вас пока нет заказов.\nНажмите 📝 чтобы оставить заказ.",
    "my_orders_header": "📋 <b>Мои заказы:</b>\n",
    "new_order_notify": "🆕 <b>Новый заказ!</b>\n\n🔢 #{number}\n👤 {name}\n📱 {phone}\n📍 {address}\n{location_link}📐 {area} м²\n🏗 {asphalt}",

    # ── Price calculator ──
    "calc_start": "🧮 <b>Расчёт цены</b>\n\n📐 Введите площадь (м²):\nПример: <code>300</code>",
    "calc_invalid": "❌ Неправильный формат. Введите число:",
    "calc_result": (
        "🧮 <b>Результат расчёта</b>\n\n"
        "📐 Площадь: <b>{area} м²</b>\n"
        "🏗 Асфальт: <b>{asphalt}</b>\n"
        "💲 Цена: <b>{price_per_m2} сум/м²</b>\n"
        "─────────────────\n"
        "💰 Ориентировочный итог: <b>{total} сум</b>\n\n"
        "<i>* Точная цена определяется мастером</i>"
    ),

    # ── Consultation ──
    "consultation": "📞 <b>Консультация</b>\n\nСвяжитесь с нашим оператором:\n📱 <b>+998 XX XXX XX XX</b>\n\n🕒 Рабочее время: 09:00 — 18:00",
    "about_company": "🏗 <b>Avtoban Stroy</b>\n\nПрофессиональные услуги по укладке асфальта и дорожному строительству.\n\n📍 Адрес: г. Ташкент\n📱 Тел: +998 XX XXX XX XX\n🕒 Рабочее время: 09:00 — 18:00\n\nНадёжно, быстро и качественно!",

    # ── Master ──
    "no_new_orders": "🆕 <b>Новые заказы</b>\n\nПока новых заказов нет.",
    "new_orders_header": "🆕 <b>Новые заказы</b> ({count} шт.)\n\nВыберите для подробностей:",
    "order_not_found": "❌ Заказ не найден",
    "order_detail": (
        "📋 <b>Заказ: {number}</b>\n\n"
        "👤 Клиент: <b>{client}</b>\n"
        "📱 Тел: <b>{phone}</b>\n"
        "📍 Адрес: <b>{address}</b>\n"
        "📐 Ориент. площадь: <b>{area} м²</b>\n"
        "🏗 Асфальт: <b>{asphalt}</b>\n"
        "📅 Создан: <b>{date}</b>\n\n"
        "<i>Нажмите кнопку для подтверждения.</i>"
    ),
    "master_create_start": "➕ <b>Добавить заказ</b>\n\n1️⃣ Введите телефон клиента:\nПример: <code>998901234567</code>",
    "enter_client_name": "2️⃣ Введите имя клиента:",
    "invalid_phone": "❌ Неправильный номер. Повторите ввод:",
    "name_too_short": "❌ Введите имя полностью:",
    "select_region": "Выберите область:",
    "enter_district_num": "Введите район:",
    "enter_street_num": "Введите название улицы:\n<i>Например: ул. Амира Темура</i>",
    "enter_target_num": "Введите ориентир:\n<i>Например: рядом со школой, дом 45</i>",
    "enter_area_num": "Введите площадь (<b>м²</b>):\nПример: <code>500</code>",
    "select_asphalt_num": "Выберите тип асфальта:",
    "master_order_summary": (
        "📋 <b>Сводка заказа</b>\n\n"
        "👤 Клиент: <b>{client}</b>\n"
        "📱 Тел: <b>{phone}</b>\n"
        "📍 Адрес: <b>{address}</b>\n"
        "{location_link}"
        "📐 Площадь: <b>{area} м²</b>\n"
        "🏗 Асфальт: <b>{asphalt}</b>\n"
        "💰 Ориент. цена: <b>{price} сум</b>\n\n"
        "Подтверждаете?"
    ),
    "master_order_created": "✅ <b>Заказ создан!</b>\n\n🔢 Номер: <code>{number}</code>\n👤 Клиент: {name}\n📍 Адрес: {address}\n{location_link}📐 Площадь: {area} м²\n\nТеперь подтвердите через 'Новые заказы'.",
    "no_my_orders": "📋 <b>Мои заказы</b>\n\nЗакреплённых за вами заказов нет.",
    "my_orders_master": "📋 <b>Мои заказы</b> ({count} шт.):",

    # ── Master confirmation FSM ──
    "confirm_start": "✅ <b>Подтверждение заказа: {number}</b>\n\n1/8 — Введите точную площадь (м²):",
    "already_confirmed": "❌ Этот заказ уже подтверждён!",
    "invalid_positive": "❌ Неправильно. Введите положительное число (например: 450):",
    "enter_sum": "2/8 — Введите общую сумму (сум):\nПример: <code>45000000</code>",
    "invalid_sum": "❌ Неправильная сумма. Введите положительное число:",
    "enter_advance": "3/8 — Сумма залога (аванса) (сум):\nПример: <code>10000000</code>",
    "invalid_advance": "❌ Неправильно. Введите число (может быть 0):",
    "enter_address_confirm": "4/8 — Подтвердите или измените адрес:\nТекущий адрес: <b>{address}</b>\n\nВведите новый адрес или нажмите 'Сохранить':",
    "address_too_short": "❌ Адрес слишком короткий. Уточните:",
    "enter_work_date": "5/8 — Введите дату работ (ДД.ММ.ГГГГ):\nПример: <code>25.04.2026</code>",
    "invalid_date": "❌ Неправильная дата. Формат: ДД.ММ.ГГГГ (например: 25.04.2026):",
    "enter_usta_wage": "6/8 — Зарплата мастера-исполнителя (сум):\nПример: <code>5000000</code>",
    "enter_commission": "7/8 — Ваша комиссия (сум):\nПример: <code>2000000</code>",
    "enter_notes": "8/8 — Примечание (необязательно). Введите или пропустите:",
    "confirm_summary": (
        "📋 <b>Сводка подтверждения — {number}</b>\n\n"
        "📐 Площадь: <b>{area} м²</b>\n"
        "💰 Сумма: <b>{total} сум</b>\n"
        "💵 Залог: <b>{advance} сум</b>\n"
        "💳 Долг: <b>{debt} сум</b>\n"
        "📍 Адрес: {address}\n"
        "📅 Дата работ: {date}\n"
        "👷 Зарплата мастера: <b>{wage} сум</b>\n"
        "💼 Комиссия: <b>{commission} сум</b>\n"
        "📝 Примечание: {notes}\n\n"
        "Подтверждаете?"
    ),
    "order_confirmed": "✅ <b>Заказ успешно подтверждён!</b>\n\n🔢 #{number}\n⏰ У вас 30 минут на назначение мастера-исполнителя.\nНажмите '👷 Назначить мастера'.",
    "confirm_cancel": "❌ Подтверждение отменено.",
    "confirm_error": "❌ Ошибка: заказ уже подтверждён другим или не найден.",
    "order_confirmed_notify": "✅ <b>Заказ подтверждён!</b>\n\n🔢 #{number}\n👷 Мастер: {master}\n💰 Сумма: {total} сум\n⏰ Срок назначения мастера: 30 минут",
    "status_updated": "✅ Статус обновлён",
    "invalid_status": "❌ Неправильный статус",

    # ── Usta assignment ──
    "no_usta_orders": "👷 <b>Назначить мастера</b>\n\nПока нет заказов, требующих назначения.\n(Появится после подтверждения нового заказа)",
    "usta_orders_header": "👷 <b>Назначить мастера</b>\n\n{count} заказов ждут назначения.\nВыберите:",
    "no_available_ustas": "⚠️ <b>Нет доступных мастеров</b>\n\nВсе мастера неактивны.\nЧерез 30 минут назначится автоматически.",
    "select_usta": "👷 <b>Выберите мастера</b>\n\nЗаказ: #{number}\n📐 {area} м²  🏗 {asphalt}\n\nДоступные мастера ({count} шт.):",
    "usta_assigned": "✅ <b>Мастер назначен!</b>\n\nЗаказ: #{number}\n👷 Мастер: {usta}\n\nМастер получил уведомление.",
    "usta_assigned_notify": "👷 <b>Вам назначен заказ!</b>\n\n🔢 #{number}\n📍 {address}\n📐 {area} м²  🏗 {asphalt}\n📅 Дата работ: {date}\n💰 Зарплата: {wage} сум\n\nПринимаете?",
    "back_usta_no_orders": "👷 Нет заказов для назначения мастера.",
    "back_usta_header": "👷 <b>Назначить мастера</b> — {count} заказов:",

    # ── Usta ──
    "usta_no_orders": "📋 <b>Мои заказы</b>\n\nВам ещё не назначены заказы.\nУведомление придёт автоматически.",
    "usta_orders_list": "📋 <b>Мои заказы</b> ({count} шт.):\n",
    "usta_accepted": "✅ <b>Заказ принят!</b>\n\n🔢 #{number}\n📍 {address}\n{location_link}📐 {area} м²  🏗 {asphalt}\n📅 Дата работ: {date}\n💰 Зарплата: {wage} сум",
    "usta_accepted_notify": "✅ <b>Мастер принял заказ!</b>\n\nЗаказ: #{number}\n👷 Мастер: {usta}",
    "assignment_not_yours": "❌ Этот заказ не назначен вам или уже принят другим мастером.",
    "usta_declined": "❌ Заказ отклонён.",
    "usta_declined_notify": "❌ <b>Мастер отклонил заказ!</b>\n\nЗаказ: #{number}\n👷 {usta} отклонил.\n\nНазначьте нового: '👷 Назначить мастера'",

    # ── Material request ──
    "material_start": "📦 <b>Запросить материал</b>\n\nДля какого заказа?",
    "material_no_active": "📦 <b>Запросить материал</b>\n\nНет активных заказов. Сначала примите заказ.",
    "material_enter_tonnes": "📦 Введите количество материала (<b>тонн</b>):\nПример: <code>12.5</code>",
    "material_invalid_tonnes": "❌ Неправильное количество. Введите положительное число (например: 12.5):",
    "material_enter_notes": "📝 Примечание или доп. информация (необязательно):",
    "material_summary": "📦 <b>Сводка запроса материала</b>\n\n📐 Количество: <b>{tonnes} тонн</b>\n📝 Примечание: {notes}\n\nОтправить?",
    "material_submitted": "✅ <b>Запрос отправлен!</b>\n\n📦 {tonnes} тонн\nАдмин проверит и передаст на завод.",
    "material_cancelled": "❌ Запрос отменён.",
    "material_new_notify": "📦 <b>Новый запрос материала!</b>\n\n🔢 Запрос #{id}\n📍 Область: {region}\n👷 Мастер: {usta}\n📦 Количество: <b>{tonnes} тонн</b>\n📝 Примечание: {notes}\n\n⚠️ Требуется подтверждение!",

    # ── Work history ──
    "no_work_history": "📊 <b>История работ</b>\n\nЗавершённых работ пока нет.",
    "work_history_header": "📊 <b>История работ</b> ({count} шт.):\n",

    # ── Zavod ──
    "zavod_no_pending": "📦 <b>Входящие запросы</b>\n\nПока новых запросов нет.",
    "zavod_pending_header": "📦 <b>Входящие запросы</b> ({count} шт.)\n\nВыберите:",
    "zavod_no_pending_short": "📦 Новых запросов нет.",
    "zavod_pending_header_short": "📦 <b>Входящие запросы</b> ({count} шт.):",
    "zavod_request_not_found": "❌ Запрос не найден",
    "zavod_request_detail": "📦 <b>Запрос материала #{id}</b>\n\n🔢 Заказ: {order}\n👷 Мастер: {usta}\n📦 Количество: <b>{tonnes} тонн</b>\n📝 Примечание: {notes}\n📅 Дата: {date}",
    "zavod_enter_material_price": "1/3 — Введите цену материала (сум):\nПример: <code>8500000</code>",
    "zavod_enter_delivery_price": "2/3 — Введите цену доставки (сум):\nПример: <code>500000</code>",
    "zavod_enter_extra_cost": "3/3 — Дополнительные расходы (сум). Если нет — введите 0:",
    "zavod_invalid_price": "❌ Неправильная цена. Введите число:",
    "zavod_invalid_delivery": "❌ Неправильная цена. Введите число (может быть 0):",
    "zavod_invalid_extra": "❌ Неправильно. Введите число (может быть 0):",
    "zavod_price_summary": "💰 <b>Итог ценообразования</b>\n\n🏗 Материал: <b>{material} сум</b>\n🚚 Доставка: <b>{delivery} сум</b>\n➕ Дополнительно: <b>{extra} сум</b>\n─────────────────\n💰 Итого: <b>{total} сум</b>\n\nПодтверждаете?",
    "zavod_price_set": "✅ <b>Цена установлена!</b>\n\n📦 {tonnes} тонн — {total} сум\nМастер и водители уведомлены.",
    "zavod_price_error": "❌ Ошибка: запрос уже оценён или не найден.",
    "zavod_price_cancelled": "❌ Отменено.",
    "zavod_price_notify_usta": "💰 <b>Цена на материал установлена!</b>\n\n📦 {tonnes} тонн\n🏗 Материал: {material} сум\n🚚 Доставка: {delivery} сум\n➕ Дополнительно: {extra} сум\n💰 Итого: {total} сум\n\nДоставка организовывается.",
    "zavod_delivery_task": "🚚 <b>Задание на доставку!</b>\n\n📦 {tonnes} тонн материала\n📝 Заказ: {order}\n\nДоставлено?",
    "zavod_no_history": "📋 Нет запросов, ожидающих доставки.",
    "zavod_history_header": "🚚 <b>Ожидают доставки</b> ({count} шт.):",
    "zavod_delivered": "✅ Отмечено как доставлено!",
    "zavod_delivered_detail": "✅ <b>Доставлено!</b>\n\n📦 {tonnes} тонн\nМастер уведомлён.",
    "zavod_deliver_error": "❌ Запрос не найден или уже доставлен.",
    "material_delivered_notify": "📦 <b>Материал доставлен!</b>\n\n📦 {amount} тонн\nМожете приступать к работе!",

    # ── Shofer ──
    "shofer_no_deliveries": "🚗 <b>Мои доставки</b>\n\nПока нет материалов для доставки.",
    "shofer_active_header": "🚗 <b>Активные задания</b> ({count} шт.):\n",
    "shofer_not_found": "❌ Запрос не найден.",
    "shofer_already_delivered": "ℹ️ Это уже доставлено.",
    "shofer_not_priced": "❌ Цена ещё не установлена.",
    "shofer_confirmed": "✅ <b>Доставка подтверждена!</b>\n\n📦 {tonnes} тонн материала\nМастер уведомлён.",

    # ── Admin materials ──
    "admin_materials_header": "📦 <b>Заявки на материалы</b> ({count} шт.)\n\nТребуется подтверждение:",
    "admin_materials_empty": "📦 <b>Заявки на материалы</b>\n\nНет заявок, ожидающих подтверждения.",
    "admin_material_detail": "📦 <b>Заявка на материал #{id}</b>\n\n🔢 Заказ: {order}\n📍 Область: {region}\n👷 Мастер: {usta}\n📦 Количество: <b>{tonnes} тонн</b>\n📝 Примечание: {notes}\n📅 Дата: {date}\n\nПодтверждаете?",
    "admin_material_approved": "✅ <b>Заявка подтверждена!</b>\n\n📦 {tonnes} тонн\n📍 Область: {region}\nЗавод уведомлён ({count} шт.).",
    "admin_material_rejected": "❌ <b>Заявка отклонена</b>\n\nМастер уведомлён.",
    "admin_material_reject_notify": "❌ <b>Заявка на материал отклонена</b>\n\n📦 {tonnes} тонн\nОтклонено администратором.",
    "admin_material_approve_notify": "📦 <b>Новая заявка на материал!</b>\n\n🔢 Заявка #{id}\n📍 Область: {region}\n👷 Мастер: {usta}\n📦 Количество: <b>{tonnes} тонн</b>\n📝 Примечание: {notes}",
    "admin_materials_empty_short": "📦 Нет заявок, ожидающих подтверждения.",

    # ── Admin users ──
    "users_manage": "👥 <b>Управление пользователями</b>\n\nЧто хотите сделать?",
    "search_by_id": "🔍 Поиск по ID",
    "all_users": "📋 Все пользователи",
    "enter_telegram_id": "🔍 Отправьте <b>Telegram ID</b> пользователя:\n\n<i>Для получения ID пользователь должен написать /start боту @userinfobot.</i>",
    "invalid_telegram_id": "❌ Неправильный формат. Введите только число (например: <code>123456789</code>):",
    "user_not_found": "❌ Пользователь с таким Telegram ID не найден.\nПользователь должен нажать /start в боте.",
    "user_detail": (
        "👤 <b>Данные пользователя</b>\n\n"
        "🆔 TG ID: <code>{tg_id}</code>\n"
        "👤 Имя: <b>{name}</b>\n"
        "📱 Тел: <b>{phone}</b>\n"
        "👥 Роль: <b>{role}</b>\n"
        "📍 Область: <b>{region}</b>\n"
        "Статус: {status_icon} {status_text}\n"
        "📅 Дата рег.: <b>{date}</b>"
    ),
    "select_new_role": "👥 Выберите новую роль:",
    "role_changed": "✅ Роль успешно изменена!\n\n👤 <b>{name}</b>\n👥 Новая роль: <b>{role}</b>",
    "role_changed_notify": "🔔 <b>Ваша роль изменена!</b>\n\n👥 Новая роль: <b>{role}</b>\n\nНовое меню загружено.",
    "cannot_block_self": "❌ Вы не можете заблокировать себя!",
    "cannot_block_super_admin": "❌ Нельзя заблокировать супер-админа!",
    "cannot_assign_super_admin": "❌ Вы не можете назначить супер-админа!",
    "user_activated": "активирован",
    "user_blocked": "заблокирован",
    "users_list_header": "👥 <b>Пользователи</b> (страница {page})\n",
    "users_not_found": "👥 Пользователи не найдены.",
    "select_region_admin": "📍 Выберите область:",
    "region_changed": "✅ Область изменена!",
    "no_regions_admin": "⚠️ Области ещё не настроены.",

    # ── Admin orders ──
    "orders_header": "📋 <b>Заказы ({filter})</b> — {total} шт.\nСтраница {page}/{pages}\n",
    "orders_empty": "Заказы не найдены.",
    "admin_create_start": "➕ <b>Добавить заказ</b>\n\n1/5 — Введите телефон клиента:\nПример: <code>+998901234567</code>",
    "invalid_phone_short": "❌ Неправильный номер. Повторите:",
    "client_found": "✅ Клиент найден: <b>{name}</b>\n\n2/5 — Введите адрес:",
    "client_not_found_enter_name": "⚠️ Пользователь с этим номером не найден.\n\n1.5/5 — Введите имя клиента:",
    "name_too_short_admin": "❌ Имя слишком короткое:",
    "client_created": "✅ Клиент создан: <b>{name}</b>\n\n2/5 — Введите адрес:",
    "address_too_short_admin": "❌ Адрес слишком короткий:",
    "enter_area_admin": "3/5 — Введите площадь (м²):\nПример: <code>500</code>",
    "select_asphalt_admin": "4/5 — Выберите тип асфальта:",
    "no_asphalt_admin": "⚠️ Типы асфальта не найдены. Сначала добавьте в настройках.",
    "admin_order_summary": (
        "📋 <b>Сводка нового заказа</b>\n\n"
        "👤 Клиент: <b>{client}</b>\n"
        "📱 Тел: <b>{phone}</b>\n"
        "📍 Адрес: {address}\n"
        "{location_link}"
        "📐 Площадь: <b>{area} м²</b>\n"
        "🏗 Асфальт: <b>{asphalt}</b>\n"
        "💰 Ориент.: <b>{price} сум</b>\n\n"
        "Подтверждаете?"
    ),
    "admin_order_created": "✅ <b>Заказ создан!</b>\n\n🔢 Номер: <code>{number}</code>\n👤 Клиент: {client}\n📍 Адрес: {address}\n{location_link}",
    "admin_order_notify": "🆕 <b>Новый заказ (от админа)!</b>\n\n🔢 #{number}\n👤 {client} | {phone}\n📍 {address}\n{location_link}📐 {area} м²",
    "change_status": "🔄 Выберите новый статус:",

    # ── Admin settings ──
    "settings_menu": "🔧 <b>Настройки</b>\n\nЧто настроить?",
    "asphalt_types_btn": "🏗 Типы асфальта",
    "no_asphalt_types_admin": "🏗 Типов асфальта нет.\nДобавьте новый:",
    "asphalt_types_header": "🏗 <b>Типы асфальта</b>\nВыберите для управления:",
    "add_asphalt": "➕ Добавить новый",
    "enter_asphalt_name": "🏗 Введите название нового типа асфальта:\nПример: <code>Горячий асфальт</code>, <code>Холодный асфальт</code>",
    "asphalt_name_short": "❌ Название слишком короткое. Повторите:",
    "enter_asphalt_price": "💰 Введите цену за м² для <b>{name}</b> (сум):\nПример: <code>85000</code>",
    "invalid_asphalt_price": "❌ Неправильная цена. Введите число (например: 85000):",
    "asphalt_added": "✅ Тип асфальта добавлен!\n\n🏗 Название: <b>{name}</b>\n💰 Цена: <b>{price} сум/м²</b>",
    "enter_new_price": "💰 Введите новую цену (сум):\nПример: <code>90000</code>",
    "price_updated": "✅ Цена обновлена!\n\n🏗 {name}: <b>{price} сум/м²</b>",
    "asphalt_not_found_admin": "❌ Тип асфальта не найден.",

    # ── Reports ──
    "period_today": "Сегодня",
    "period_week": "Эта неделя",
    "period_month": "Этот месяц",
    "period_all": "Всё время",
    "statistics_header": (
        "📊 <b>Общая статистика</b>\n\n"
        "📦 Всего заказов: <b>{total}</b>\n"
        "  🆕 Новые: {new}\n"
        "  ✅ Подтверждённые: {confirmed}\n"
        "  🔧 В работе: {in_work}\n"
        "  🏁 Завершённые: {done}\n"
        "  ❌ Отменённые: {cancelled}\n\n"
        "💰 Общий доход: <b>{revenue} сум</b>\n"
        "💵 Собрано: <b>{collected} сум</b>\n"
        "💳 Общий долг: <b>{debt} сум</b>\n\n"
        "📅 <b>Этот месяц:</b>\n"
        "  Заказы: <b>{month_total}</b>\n"
        "  Доход: <b>{month_revenue} сум</b>"
    ),
    "master_report_menu": "👷 <b>Отчёт мастеров</b>\n\nВыберите период:",
    "master_report_empty": "👷 <b>Отчёт мастеров</b> — {period}\n\nДанных нет.",
    "master_report_header": "👷 <b>Отчёт мастеров</b> — {period}\n",
    "usta_report_menu": "🔨 <b>Отчёт мастеров-исп.</b>\n\nВыберите период:",
    "usta_report_empty": "🔨 <b>Отчёт мастеров-исп.</b> — {period}\n\nДанных нет.",
    "usta_report_header": "🔨 <b>Отчёт мастеров-исп.</b> — {period}\n",

    # ── Payments ──
    "payment_menu": "💵 <b>Обновить оплату</b>\n\nЧто хотите сделать?",
    "enter_payment": "💵 Введите сумму платежа (сум):\nПример: <code>5000000</code>",
    "payment_added": "✅ <b>Платёж внесён!</b>\n\nЗаказ: #{number}\n💵 Внесено: {amount} сум\n💰 Всего оплачено: {total} сум\n💳 Долг: {debt} сум",
    "payment_full_done": "✅ <b>Полностью оплачено и завершено!</b>\n\nЗаказ: #{number}\n💰 {total} сум полностью получено.",

    # ── Expenses ──
    "expense_start": "💸 <b>Добавить расход</b>\n\nДля какого заказа?",
    "expense_no_active": "💸 <b>Добавить расход</b>\n\nНет активных заказов.",
    "expense_select_type": "💸 Выберите тип расхода:",
    "expense_enter_amount": "💰 Введите сумму (сум):\nПример: <code>250000</code>",
    "expense_invalid_amount": "❌ Неправильная сумма. Введите число:",
    "expense_enter_desc": "📝 Введите примечание (необязательно):\nНажмите '⏩' для пропуска.",
    "expense_added": "✅ <b>Расход добавлен!</b>\n\n{label}: <b>{amount} сум</b>\n📝 {desc}",
    "expense_cancelled": "❌ Добавление расхода отменено.",
    "no_expenses": "📋 Для этого заказа расходы не внесены.",
    "expenses_header": "💸 <b>Расходы</b> (итого: {total} сум):\n",

    # ── Export ──
    "export_menu": "📥 <b>Экспорт в Excel</b>\n\nКакие данные выгрузить?",
    "export_orders_month": "📋 Заказы (этот месяц)",
    "export_orders_all": "📋 Заказы (все)",
    "export_expenses_month": "💸 Расходы (этот месяц)",
    "export_materials_month": "📦 Заявки на материалы (этот месяц)",
    "export_preparing": "⏳ Файл готовится...",

    # ── Standalone labels (used in detail views) ──
    "order": "Заказ",
    "client": "Клиент",
    "phone": "Тел",
    "address": "Адрес",
    "area": "Площадь",
    "asphalt": "Асфальт",
    "created": "Создан",
    "total": "Сумма",
    "advance": "Залог",
    "debt": "Долг",
    "status": "Статус",
    "usta": "Мастер-исп.",
    "work_date": "Дата работ",
    "press_to_confirm": "Нажмите кнопку для подтверждения.",

    # ── Button aliases ──
    "btn_material_requests": "📦 Заявки на материалы",
    "btn_set_price": "✅ Указать цену",

    # ── Master handler aliases ──
    "new_orders_list": "🆕 <b>Новые заказы</b> ({count} шт.)\n\nВыберите для подробностей:",
    "master_order_start": "➕ <b>Добавить заказ</b>\n\n1️⃣ Введите телефон клиента:\nПример: <code>998901234567</code>",
    "master_no_orders": "📋 <b>Мои заказы</b>\n\nЗакреплённых за вами заказов нет.",
    "master_orders_list": "📋 <b>Мои заказы</b> ({count} шт.):",
    "confirm_step_area": "✅ <b>Подтверждение заказа: {number}</b>\n\n1/8 — Введите точную площадь (м²):",
    "confirm_step_sum": "2/8 — Введите общую сумму (сум):\nПример: <code>45000000</code>",
    "confirm_step_advance": "3/8 — Сумма залога (аванса) (сум):\nПример: <code>10000000</code>",
    "confirm_step_address": "4/8 — Подтвердите или измените адрес:\nТекущий адрес: <b>{address}</b>\n\nВведите новый адрес или нажмите 'Сохранить':",
    "confirm_step_date": "5/8 — Введите дату работ (ДД.ММ.ГГГГ):\nПример: <code>25.04.2026</code>",
    "confirm_step_usta_wage": "6/8 — Зарплата мастера-исполнителя (сум):\nПример: <code>5000000</code>",
    "confirm_step_commission": "7/8 — Ваша комиссия (сум):\nПример: <code>2000000</code>",
    "confirm_step_notes": "8/8 — Примечание (необязательно). Введите или пропустите:",
    "order_confirmed_success": "✅ <b>Заказ успешно подтверждён!</b>\n\n🔢 #{number}\n⏰ У вас 30 минут на назначение мастера-исполнителя.\nНажмите '👷 Назначить мастера'.",
    "confirm_cancelled": "❌ Подтверждение отменено.",
    "no_usta_pending": "👷 <b>Назначить мастера</b>\n\nПока нет заказов, требующих назначения.\n(Появится после подтверждения нового заказа)",
    "usta_assign_list": "👷 <b>Назначить мастера</b>\n\n{count} заказов ждут назначения.\nВыберите:",
    "no_ustas_available": "⚠️ <b>Нет доступных мастеров</b>\n\nВсе мастера заняты или неактивны.",
    "usta_assignment_notify": "👷 <b>Вам назначен заказ!</b>\n\n🔢 #{number}\n📍 {address}\n📐 {area} м²  🏗 {asphalt}\n📅 Дата работ: {date}\n💰 Зарплата: {wage} сум\n\nПринимаете?",
    "usta_assigned_success": "✅ <b>Мастер назначен!</b>\n\nЗаказ: #{number}\n👷 Мастер: {usta}",

    # ── Zavod handler aliases ──
    "no_pending_requests": "📦 <b>Входящие запросы</b>\n\nПока новых запросов нет.",
    "pending_requests_list": "📦 <b>Входящие запросы</b> ({count} шт.)\n\nВыберите:",
    "request_not_found": "❌ Запрос не найден",
    "material_request_detail": "📦 <b>Запрос материала #{id}</b>\n\n🔢 Заказ: {order}\n👷 Мастер: {usta}\n📦 Количество: <b>{amount} тонн</b>\n📝 Примечание: {notes}\n📅 Дата: {date}",
    "price_step_material": "1/3 — Введите цену материала (сум):\nПример: <code>8500000</code>",
    "price_step_delivery": "2/3 — Введите цену доставки (сум):\nПример: <code>500000</code>",
    "price_step_extra": "3/3 — Дополнительные расходы (сум). Если нет — введите 0:",
    "price_summary": "💰 <b>Итог ценообразования</b>\n\n🏗 Материал: <b>{material} сум</b>\n🚚 Доставка: <b>{delivery} сум</b>\n➕ Дополнительно: <b>{extra} сум</b>\n─────────────────\n💰 Итого: <b>{total} сум</b>\n\nПодтверждаете?",
    "price_error": "❌ Ошибка: запрос уже оценён или не найден.",
    "material_price_set_notify": "💰 <b>Цена на материал установлена!</b>\n\n📦 {amount} тонн\n🏗 Материал: {material} сум\n🚚 Доставка: {delivery} сум\n➕ Дополнительно: {extra} сум\n💰 Итого: {total} сум\n\nДоставка организовывается.",
    "delivery_task_notify": "🚚 <b>Задание на доставку!</b>\n\n📦 {amount} тонн материала\n📝 Заказ: {order}\n\nДоставлено?",
    "price_set_success": "✅ <b>Цена установлена!</b>\n\n📦 {amount} тонн — {total} сум\nМастер и водители уведомлены.",
    "no_priced_requests": "📋 Нет запросов, ожидающих доставки.",
    "priced_requests_list": "🚚 <b>Ожидают доставки</b> ({count} шт.):",
    "deliver_error": "❌ Запрос не найден или уже доставлен.",
    "delivered_marked": "✅ Отмечено как доставлено!",
    "delivered_success": "✅ <b>Доставлено!</b>\n\n📦 {amount} тонн\nМастер уведомлён.",

    # ── Shofer handler aliases ──
    "no_deliveries": "🚗 <b>Мои доставки</b>\n\nПока нет материалов для доставки.",
    "active_deliveries": "🚗 <b>Активные задания</b> ({count} шт.):\n",
    "already_delivered": "ℹ️ Это уже доставлено.",
    "not_priced_yet": "❌ Цена ещё не установлена.",
    "delivery_confirmed": "✅ <b>Доставка подтверждена!</b>\n\n📦 {amount} тонн материала\nМастер уведомлён.",

    "btn_web_panel": "🌐 Веб панель",

    # ── Region / viloyat ──
    "no_regions": "⚠️ Регионы ещё не настроены. Обратитесь к администратору.",
    "select_region": "📍 Выберите регион (вилоят):",
    "region_selected": "✅ Регион выбран. Продолжаем...",
}
