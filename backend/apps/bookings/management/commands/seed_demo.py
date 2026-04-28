import random
import time as time_module
import urllib.request
import urllib.error
from datetime import date, time, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.users.models import CustomUser
from apps.shops.models import Shop, ShopHours, ShopPhoto, BarberShopMembership
from apps.services.models import Service, WeeklySchedule
from apps.bookings.models import Appointment, AppointmentService
from apps.reviews.models import Review


SHOP_DATA = [
    {
        "owner_email": "owner1@ibook.demo",
        "owner_name": ("Akbar", "Tursunov"),
        "name": "Prestige Barber",
        "address": "Yunusabad tumani, Toshkent",
        "lat": "41.342000",
        "lng": "69.285000",
        "description": (
            "Yunusobod tumanidagi zamonaviy sartaroshxona. "
            "Yuqori sifatli xizmat va qulay muhit."
        ),
    },
    {
        "owner_email": "owner2@ibook.demo",
        "owner_name": ("Behruz", "Xoliqov"),
        "name": "Classic Cut",
        "address": "Mirzo Ulug'bek tumani, Toshkent",
        "lat": "41.309000",
        "lng": "69.320000",
        "description": (
            "Klassik uslubdagi professional sartaroshxona. "
            "Har bir mijozga individual yondashuv."
        ),
    },
    {
        "owner_email": "owner3@ibook.demo",
        "owner_name": ("Doniyor", "Rahimov"),
        "name": "Royal Style",
        "address": "Chilonzor tumani, Toshkent",
        "lat": "41.284000",
        "lng": "69.199000",
        "description": (
            "Chilonzordagi eng mashhur sartaroshxonalardan biri. "
            "Zamonaviy texnikalar va an'anaviy xizmatlar."
        ),
    },
    {
        "owner_email": "owner4@ibook.demo",
        "owner_name": ("Eldor", "Mirzayev"),
        "name": "Gentlemen's Club",
        "address": "Sergeli tumani, Toshkent",
        "lat": "41.230000",
        "lng": "69.230000",
        "description": (
            "Janoblarga maxsus premium sartaroshxona. "
            "Dam olish va sifatli xizmatning uyg'unligi."
        ),
    },
    {
        "owner_email": "owner5@ibook.demo",
        "owner_name": ("Farrux", "Qodirov"),
        "name": "Tashkent Trim",
        "address": "Yakkasaroy tumani, Toshkent",
        "lat": "41.292000",
        "lng": "69.249000",
        "description": (
            "Yakkasaroydagi do'stona muhitli sartaroshxona. "
            "Oilalar va yoshlar uchun qulay narxlar."
        ),
    },
    {
        "owner_email": "owner6@ibook.demo",
        "owner_name": ("Jasur", "Nazarov"),
        "name": "Sultan Barbers",
        "address": "Shayxontohur tumani, Toshkent",
        "lat": "41.315000",
        "lng": "69.243000",
        "description": (
            "Shayxontohurdagi nufuzli sartaroshxona. "
            "Tajribali ustalar va qulay joy."
        ),
    },
    {
        "owner_email": "owner7@ibook.demo",
        "owner_name": ("Kamol", "Ismoilov"),
        "name": "Fresh Fade",
        "address": "Uchtepa tumani, Toshkent",
        "lat": "41.295000",
        "lng": "69.197000",
        "description": (
            "Zamonaviy fade va trend soch turmaklari ixtisosi. "
            "Uchtepadagi eng yangi sartaroshxona."
        ),
    },
    {
        "owner_email": "owner8@ibook.demo",
        "owner_name": ("Mirzo", "Usmonov"),
        "name": "Elite Grooming",
        "address": "Olmazor tumani, Toshkent",
        "lat": "41.335000",
        "lng": "69.212000",
        "description": (
            "Olmazordagi premium grooming markazi. "
            "Soqol va soch parvarishi bo'yicha mutaxassislar."
        ),
    },
    {
        "owner_email": "owner9@ibook.demo",
        "owner_name": ("Nodir", "Xasanov"),
        "name": "Sharp & Clean",
        "address": "Mirabad tumani, Toshkent",
        "lat": "41.300000",
        "lng": "69.260000",
        "description": (
            "Mirobbodda joylashgan toza va qulay sartaroshxona. "
            "Tez va sifatli xizmat."
        ),
    },
    {
        "owner_email": "owner10@ibook.demo",
        "owner_name": ("Otabek", "Yunusov"),
        "name": "Barber House",
        "address": "Bektemir tumani, Toshkent",
        "lat": "41.220000",
        "lng": "69.340000",
        "description": (
            "Bektemirdagi ishonchli sartaroshxona. "
            "Oila a'zolari uchun kompleks xizmatlar."
        ),
    },
]

