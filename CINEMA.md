# Dark Cinema integratsiyasi

`/panel/cinema/` menyusi dashboardga Django login orqali kirgan akkauntlarga ochiq. U yerda pulli obuna narxi,
kunlar soni va savdo holati sozlanadi. Kinolar ro'yxati, kanallar va zayavkalar
sonini ko'rish, obunachilar va to'lov tarixini tekshirish ham shu menyuda.

`bot/cinema_models.py` Dark Cinema botning `app/models/movie.py`, `subscription.py`,
`premium.py`, `audience.py` modellariga Django moslamasidir. Barcha modellar `managed=False`:
jadvallar Cinema bot tomonidan boshqariladi. Maydon nomlari, turlari va `db_table`
bir xil saqlanishi kerak. Balans mavjud `Profile.diamond` maydonidan o'qiladi.

Ishga tushirish:

1. Mafia bot, Cinema bot va dashboardni aynan bitta PostgreSQL bazasiga ulang.
2. Cinema botda `AUTO_CREATE_TABLES=true` bilan jadvallarni yarating yoki uning
   `migrations/001_create_cinema_movie.sql`, `002_create_subscriptions.sql`,
   `003_create_cinema_premium.sql`, `004_create_cinema_viewer.sql` fayllarini ketma-ket bajaring.
3. Dashboardda `python manage.py migrate` bajaring. `0007_cinema_models` faqat Django
   model holatini qayd etadi, umumiy bot jadvallarini yaratmaydi/o'zgartirmaydi.
4. **Dark Cinema → Obuna sozlamalari** da narx/muddatni tekshirib, savdoni yoqing.
   Boshlang'ich narx 100 💎, muddat 30 kun, savdo o'chirilgan.
5. Cinema botning `.env` fayliga `seller_link=https://t.me/your_seller` yozing.

Narx va muddat faqat yangi xaridlarga ta'sir qiladi. Savdoni o'chirish oldingi
faol obunalarni bekor qilmaydi. Kanal qo'shish/o'chirish Cinema bot admin panelida
bajariladi, chunki bot Telegram huquqlarini tekshiradi va mos taklif havolasini yaratadi.

Lokal testlar (production bazasiga ulanmaydi):

```bash
python manage.py test bot.test_cinema --settings=mafiadash.test_settings
```

## Auditoriya va UI yangilanishi

- Bosh sahifada jami bot obunachilari va faol pulli obunalar alohida sanaladi.
- Foydalanuvchilar ism/Telegram ID bo'yicha qidiriladi, oddiy yoki faol pulli obuna
  bo'yicha filtrlanadi. Balans uchun o'yin profili majburiy emas.
- Kino bo'limi faqat ro'yxat/qidiruv uchun. Qo'shish, tahrirlash va o'chirish
  URL'lari olib tashlangan; bular Cinema bot admin panelida bajariladi.
- Cinema botning yangi `cinema_viewer` jadvali shaxsiy muloqotni obuna tekshiruvidan
  oldin qayd etadi. Uni 004 SQL migratsiya yoki botning AUTO_CREATE_TABLES rejimi
  yaratadi. So'ng botni qayta ishga tushiring.
- Dashboard `0008_cinema_viewer` migratsiyasini ham qo'llang.

Bot auditoriyasi umumiy Mafia User jadvalidan farq qiladi. Dashboard faqat Cinema
faolligi, avvalgi xarid taklifi yoki obunasi bilan tasdiqlangan foydalanuvchilarni
sanaydi. Eski oddiy foydalanuvchining Cinema faolligi oldin qayd etilmagan bo'lsa,
u botga qayta yozganda hisobga tushadi. Jadval hali yaratilmagan bo'lsa, oldingi
xarid/obunalardagi foydalanuvchilar ko'rsatiladi va hisob yoqilmagani yoziladi.
