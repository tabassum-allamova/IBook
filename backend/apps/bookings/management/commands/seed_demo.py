import random
from datetime import date, time, timedelta

from django.core.management.base import BaseCommand

from apps.users.models import CustomUser
from apps.shops.models import Shop, ShopHours, BarberShopMembership
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

        owners = self._seed_owners()
        shops = self._seed_shops(owners)
        self._seed_shop_hours(shops)
        barbers = self._seed_barbers(shops)
        barber_services = self._seed_services(barbers)
        self._seed_weekly_schedules(barbers)
        customers = self._seed_customers()
        appointments = self._seed_appointments(barbers, barber_services, customers)
        self._seed_reviews(appointments)

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeded: {len(shops)} shops, {len(barbers)} barbers, "
            f"{len(customers)} customers, {appointments} appointments, "
            f"reviews created for ~80% of appointments\n"
        ))

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
