"""Runtime-editable app settings (key/value) backed by the `app_settings` table.

Used for things like the bot's "Konsultatsiya" and "Kompaniya haqida" texts
that the admin should be able to edit from the web panel.
"""
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AppSetting
from app.db.session import async_session_maker


# Default fallback values per language, used when no DB override is set.
# Keys: <prefix>_<lang>  where prefix in {consultation_text, about_text}
# and lang in {uz_lat, uz_cyr, ru}.
DEFAULTS: Dict[str, str] = {
    # ── Consultation ──
    "consultation_text_uz_lat": (
        "📞 <b>Konsultatsiya</b>\n\n"
        "Operatorimiz bilan bog'laning:\n"
        "📱 <b>+998 XX XXX XX XX</b>\n\n"
        "🕒 Ish vaqti: 09:00 — 18:00"
    ),
    "consultation_text_uz_cyr": (
        "📞 <b>Консультация</b>\n\n"
        "Операторимиз билан боғланинг:\n"
        "📱 <b>+998 XX XXX XX XX</b>\n\n"
        "🕒 Иш вақти: 09:00 — 18:00"
    ),
    "consultation_text_ru": (
        "📞 <b>Консультация</b>\n\n"
        "Свяжитесь с нашим оператором:\n"
        "📱 <b>+998 XX XXX XX XX</b>\n\n"
        "🕒 Время работы: 09:00 — 18:00"
    ),
    # ── About company ──
    "about_text_uz_lat": (
        "🏗 <b>Avtoban Stroy</b>\n\n"
        "Asfalt va yo'l qurilishi bo'yicha professional xizmat.\n\n"
        "📍 Manzil: Toshkent sh.\n"
        "📱 Tel: +998 XX XXX XX XX\n"
        "🕒 Ish vaqti: 09:00 — 18:00\n\n"
        "Ishonchli, tez va sifatli!"
    ),
    "about_text_uz_cyr": (
        "🏗 <b>Автобан Строй</b>\n\n"
        "Асфалт ва йўл қурилиши бўйича профессионал хизмат.\n\n"
        "📍 Манзил: Тошкент ш.\n"
        "📱 Тел: +998 XX XXX XX XX\n"
        "🕒 Иш вақти: 09:00 — 18:00\n\n"
        "Ишончли, тез ва сифатли!"
    ),
    "about_text_ru": (
        "🏗 <b>Avtoban Stroy</b>\n\n"
        "Профессиональные услуги по асфальтированию и строительству дорог.\n\n"
        "📍 Адрес: г. Ташкент\n"
        "📱 Тел: +998 XX XXX XX XX\n"
        "🕒 Время работы: 09:00 — 18:00\n\n"
        "Надёжно, быстро и качественно!"
    ),
}


async def get_setting(key: str, default: Optional[str] = None) -> str:
    """Fetch a single setting value, falling back to DEFAULTS or `default`."""
    async with async_session_maker() as session:
        row = (
            await session.execute(select(AppSetting).where(AppSetting.key == key))
        ).scalar_one_or_none()
        if row and row.value:
            return row.value
    if default is not None:
        return default
    return DEFAULTS.get(key, "")


async def get_all_settings() -> Dict[str, str]:
    """Return every known setting, merged with DEFAULTS for missing keys."""
    async with async_session_maker() as session:
        rows = (await session.execute(select(AppSetting))).scalars().all()
    db_map = {r.key: r.value for r in rows}
    merged: Dict[str, str] = {}
    # Always expose all default keys so the admin UI can render them.
    for k, v in DEFAULTS.items():
        merged[k] = db_map.get(k, v)
    # Include any extra keys that were stored but are not in DEFAULTS.
    for k, v in db_map.items():
        if k not in merged:
            merged[k] = v
    return merged


async def set_settings(values: Dict[str, str]) -> None:
    """Upsert multiple settings in one go."""
    if not values:
        return
    async with async_session_maker() as session:
        for key, value in values.items():
            stmt = (
                pg_insert(AppSetting)
                .values(key=key, value=value or "")
                .on_conflict_do_update(
                    index_elements=[AppSetting.key],
                    set_={"value": value or ""},
                )
            )
            await session.execute(stmt)
        await session.commit()


def lang_key(prefix: str, lang: str) -> str:
    """Compose a setting key from a prefix and language code."""
    if lang not in {"uz_lat", "uz_cyr", "ru"}:
        lang = "uz_lat"
    return f"{prefix}_{lang}"
