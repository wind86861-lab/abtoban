"""Seed Uzbekistan viloyats and tumans, and backfill existing users/orders.

Usage:
    python -m scripts.seed_viloyats_tumans
"""
import asyncio
from sqlalchemy import select

from app.db.session import async_session_maker as AsyncSessionLocal
from app.db.models import Viloyat, Tuman, Region, User, Order


# Uzbekistan viloyats and their tumans
UZ_DATA = {
    "Toshkent shahri": [
        "Bektemir", "Chilonzor", "Mirobod", "Mirzo Ulug'bek", "Olmazor",
        "Sergeli", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Yashnobod",
        "Yunusobod", "Yangihayot",
    ],
    "Toshkent viloyati": [
        "Bekobod", "Bo'ka", "Bo'stonliq", "Chinoz", "Ohangaron", "Oqqo'rg'on",
        "Parkent", "Piskent", "Qibray", "Quyichirchiq", "O'rtachirchiq",
        "Yangiyo'l", "Yuqorichirchiq", "Zangiota",
    ],
    "Andijon viloyati": [
        "Andijon shahri", "Asaka", "Baliqchi", "Bo'z", "Buloqboshi",
        "Izboskan", "Jalaquduq", "Xo'jaobod", "Qo'rg'ontepa", "Marhamat",
        "Oltinko'l", "Paxtaobod", "Shahrixon", "Ulug'nor",
    ],
    "Buxoro viloyati": [
        "Buxoro shahri", "Olot", "G'ijduvon", "Jondor", "Kogon",
        "Qorako'l", "Qorovulbozor", "Peshku", "Romitan", "Shofirkon",
        "Vobkent",
    ],
    "Farg'ona viloyati": [
        "Farg'ona shahri", "Marg'ilon", "Qo'qon", "Quva", "Rishton",
        "Beshariq", "Bog'dod", "Buvayda", "Dang'ara", "Furqat",
        "Oltiariq", "O'zbekiston", "So'x", "Toshloq", "Yozyovon",
    ],
    "Jizzax viloyati": [
        "Jizzax shahri", "Arnasoy", "Baxmal", "Do'stlik", "Forish",
        "G'allaorol", "Mirzacho'l", "Paxtakor", "Yangiobod", "Zafarobod",
        "Zarbdor", "Zomin",
    ],
    "Xorazm viloyati": [
        "Urganch", "Bog'ot", "Gurlan", "Qo'shko'pir", "Xiva",
        "Xonqa", "Hazorasp", "Shovot", "Urganch tumani", "Yangiariq",
        "Yangibozor",
    ],
    "Namangan viloyati": [
        "Namangan shahri", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq",
        "Namangan tumani", "Norin", "Pop", "To'raqo'rg'on", "Uchqo'rg'on",
        "Uychi", "Yangiqo'rg'on",
    ],
    "Navoiy viloyati": [
        "Navoiy shahri", "Konimex", "Qiziltepa", "Karmana", "Navbahor",
        "Nurota", "Tomdi", "Uchquduq", "Xatirchi",
    ],
    "Qashqadaryo viloyati": [
        "Qarshi", "Shahrisabz", "Chiroqchi", "Dehqonobod", "G'uzor",
        "Kasbi", "Kitob", "Koson", "Mirishkor", "Muborak", "Nishon",
        "Qamashi", "Yakkabog'",
    ],
    "Qoraqalpog'iston Respublikasi": [
        "Nukus", "Amudaryo", "Beruniy", "Chimboy", "Ellikqal'a",
        "Kegeyli", "Mo'ynoq", "Nukus tumani", "Qanliko'l", "Qonliko'l",
        "Qo'ng'irot", "Qorao'zak", "Shumanay", "Taxiatosh", "Taxtako'pir",
        "To'rtko'l", "Xo'jayli",
    ],
    "Samarqand viloyati": [
        "Samarqand shahri", "Bulung'ur", "Ishtixon", "Jomboy", "Kattaqo'rg'on",
        "Narpay", "Nurobod", "Oqdaryo", "Pastdarg'om", "Paxtachi",
        "Payariq", "Qo'shrabot", "Samarqand tumani", "Toyloq", "Urgut",
    ],
    "Sirdaryo viloyati": [
        "Guliston", "Boyovut", "Mirzaobod", "Oqoltin", "Sardoba",
        "Sayxunobod", "Sirdaryo tumani", "Xovos", "Yangiyer",
    ],
    "Surxondaryo viloyati": [
        "Termiz", "Angor", "Bandixon", "Boysun", "Denov", "Jarqo'rg'on",
        "Qiziriq", "Qumqo'rg'on", "Muzrabot", "Oltinsoy", "Sariosiyo",
        "Sherobod", "Sho'rchi", "Termiz tumani", "Uzun",
    ],
}


