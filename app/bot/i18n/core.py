"""
Internationalization core module.
Supports: uz_lat (O'zbek lotin), uz_cyr (Ўзбек кирилл), ru (Русский)
"""
from app.db.models import Language

_DEFAULT_LANG = Language.UZ_LAT


def get_lang(user) -> str:
    """Get language code from user object, default to uz_lat."""
    if user and hasattr(user, "language") and user.language:
        return user.language
    return _DEFAULT_LANG.value


def t(key: str, lang: str = "uz_lat", **kwargs) -> str:
    """Get translated string by key and language code."""
    from .uz_lat import STRINGS as UZ_LAT
    from .uz_cyr import STRINGS as UZ_CYR
    from .ru import STRINGS as RU

    _ALL = {"uz_lat": UZ_LAT, "uz_cyr": UZ_CYR, "ru": RU}
    lang_dict = _ALL.get(lang, UZ_LAT)
    text = lang_dict.get(key) or UZ_LAT.get(key) or key
    if kwargs:
        text = text.format(**kwargs)
    return text


def _btn_variants(key: str) -> set:
    """Get all language variants for a button text key."""
    from .uz_lat import STRINGS as UZ_LAT
    from .uz_cyr import STRINGS as UZ_CYR
    from .ru import STRINGS as RU

    variants = set()
    for lang_dict in (UZ_LAT, UZ_CYR, RU):
        val = lang_dict.get(key)
        if val:
            variants.add(val)
    return variants


# Collect all button text variants across all languages for F.text.in_() filters
ALL_BUTTON_TEXTS: dict[str, set] = {}


def build_button_variants():
    """Build ALL_BUTTON_TEXTS dict: key -> {uz_lat_text, uz_cyr_text, ru_text}."""
    from .uz_lat import STRINGS as UZ_LAT
    btn_keys = [k for k in UZ_LAT if k.startswith("btn_")]
    for key in btn_keys:
        ALL_BUTTON_TEXTS[key] = _btn_variants(key)


build_button_variants()
