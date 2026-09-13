# Dark Cinema integratsiyasi

`/panel/cinema/` menyusi staff/superuser adminlarga ochiq. U yerda pulli obuna narxi,
kunlar soni va savdo holati sozlanadi. Kinolarni boshqarish, kanallar va zayavkalar
sonini ko'rish, obunachilar va to'lov tarixini tekshirish ham shu menyuda.

`bot/cinema_models.py` Dark Cinema botning `app/models/movie.py`, `subscription.py`,
`premium.py` modellariga Django moslamasidir. Barcha modellar `managed=False`:
jadvallar Cinema bot tomonidan boshqariladi. Maydon nomlari, turlari va `db_table`
bir xil saqlanishi kerak. Balans mavjud `Profile.diamond` maydonidan o'qiladi.

Ishga tushirish:

1. Mafia bot, Cinema bot va dashboardni aynan bitta PostgreSQL bazasiga ulang.
2. Cinema botda `AUTO_CREATE_TABLES=true` bilan jadvallarni yarating yoki uning
   `migrations/001_create_cinema_movie.sql`, `002_create_subscriptions.sql`,
   `003_create_cinema_premium.sql` fayllarini ketma-ket bajaring.
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