BARBER_NAMES = [
    ("Aziz", "Karimov"),
    ("Bobur", "Toshmatov"),
    ("Doniyor", "Sobirov"),
    ("Eldor", "Xolmatov"),
    ("Farrukh", "Rajabov"),
    ("Jasur", "Ibragimov"),
    ("Kamol", "Abdullayev"),
    ("Mirzo", "Baxtiyorov"),
    ("Nodir", "Ergashev"),
    ("Otabek", "Sotvoldiyev"),
    ("Sardor", "Muxtarov"),
    ("Ulugbek", "Normatov"),
    ("Zafar", "Haydarov"),
    ("Akbar", "Tojiboyev"),
    ("Behruz", "Mamatov"),
    ("Dilshod", "Raximov"),
    ("Husan", "Qosimov"),
    ("Islom", "Sultonov"),
    ("Jamshid", "Nurullayev"),
    ("Kobil", "Mirzayev"),
    ("Lochinbek", "Askarov"),
    ("Mansur", "Holiqov"),
    ("Nurbek", "Xoliqov"),
    ("Pahlavon", "Jurayev"),
    ("Rahim", "Tursunov"),
    ("Saidakbar", "Yusupov"),
    ("Tohir", "Nazirov"),
    ("Umid", "Xudoyberdiyev"),
    ("Vohid", "Saidov"),
    ("Yorqin", "Razzaqov"),
    ("Zubaydullo", "Tillayev"),
    ("Alisher", "Qodirov"),
    ("Behzod", "Islamov"),
    ("Dostonbek", "Mahmudov"),
    ("Erkin", "Boymurodov"),
    ("Firdavs", "Xoliqov"),
    ("Hamid", "Nazarov"),
    ("Ilhom", "Toshpulatov"),
    ("Javlon", "Ismoilov"),
    ("Kenja", "Qurbonov"),
    ("Laziz", "Usmonov"),
    ("Muzaffar", "Abduraxmonov"),
    ("Nuriddin", "Olimov"),
    ("Odil", "Saydullayev"),
    ("Pulat", "Xasanov"),
    ("Ravshan", "Begmatov"),
    ("Shuhrat", "Tursunov"),
    ("Temur", "Rahimov"),
    ("Valijon", "Xolmatov"),
    ("Xusan", "Abdullayev"),
    ("Yunusbek", "Nazarov"),
    ("Ziyod", "Mirzayev"),
    ("Alim", "Qoraboyev"),
    ("Bahodir", "Kalandarov"),
    ("Davron", "Xoliqov"),
    ("Elbek", "Turobov"),
    ("Farhodjon", "Sotvoldiyev"),
    ("Hayot", "Tojiboyev"),
    ("Ibrohim", "Rahimov"),
    ("Jahongir", "Zokirov"),
]

CUSTOMER_NAMES = [
    ("Abdulloh", "Xoliqov"),
    ("Bekzod", "Ismoilov"),
    ("Doston", "Karimov"),
    ("Elbek", "Toshmatov"),
    ("Furqat", "Rajabov"),
    ("Hayotjon", "Ibragimov"),
    ("Ikrom", "Abdullayev"),
    ("Jamol", "Ergashev"),
    ("Kobuljon", "Normatov"),
    ("Lochin", "Haydarov"),
    ("Murod", "Tojiboyev"),
    ("Nozim", "Mamatov"),
    ("Orif", "Raximov"),
    ("Parviz", "Qosimov"),
    ("Rustam", "Sultonov"),
    ("Salim", "Nurullayev"),
    ("Timur", "Mirzayev"),
    ("Ulmas", "Jurayev"),
    ("Vohidjon", "Tursunov"),
    ("Xurshid", "Yusupov"),
]

