"""
Web panel i18n — three languages: uz_lat (O'zbek lotin), uz_cyr (Ўзбек кирилл), ru (Русский).
Usage in Jinja2 templates:  {{ t('key') }}
"""

TRANSLATIONS: dict[str, dict[str, str]] = {}

# ── Common / shared ──────────────────────────────────────────────────────────
_common = {
    # Language picker
    "lang_uz_lat":     ("O'zbek (Lotin)",       "Ўзбек (Лотин)",        "Узбек (Латин)"),
    "lang_uz_cyr":     ("Ўзбек (Кирилл)",       "Ўзбек (Кирилл)",       "Узбек (Кирилл)"),
    "lang_ru":         ("Русский",               "Русский",               "Русский"),
    "lang_label":      ("🌐 Til",                "🌐 Тил",                "🌐 Язык"),

    # Units
    "som":             ("so'm",                  "сўм",                   "сум"),
    "ta":              ("ta",                    "та",                    "шт"),
    "pcs":             ("ta",                    "та",                    "шт"),

    # Statuses
    "status_new":        ("Yangi",       "Янги",       "Новый"),
    "status_confirmed":  ("Tasdiqlangan","Тасдиқланган","Подтверждён"),
    "status_in_work":    ("Ish jarayonida","Иш жараёнида","В работе"),
    "status_done":       ("Bajarildi",   "Бажарилди",   "Выполнен"),
    "status_cancelled":  ("Bekor qilindi","Бекор қилинди","Отменён"),
    "status_finished":   ("Yakunlandi",  "Якунланди",   "Завершён"),

    # Common buttons / labels
    "save":            ("Saqlash",               "Сақлаш",                "Сохранить"),
    "back":            ("Orqaga",                "Орқага",                "Назад"),
    "search":          ("Qidirish",              "Қидириш",               "Поиск"),
    "total":           ("Jami",                  "Жами",                  "Итого"),
    "date":            ("Sana",                  "Сана",                  "Дата"),
    "no_data":         ("Ma'lumot yo'q",         "Маълумот йўқ",          "Нет данных"),

    # ── Master Dashboard ─────────────────────────────────────────────────────
    "hello":           ("Salom",                 "Салом",                 "Здравствуйте"),
    "master_panel_sub":("Master Panel — zakazlar va komissiya boshqaruvi",
                        "Мастер Панел — заказлар ва комиссия бошқаруви",
                        "Мастер Панель — управление заказами и комиссией"),
    "total_commission":("Jami Komissiya",        "Жами Комиссия",         "Общая Комиссия"),
    "total_orders":    ("Jami Zakazlar",         "Жами Заказлар",         "Всего Заказов"),
    "total_revenue":   ("Jami Tushum",           "Жами Тушум",            "Общий Доход"),
    "payment_share":   ("To'lov ulushi",         "Тўлов улуши",           "Доля оплаты"),
    "this_month":      ("Bu oy",                 "Бу ой",                 "Этот месяц"),
    "debt":            ("Qarz",                  "Қарз",                  "Долг"),
    "recent_orders":   ("Oxirgi Zakazlar",       "Охирги Заказлар",       "Последние Заказы"),
    "order_status":    ("Zakazlar Holati",       "Заказлар Ҳолати",       "Статус Заказов"),
    "payment_status":  ("To'lov Holati",         "Тўлов Ҳолати",          "Статус Оплаты"),
    "paid":            ("To'langan",             "Тўланган",              "Оплачено"),
    "month_results":   ("Bu Oy Natijalar",       "Бу Ой Натижалар",       "Результаты Месяца"),
    "by_status":       ("Status bo'yicha",       "Статус бўйича",         "По Статусу"),
    "orders":          ("Zakazlar",              "Заказлар",              "Заказы"),
    "revenue_som":     ("Tushum so'm",           "Тушум сўм",             "Доход сум"),
    "commission_som":  ("Komissiya so'm",        "Комиссия сўм",          "Комиссия сум"),
    "no_orders":       ("Zakazlar yo'q",         "Заказлар йўқ",          "Заказов нет"),

    # Table headers
    "th_number":       ("№",                     "№",                     "№"),
    "th_client":       ("Klient",                "Клиент",                "Клиент"),
    "th_address":      ("Manzil",                "Манзил",                "Адрес"),
    "th_amount":       ("Summa",                 "Сумма",                 "Сумма"),
    "th_commission":   ("Komissiya",             "Комиссия",              "Комиссия"),
    "th_status":       ("Status",                "Статус",                "Статус"),
    "th_date":         ("Sana",                  "Сана",                  "Дата"),

    # ── Master Clients ───────────────────────────────────────────────────────
    "my_clients":      ("Mening Klientlarim",    "Менинг Клиентларим",    "Мои Клиенты"),
    "clients_sub":     ("Barcha klientlar va ularning zakaz tarixi",
                        "Барча клиентлар ва уларнинг заказ тарихи",
                        "Все клиенты и их история заказов"),
    "clients_list":    ("Klientlar Ro'yxati",    "Клиентлар Рўйхати",    "Список Клиентов"),
    "client_name":     ("Klient Ismi",           "Клиент Исми",           "Имя Клиента"),
    "phone":           ("Telefon",               "Телефон",               "Телефон"),
    "orders_count":    ("Zakazlar Soni",         "Заказлар Сони",         "Кол-во Заказов"),
    "last_order":      ("Oxirgi Zakaz",          "Охирги Заказ",          "Последний Заказ"),
    "total_clients":   ("Jami Klientlar",        "Жами Клиентлар",       "Всего Клиентов"),

    # ── Master Commission ────────────────────────────────────────────────────
    "commission_report":("Komissiya Hisoboti",   "Комиссия Ҳисоботи",    "Отчёт по Комиссии"),
    "commission_sub":  ("Sizning komissiya daromadingiz va tafsilotlar",
                        "Сизнинг комиссия даромадингиз ва тафсилотлар",
                        "Ваш доход от комиссий и подробности"),
    "this_week":       ("Bu Hafta",              "Бу Ҳафта",              "Эта Неделя"),
    "financial_details":("Moliyaviy Tafsilotlar","Молиявий Тафсилотлар",  "Финансовые Детали"),
    "advance_payment": ("Oldindan To'lov",       "Олдиндан Тўлов",        "Аванс"),
    "my_commission":   ("Mening Komissiyam",     "Менинг Комиссиям",      "Моя Комиссия"),
    "status_commission":("Holat Bo'yicha Komissiya","Ҳолат Бўйича Комиссия","Комиссия по Статусу"),
    "status_col":      ("Holat",                 "Ҳолат",                 "Статус"),
    "recent_commissions":("Oxirgi Komissiyalar", "Охирги Комиссиялар",    "Последние Комиссии"),
    "order_number":    ("Zakaz №",               "Заказ №",               "Заказ №"),
    "total_amount":    ("Jami Summa",            "Жами Сумма",            "Общая Сумма"),

    # ── Master Expenses ──────────────────────────────────────────────────────
    "expense_entry":   ("Xarajat Kiritish",      "Харажат Киритиш",       "Внесение Расходов"),
    "new_expense":     ("Yangi Xarajat",         "Янги Харажат",          "Новый Расход"),
    "select_order":    ("— Zakaz tanlang —",     "— Заказ танланг —",     "— Выберите заказ —"),
    "expense_type":    ("Xarajat turi",          "Харажат тури",          "Тип расхода"),
    "select_type":     ("— Tur tanlang —",       "— Тур танланг —",       "— Выберите тип —"),
    "amount_som":      ("Miqdor (so'm)",         "Миқдор (сўм)",          "Сумма (сум)"),
    "comment_optional":("Izoh (ixtiyoriy)",      "Изоҳ (ихтиёрий)",       "Комментарий (необязательно)"),
    "comment_placeholder":("Qo'shimcha izoh...", "Қўшимча изоҳ...",       "Дополнительный комментарий..."),
    "recent_expenses": ("So'nggi xarajatlar",    "Сўнгги харажатлар",     "Последние расходы"),
    "no_expenses":     ("Hozircha xarajatlar yo'q.","Ҳозирча харажатлар йўқ.","Расходов пока нет."),
    "expense_saved":   ("Xarajat muvaffaqiyatli saqlandi!",
                        "Харажат муваффақиятли сақланди!",
                        "Расход успешно сохранён!"),
    "error_fields":    ("Barcha maydonlarni to'ldiring.",
                        "Барча майдонларни тўлдиринг.",
                        "Заполните все поля."),
    "error_amount":    ("Miqdor noto'g'ri formatda kiritildi.",
                        "Миқдор нотўғри форматда киритилди.",
                        "Сумма введена в неверном формате."),
    "error_order":     ("Tanlangan zakaz topilmadi.",
                        "Танланган заказ топилмади.",
                        "Выбранный заказ не найден."),
    "error_generic":   ("Xatolik yuz berdi.",    "Хатолик юз берди.",     "Произошла ошибка."),
    "order_label":     ("Zakaz",                 "Заказ",                 "Заказ"),
    "type_label":      ("Tur",                   "Тур",                   "Тип"),
    "amount_label":    ("Miqdor",                "Миқдор",                "Сумма"),
    "comment_label":   ("Izoh",                  "Изоҳ",                  "Комментарий"),

    # Expense types
    "exp_material":    ("Material",              "Материал",              "Материал"),
    "exp_delivery":    ("Yetkazib berish",       "Етказиб бериш",        "Доставка"),
    "exp_wage":        ("Ish haqi",              "Иш ҳақи",               "Зарплата"),
    "exp_bardyor":     ("Bardyor",               "Бардёр",                "Бордюр"),
    "exp_extra":       ("Qo'shimcha",            "Қўшимча",               "Дополнительно"),

    # ── Master Usta ──────────────────────────────────────────────────────────
    "usta_assign":     ("Usta Tayinlash",        "Уста Тайинлаш",         "Назначение Мастера"),
    "orders_list":     ("Zakazlar ro'yxati",     "Заказлар рўйхати",      "Список заказов"),
    "current_usta":    ("Hozirgi Usta",          "Ҳозирги Уста",          "Текущий Мастер"),
    "usta_wage":       ("Usta Maoshi",           "Уста Маоши",            "Зарплата Мастера"),
    "assign":          ("Tayinlash",             "Тайинлаш",              "Назначить"),
    "assigned":        ("Tayinlangan",           "Тайинланган",           "Назначен"),
    "not_assigned":    ("Tayinlanmagan",         "Тайинланмаган",         "Не назначен"),
    "select_usta":     ("— Usta tanlanmagan —",  "— Уста танланмаган —",  "— Мастер не выбран —"),
    "wage_placeholder":("Maosh (so'm)",          "Маош (сўм)",            "Зарплата (сум)"),
    "no_orders_msg":   ("Sizda hech qanday zakaz yo'q.",
                        "Сизда ҳеч қандай заказ йўқ.",
                        "У вас нет заказов."),

    # ── Reports ──────────────────────────────────────────────────────────────
    "reports":         ("Hisobotlar",            "Ҳисоботлар",            "Отчёты"),
    "financial_report":("Moliyaviy Hisobot",     "Молиявий Ҳисобот",      "Финансовый Отчёт"),
    "total_income":    ("Jami Daromad",          "Жами Даромад",          "Общий Доход"),
    "total_expenses":  ("Jami Xarajatlar",       "Жами Харажатлар",       "Общие Расходы"),
    "net_profit":      ("Sof Foyda",             "Соф Фойда",             "Чистая Прибыль"),
    "profit_margin":   ("Foyda darajasi",        "Фойда даражаси",        "Маржа прибыли"),
    "asphalt_analysis":("Asfalt Foyda Tahlili",  "Асфалт Фойда Таҳлили",  "Анализ Прибыли по Асфальту"),
    "asphalt_revenue": ("Asfalt sotuv daromadi", "Асфалт сотув даромади",  "Доход от продажи асфальта"),
    "asphalt_cost":    ("Asfalt tannarxi",       "Асфалт таннархи",        "Себестоимость асфальта"),
    "asphalt_profit":  ("Asfalt foyda",          "Асфалт фойда",           "Прибыль от асфальта"),
    "cost_breakdown":  ("Xarajatlar Tafsiloti",  "Харажатлар Тафсилоти",   "Детализация Расходов"),
    "material_costs":  ("Material xarajatlari",  "Материал харажатлари",    "Расходы на материалы"),
    "other_expenses":  ("Boshqa xarajatlar",     "Бошқа харажатлар",       "Прочие расходы"),
    "total_cost":      ("Jami xarajat",          "Жами харажат",           "Общие расходы"),
    "advance_label":   ("Oldindan to'lov",       "Олдиндан тўлов",         "Аванс"),
    "payment_pct":     ("To'lov foizi",          "Тўлов фоизи",            "Процент оплаты"),
    "order_statuses":  ("Zakazlar Holati",       "Заказлар Ҳолати",        "Статус Заказов"),

    # ── Order Actions (confirm + status) ────────────────────────────────────
    "new_orders_title":    ("Yangi Zakazlar",        "Янги Заказлар",          "Новые Заказы"),
    "new_orders_sub":      ("Tasdiqlanmagan zakazlar — tekshirib tasdiqlang",
                            "Тасдиқланмаган заказлар — текшириб тасдиқланг",
                            "Неподтверждённые заказы — проверьте и подтвердите"),
    "my_active_orders":    ("Faol Zakazlarim",       "Фаол Заказларим",        "Мои Активные Заказы"),
    "active_orders_sub":   ("Tasdiqlangan va ishda — holatini o'zgartiring",
                            "Тасдиқланган ва ишда — ҳолатини ўзгартиринг",
                            "Подтверждённые и в работе — измените статус"),
    "confirm_btn":         ("Tasdiqlash",            "Тасдиқлаш",             "Подтвердить"),
    "confirm_order_title": ("Zakazni Tasdiqlash",    "Заказни Тасдиқлаш",     "Подтвердить Заказ"),
    "confirm_and_save":    ("Tasdiqlash va Saqlash",  "Тасдиқлаш ва Сақлаш",   "Подтвердить и Сохранить"),
    "start_work_btn":      ("Ishga Olish",           "Ишга Олиш",             "Начать Работу"),
    "finish_btn":          ("Yakunlash",             "Якунлаш",               "Завершить"),
    "area_m2_label":       ("Maydon (m²)",           "Майдон (м²)",            "Площадь (м²)"),
    "total_price_label":   ("Jami Summa",            "Жами Сумма",             "Общая Сумма"),
    "work_date_label":     ("Ish Sanasi",            "Иш Санаси",             "Дата Работы"),
    "select_usta_label":   ("Usta tanlash",          "Уста танлаш",            "Выбрать Мастера"),
    "notes_label":         ("Izoh",                  "Изоҳ",                   "Примечание"),
    "no_new_orders_msg":   ("Hozircha yangi zakazlar yo'q",
                            "Ҳозирча янги заказлар йўқ",
                            "Новых заказов пока нет"),
    "no_active_orders_msg":("Faol zakazlar yo'q",    "Фаол заказлар йўқ",      "Активных заказов нет"),
    "order_confirmed_msg": ("Zakaz muvaffaqiyatli tasdiqlandi!",
                            "Заказ муваффақиятли тасдиқланди!",
                            "Заказ успешно подтверждён!"),
    "status_changed_msg":  ("Holat muvaffaqiyatli o'zgartirildi!",
                            "Ҳолат муваффақиятли ўзгартирилди!",
                            "Статус успешно изменён!"),
    "error_date":          ("Sana noto'g'ri formatda.",
                            "Сана нотўғри форматда.",
                            "Неверный формат даты."),

    # ── Login ────────────────────────────────────────────────────────────────
    "login_title":     ("Kirish",                "Кириш",                 "Вход"),
    "phone_label":     ("Telefon raqam",         "Телефон рақам",          "Номер телефона"),
    "password_label":  ("Parol",                 "Парол",                  "Пароль"),
    "login_btn":       ("Kirish",                "Кириш",                 "Войти"),

    # ── Order confirm — line items ────────────────────────────────────────
    "select_category":     ("Kategoriyani tanlang",     "Категорияни танланг",     "Выберите категорию"),
    "select_subcategory":  ("Sub-kategoriyani tanlang", "Суб-категорияни танланг", "Выберите подкатегорию"),
    "select_material":     ("Materialni tanlang",       "Материални танланг",      "Выберите материал"),
    "main_asphalt":        ("Asosiy asfalt turi",       "Асосий асфалт тури",      "Основной тип асфальта"),
    "extra_services":      ("Qo'shimcha xizmatlar",     "Қўшимча хизматлар",       "Дополнительные услуги"),
    "add_service":         ("➕ Qo'shimcha qo'shish",   "➕ Қўшимча қўшиш",        "➕ Добавить услугу"),
    "remove":              ("O'chirish",                "Ўчириш",                 "Удалить"),
    "service_name":        ("Xizmat nomi",              "Хизмат номи",             "Название услуги"),
    "price_m2":            ("Narx/m²",                  "Нарх/м²",                 "Цена/м²"),  
    "subtotal":            ("Jami",                     "Жами",                    "Итого"),
    "calculated_total":    ("Hisoblangan summa",        "Ҳисобланган сумма",       "Рассчитанная сумма"),
    "agreed_sum":          ("Kelishilgan summa",        "Келишилган сумма",        "Согласованная сумма"),
    "line_items":          ("Xizmatlar ro'yxati",       "Хизматлар рўйхати",      "Список услуг"),

    # ── Admin sidebar view names ───────────────────────────────────────────
    "v_users":         ("Foydalanuvchilar",      "Фойдаланувчилар",       "Пользователи"),
    "v_orders":        ("Zakazlar",              "Заказлар",              "Заказы"),
    "v_expenses":      ("Xarajatlar",            "Харажатлар",            "Расходы"),
    "v_material_req":  ("Material so'rovlar",    "Материал сўровлар",     "Заявки на материал"),
    "v_categories":    ("Kategoriyalar",         "Категориялар",          "Категории"),
    "v_subcategories": ("Sub-kategoriyalar",     "Суб-категориялар",      "Подкатегории"),
    "v_materials":     ("Materiallar",           "Материаллар",           "Материалы"),
    "v_viloyat":       ("Viloyatlar",            "Вилоятлар",             "Области"),
    "v_tuman":         ("Tumanlar",              "Туманлар",              "Районы"),
    "v_region":        ("Hududlar (eski)",       "Ҳудудлар (эски)",       "Регионы (стар.)"),
    "v_zavod":         ("Zavodlar",              "Заводлар",              "Заводы"),
    "v_shop_cat":      ("Do'kon Kategoriyalar",  "Дўкон Категориялар",    "Категории Магазина"),
    "v_products":      ("Mahsulotlar",           "Маҳсулотлар",           "Товары"),
    "v_portfolio":     ("Portfoliolar",          "Портфолиолар",          "Портфолио"),
    "v_shop_orders":   ("Do'kon Buyurtmalar",    "Дўкон Буюртмалар",     "Заказы Магазина"),
    "v_reports":       ("Hisobotlar",            "Ҳисоботлар",            "Отчёты"),
    "v_dashboard":     ("Dashboard",             "Дашборд",               "Дашборд"),
    "v_order_actions": ("Zakazlarni Boshqarish", "Заказларни Бошқариш",   "Управление Заказами"),
    "v_usta_assign":   ("Usta Tayinlash",        "Уста Тайинлаш",         "Назначение Мастера"),
    "v_expense_entry": ("Xarajat Kiritish",      "Харажат Киритиш",       "Внесение Расходов"),
    "v_clients":       ("Klientlar",             "Клиентлар",             "Клиенты"),
    "v_commission":    ("Komissiya Hisoboti",    "Комиссия Ҳисоботи",    "Отчёт по Комиссии"),
}

# Indices: 0 = uz_lat, 1 = uz_cyr, 2 = ru
_LANG_INDEX = {"uz_lat": 0, "uz_cyr": 1, "ru": 2}

# Build TRANSLATIONS dict
for lang_code, idx in _LANG_INDEX.items():
    TRANSLATIONS[lang_code] = {key: vals[idx] for key, vals in _common.items()}


def get_translator(lang: str):
    """Return a callable ``t(key)`` that resolves a string for *lang*."""
    strings = TRANSLATIONS.get(lang, TRANSLATIONS["uz_lat"])

    def _t(key: str) -> str:
        return strings.get(key, key)

    return _t