async def main():
    async with AsyncSessionLocal() as session:
        # Create Viloyats and Tumans
        existing = (await session.execute(select(Viloyat.name))).scalars().all()
        existing_names = set(existing)

        for v_name, tumans in UZ_DATA.items():
            if v_name in existing_names:
                # fetch existing
                vres = await session.execute(select(Viloyat).where(Viloyat.name == v_name))
                v = vres.scalar_one()
            else:
                v = Viloyat(name=v_name)
                session.add(v)
                await session.flush()
                print(f"+ Viloyat: {v_name}")

            # existing tumans for this viloyat
            tres = await session.execute(
                select(Tuman.name).where(Tuman.viloyat_id == v.id)
            )
            existing_tumans = set(tres.scalars().all())

            for t_name in tumans:
                if t_name not in existing_tumans:
                    session.add(Tuman(viloyat_id=v.id, name=t_name))
                    print(f"  + Tuman: {t_name}")

        await session.commit()
        print("Seed complete.")

        # Backfill: for Users/Orders with region_id, try to map to viloyat+tuman
        # by matching Region.viloyat / Region.tuman strings to Viloyat.name / Tuman.name
        regions = (await session.execute(select(Region))).scalars().all()
        viloyats = (await session.execute(select(Viloyat))).scalars().all()
        v_by_name = {v.name.lower(): v for v in viloyats}

        tumans_all = (await session.execute(select(Tuman))).scalars().all()

        def find_viloyat(name):
            if not name:
                return None
            key = name.strip().lower()
            for vn, v in v_by_name.items():
                if key in vn or vn in key:
                    return v
            return None

        def find_tuman(viloyat_id, name):
            if not name or not viloyat_id:
                return None
            key = name.strip().lower()
            for t in tumans_all:
                if t.viloyat_id != viloyat_id:
                    continue
                tn = t.name.lower()
                if key in tn or tn in key:
                    return t
            return None

        region_map = {}
        for r in regions:
            v = find_viloyat(r.viloyat or r.name)
            t = find_tuman(v.id, r.tuman) if v else None
            region_map[r.id] = (v.id if v else None, t.id if t else None)

        # Backfill Users
        users = (await session.execute(select(User).where(User.region_id.isnot(None)))).scalars().all()
        updated_u = 0
        for u in users:
            vid, tid = region_map.get(u.region_id, (None, None))
            if u.viloyat_id is None and vid:
                u.viloyat_id = vid
                updated_u += 1
            if u.tuman_id is None and tid:
                u.tuman_id = tid

        # Backfill Orders
        orders = (await session.execute(select(Order).where(Order.region_id.isnot(None)))).scalars().all()
        updated_o = 0
        for o in orders:
            vid, tid = region_map.get(o.region_id, (None, None))
            if o.viloyat_id is None and vid:
                o.viloyat_id = vid
                updated_o += 1
            if o.tuman_id is None and tid:
                o.tuman_id = tid

        await session.commit()
        print(f"Backfilled {updated_u} users and {updated_o} orders.")


if __name__ == "__main__":
    asyncio.run(main())