# Independent barbers — no shop affiliation, appear on the map via lat/lng
# and in the "Solo Barbers" directory section. Coordinates are spread across
# Tashkent districts so they don't overlap shop pins.
SOLO_BARBER_DATA = [
    {"first": "Akmal",  "last": "Yusupov",   "lat": "41.327000", "lng": "69.281000",
     "bio": "Mustaqil sartarosh, uy va ofislarga xizmat ko'rsataman. 8 yillik tajriba."},
    {"first": "Ravshan", "last": "Saidov",   "lat": "41.301000", "lng": "69.265000",
     "bio": "Mobil sartaroshlik xizmati. Soqol va soch kesish bo'yicha mutaxassis."},
    {"first": "Sanjar",  "last": "Komilov",  "lat": "41.355000", "lng": "69.310000",
     "bio": "Klassik va zamonaviy soch turmagi. Mijoz uyiga keladi."},
    {"first": "Behzod",  "last": "Aliyev",   "lat": "41.275000", "lng": "69.215000",
     "bio": "Premium uy xizmatlari, fade va beard styling bo'yicha ishonchli usta."},
    {"first": "Murod",   "last": "Tashkenov","lat": "41.290000", "lng": "69.340000",
     "bio": "10 yildan ortiq tajribali mustaqil sartarosh. Onlayn band qilish mumkin."},
    {"first": "Doston",  "last": "Hakimov",  "lat": "41.320000", "lng": "69.225000",
     "bio": "Bolalar va kattalar uchun soch kesish. Mahallangizga keladi."},
    {"first": "Ilyos",   "last": "Karimov",  "lat": "41.260000", "lng": "69.295000",
     "bio": "Nikoh va tantanalar oldidan soch turmagi. Uy ofis xizmati."},
    {"first": "Otabek",  "last": "Niyozov",  "lat": "41.345000", "lng": "69.255000",
     "bio": "Skin fade, taper va beard trim bo'yicha mutaxassis. Mobil xizmat."},
]

SERVICE_TEMPLATES = [
    {"name": "Haircut",          "price_range": (40000, 70000),   "duration": 30},
    {"name": "Beard Trim",       "price_range": (25000, 45000),   "duration": 15},
    {"name": "Shave",            "price_range": (30000, 50000),   "duration": 20},
    {"name": "Hair Wash + Cut",  "price_range": (60000, 90000),   "duration": 45},
    {"name": "Kids Haircut",     "price_range": (30000, 50000),   "duration": 25},
    {"name": "Hair Color",       "price_range": (100000, 150000), "duration": 60},
]

REVIEW_COMMENTS = [
    "Ajoyib sartarosh, juda professional!",
    "Yaxshi xizmat, lekin biroz kechikdi",
    "Eng yaxshi soch kesish, albatta qaytaman",
    "O'rtacha tajriba, hech narsa alohida emas",
    "Mukammal fade, juda rozi qoldim",
    "Qo'llari oltin, mehribon munosabat",
    "Tez va sifatli xizmat ko'rsatdi",
    "Narxi yaxshi, sifat ham yetarli",
    "Sartarosh juda tajribali, tavsiya qilaman",
    "Yaxshi ish, lekin navbat uzoq kutdim",
    "Great haircut, very professional!",
    "Good service, took a bit longer than expected",
    "Excellent fade, will definitely come back",
    "Average experience, nothing special",
    "The barber was friendly and skilled",
    "Clean place, great atmosphere",
    "Value for money, will return",
    "Very satisfied with the result",
    "Professional service, highly recommend",
    "Nice work on the beard trim",
    "Soch turmagi juda chiroyli chiqdi",
    "Ustaning qo'llari usta, mamnun bo'ldim",
    "Soqol olish xizmati a'lo darajada",
    "Bolam uchun soch kesish juda yaxshi o'tdi",
    "Navbat olish qulay, xizmat sifatli",
]


def _weighted_rating():
    """Skewed toward 4-5 stars like real reviews."""
    r = random.random()
    if r < 0.50:
        return 5
    elif r < 0.75:
        return 4
    elif r < 0.90:
        return 3
    elif r < 0.97:
        return 2
    else:
        return 1


class Command(BaseCommand):
    help = "Seed demo data for IBook — shops, barbers, customers, appointments, reviews"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== IBook Demo Seed ===\n"))

        random.seed(42)  # reproducible across re-runs

        self._seed_admin()
        owners = self._seed_owners()
        shops = self._seed_shops(owners)
        self._seed_shop_hours(shops)
        # Cover any shop in the DB, not only the demo ones — some may have been
        # created manually via admin or the app UI.
        self._seed_shop_photos(list(Shop.objects.all()))
        shop_barbers = self._seed_barbers(shops)
        solo_barbers = self._seed_solo_barbers()
        barbers = shop_barbers + solo_barbers
        barber_services = self._seed_services(barbers)
        self._seed_weekly_schedules(barbers)
        customers = self._seed_customers()
        appointments = self._seed_appointments(barbers, barber_services, customers)
        self._seed_reviews(appointments)

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeded: {len(shops)} shops, {len(shop_barbers)} shop barbers, "
            f"{len(solo_barbers)} solo barbers, {len(customers)} customers, "
            f"{appointments} appointments, reviews created for ~80% of appointments\n"
        ))

    def _seed_admin(self):
        email = "admin@ibook.demo"
        admin, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": "Site",
                "last_name": "Admin",
                "role": CustomUser.Role.SHOP_OWNER,
                "is_active": True,
                "is_email_verified": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin1234")
            admin.save()
        else:
            admin.is_staff = True
            admin.is_superuser = True
            admin.is_active = True
            admin.set_password("admin1234")
            admin.save()
        self.stdout.write(f"  Admin:     {email} / admin1234")

    def _seed_owners(self):
        owners = []
        for i, shop_data in enumerate(SHOP_DATA, start=1):
            email = shop_data["owner_email"]
            first, last = shop_data["owner_name"]
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": first,
                    "last_name": last,
                    "role": CustomUser.Role.SHOP_OWNER,
                    "is_active": True,
                    "is_email_verified": True,
                },
            )
            if created:
                user.set_password("demo1234")
                user.save()
            owners.append(user)

        self.stdout.write(f"  Owners:    {len(owners)} ready")
        return owners

    def _seed_shops(self, owners):
        shops = []
        for owner, shop_data in zip(owners, SHOP_DATA):
            shop, _ = Shop.objects.get_or_create(
                name=shop_data["name"],
                defaults={
                    "owner": owner,
                    "address": shop_data["address"],
                    "lat": shop_data["lat"],
                    "lng": shop_data["lng"],
                    "description": shop_data["description"],
                },
            )
            shops.append(shop)

        self.stdout.write(f"  Shops:     {len(shops)} ready")
        return shops

    def _seed_shop_hours(self, shops):
        count = 0
        for shop in shops:
            for day in range(7):
                is_sunday = day == 6
                ShopHours.objects.get_or_create(
                    shop=shop,
                    day_of_week=day,
                    defaults={
                        "is_open": not is_sunday,
                        "opens_at": None if is_sunday else time(9, 0),
                        "closes_at": None if is_sunday else time(20, 0),
                    },
                )
                count += 1

        self.stdout.write(f"  ShopHours: {count} rows ready")

    # Curated barbershop photos hosted on the Unsplash CDN.
    # LoremFlickr / Picsum were both replaced with "slop.jop" placeholder
    # images, so we hit Unsplash's image CDN directly with known photo IDs.
    BARBERSHOP_PHOTO_IDS = (
        "1503951914875-452162b0f3f1",
        "1521590832167-7bcbfaa6381f",
        "1622286342621-4bd786c2447c",
        "1599351431202-1e0f0137899a",
        "1567894340315-735d7c361db0",
        "1585747860715-2ba37e788b70",
        "1493256338651-d82f7acb2b38",
        "1517832606299-7ae9b720a186",
        "1605497788044-5a32c7078486",
        "1506634572416-48cdfe530110",
        "1580618672591-eb180b1a973f",
    )

    # Square-ish portraits for solo-barber avatars. Cropped to 600x600.
    BARBER_PORTRAIT_IDS = (
        "1500648767791-00dcc994a43e",
        "1507003211169-0a1dd7228f2d",
        "1531427186611-ecfd6d936c79",
        "1492562080023-ab3db95bfbce",
        "1519085360753-af0119f7cbe7",
        "1564564321837-a57b7070ac4f",
        "1599566150163-29194dcaad36",
        "1463453091185-61582044d556",
    )

    def _seed_shop_photos(self, shops):
        """
        Download barbershop photos from the Unsplash CDN and save them as
        ShopPhoto rows. Photos are picked from a curated, deterministic list
        keyed off shop id + photo index so re-runs are stable.

        Idempotent: shops that already have any photo are skipped.
        """
        photos_per_shop = 3
        width, height = 1200, 900
        total_created = 0
        total_failed = 0
        ids = self.BARBERSHOP_PHOTO_IDS

        for shop in shops:
            if shop.photos.exists():
                continue

            for n in range(1, photos_per_shop + 1):
                photo_id = ids[(shop.id * photos_per_shop + n) % len(ids)]
                url = (
                    f"https://images.unsplash.com/photo-{photo_id}"
                    f"?w={width}&h={height}&fit=crop&q=80"
                )
                data = self._download_image(url)
                if data is None:
                    total_failed += 1
                    continue

                filename = f"{slugify(shop.name)}-{n}.jpg"
                photo = ShopPhoto(shop=shop)
                photo.image.save(filename, ContentFile(data), save=True)
                total_created += 1

                time_module.sleep(0.2)

        if total_failed:
            self.stdout.write(
                f"  Photos:    {total_created} downloaded ({total_failed} failed)"
            )
        else:
            self.stdout.write(f"  Photos:    {total_created} downloaded")

    def _download_image(self, url):
        """Return image bytes, or None on failure."""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; IBook-seed/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            self.stdout.write(
                self.style.WARNING(f"  [warn] image fetch failed: {url} — {e}")
            )
            return None

    def _seed_barbers(self, shops):
        barbers = []
        name_iter = iter(BARBER_NAMES)
        barber_index = 1

        for shop in shops:
            count = random.randint(5, 7)
            for _ in range(count):
                try:
                    first, last = next(name_iter)
                except StopIteration:
                    name_iter = iter(BARBER_NAMES)
                    first, last = next(name_iter)

                email = f"barber{barber_index}@ibook.demo"
                barber, created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        "username": email,
                        "first_name": first,
                        "last_name": last,
                        "role": CustomUser.Role.BARBER,
                        "is_active": True,
                        "is_email_verified": True,
                        "years_of_experience": random.randint(1, 12),
                    },
                )
                if created:
                    barber.set_password("demo1234")
                    barber.save()

                BarberShopMembership.objects.get_or_create(
                    shop=shop,
                    barber=barber,
                )
                barbers.append((barber, shop))
                barber_index += 1

        self.stdout.write(f"  Barbers:   {len(barbers)} ready")
        return barbers

    def _seed_solo_barbers(self):
        """
        Seed independent (solo) barbers — role=BARBER with no shop membership.
        Each gets coordinates, a short bio, and an avatar so they show up in
        the customer "Solo Barbers" directory and on the explore map.

        Idempotent: existing users with the same email are reused.
        """
        portrait_ids = self.BARBER_PORTRAIT_IDS
        solo = []

        for i, data in enumerate(SOLO_BARBER_DATA, start=1):
            email = f"solo_barber{i}@ibook.demo"
            barber, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": data["first"],
                    "last_name": data["last"],
                    "role": CustomUser.Role.BARBER,
                    "is_active": True,
                    "is_email_verified": True,
                    "years_of_experience": random.randint(3, 14),
                    "lat": data["lat"],
                    "lng": data["lng"],
                    "bio": data["bio"],
                },
            )
            if created:
                barber.set_password("demo1234")
                barber.save()

            # Backfill coords/bio/avatar on existing rows that pre-date these
            # fields, but never overwrite an avatar the user already uploaded.
            updates = {}
            if not barber.lat:
                updates["lat"] = data["lat"]
            if not barber.lng:
                updates["lng"] = data["lng"]
            if not barber.bio:
                updates["bio"] = data["bio"]
            if updates:
                CustomUser.objects.filter(pk=barber.pk).update(**updates)

            if not barber.avatar:
                portrait_id = portrait_ids[(i - 1) % len(portrait_ids)]
                url = (
                    f"https://images.unsplash.com/photo-{portrait_id}"
                    "?w=600&h=600&fit=crop&q=80"
                )
                data_bytes = self._download_image(url)
                if data_bytes is not None:
                    filename = f"solo-{slugify(data['first'])}-{slugify(data['last'])}.jpg"
                    barber.avatar.save(filename, ContentFile(data_bytes), save=True)
                    time_module.sleep(0.2)

            solo.append((barber, None))

        self.stdout.write(f"  Solo barbers: {len(solo)} ready")
        return solo

    def _seed_services(self, barbers):
        barber_services = {}
        total = 0

        for barber, _shop in barbers:
            templates = random.sample(SERVICE_TEMPLATES, random.randint(4, 6))
            services = []
            for sort_idx, tmpl in enumerate(templates):
                lo, hi = tmpl["price_range"]
                price = round(random.randint(lo, hi) / 5000) * 5000
                svc, _ = Service.objects.get_or_create(
                    barber=barber,
                    name=tmpl["name"],
                    defaults={
                        "price": price,
                        "duration_minutes": tmpl["duration"],
                        "sort_order": sort_idx,
                    },
                )
                services.append(svc)
                total += 1
            barber_services[barber.id] = services

        self.stdout.write(f"  Services:  {total} ready")
        return barber_services

    def _seed_weekly_schedules(self, barbers):
        count = 0
        for barber, _shop in barbers:
            for day in range(7):
                is_sunday = day == 6
                WeeklySchedule.objects.get_or_create(
                    barber=barber,
                    day_of_week=day,
                    defaults={
                        "is_working": not is_sunday,
                        "start_time": None if is_sunday else time(9, 0),
                        "end_time": None if is_sunday else time(19, 0),
                    },
                )
                count += 1

        self.stdout.write(f"  Schedules: {count} rows ready")

    def _seed_customers(self):
        customers = []
        for i, (first, last) in enumerate(CUSTOMER_NAMES, start=1):
            email = f"customer{i}@ibook.demo"
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": first,
                    "last_name": last,
                    "role": CustomUser.Role.CUSTOMER,
                    "is_active": True,
                    "is_email_verified": True,
                },
            )
            if created:
                user.set_password("demo1234")
                user.save()
            customers.append(user)

        self.stdout.write(f"  Customers: {len(customers)} ready")
        return customers

    def _seed_appointments(self, barbers, barber_services, customers):
        today = date.today()
        total_created = 0
        total_skipped = 0

        self._all_appointments = []

        for barber, _shop in barbers:
            services = barber_services.get(barber.id, [])
            if not services:
                continue

            appt_count = random.randint(10, 30)
            for _ in range(appt_count):
                appt_date = today - timedelta(days=random.randint(1, 90))
                slot_index = random.randint(0, 17)
                hour = 9 + slot_index // 2
                minute = 30 * (slot_index % 2)
                start_t = time(hour, minute)

                num_svcs = random.randint(1, min(2, len(services)))
                chosen_svcs = random.sample(services, num_svcs)
                total_price = sum(s.price for s in chosen_svcs)
                total_duration = sum(s.duration_minutes for s in chosen_svcs)

                end_hour = hour + (minute + total_duration) // 60
                end_minute = (minute + total_duration) % 60
                end_t = time(min(end_hour, 23), end_minute)

                customer = random.choice(customers)
                payment_method = random.choice([
                    Appointment.PaymentMethod.ONLINE,
                    Appointment.PaymentMethod.AT_SHOP,
                ])

                appt, created = Appointment.objects.get_or_create(
                    barber=barber,
                    customer=customer,
                    date=appt_date,
                    start_time=start_t,
                    defaults={
                        "end_time": end_t,
                        "status": Appointment.Status.COMPLETED,
                        "payment_method": payment_method,
                        "payment_status": Appointment.PaymentStatus.PAID,
                        "total_price": total_price,
                        "total_duration": total_duration,
                    },
                )

                if created:
                    for svc in chosen_svcs:
                        AppointmentService.objects.get_or_create(
                            appointment=appt,
                            service=svc,
                            defaults={
                                "service_name": svc.name,
                                "service_price": svc.price,
                                "service_duration": svc.duration_minutes,
                            },
                        )
                    self._all_appointments.append(appt)
                    total_created += 1
                else:
                    self._all_appointments.append(appt)
                    total_skipped += 1

        self.stdout.write(
            f"  Appointments: {total_created} created, {total_skipped} already existed"
        )
        return total_created

    def _seed_reviews(self, appointment_count):
        appointments = getattr(self, "_all_appointments", [])
        if not appointments:
            appointments = list(
                Appointment.objects.filter(status=Appointment.Status.COMPLETED)
                .select_related("customer", "barber")
            )

        review_fraction = random.uniform(0.70, 0.90)
        to_review = random.sample(appointments, int(len(appointments) * review_fraction))

        created_count = 0
        for appt in to_review:
            rating = _weighted_rating()
            comment = random.choice(REVIEW_COMMENTS)
            _review, created = Review.objects.get_or_create(
                appointment=appt,
                defaults={
                    "reviewer": appt.customer,
                    "barber": appt.barber,
                    "rating": rating,
                    "text": comment,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            f"  Reviews:  {created_count} created "
            f"({len(to_review)} selected from {len(appointments)} appointments)"
        )
