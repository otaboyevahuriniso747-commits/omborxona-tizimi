# LOYIHA ISHI

**Mavzu:** Omborxona mahsulotlar qoldig'ini nazorat qiluvchi va kam qolganda ogohlantiruvchi tizim (Inventory Management System).

## 1. Kirish
Ushbu loyiha ishi zamonaviy korxonalar, do'konlar va omborxonalar uchun mahsulotlar zaxirasini avtomatlashtirilgan tarzda nazorat qilish tizimini yaratishga qaratilgan. Tizimning asosiy maqsadi – ombordagi mahsulotlar qoldig'i haqida aniq va tezkor ma'lumot berish, shuningdek, zaxirasi tugab borayotgan mahsulotlar haqida foydalanuvchini o'z vaqtida ogohlantirishdir. Bu esa o'z navbatida biznes jarayonlarida uzilishlar bo'lishining oldini oladi.

## 2. Loyihaning Maqsad va Vazifalari
**Maqsad:** Foydalanuvchilar uchun qulay, tezkor va interaktiv veb-ilovaga asoslangan ombor nazorati tizimini ishlab chiqish.

**Vazifalar:**
- Mahsulotlarni tizimga kiritish, tahrirlash va o'chirish (CRUD operatsiyalari).
- Mahsulotlarning joriy qoldig'ini ko'rsatib borish.
- Har bir mahsulot uchun minimal zaxira chegarasini (min) belgilash.
- Mahsulot zaxirasi belgilangan chegaradan tushib ketsa, avtomatik ravishda "Kam qolgan" yoki "Tugagan" holatiga o'tkazish.
- Ma'lumotlarni qidirish qulayligini ta'minlash.

## 3. Foydalanilgan Texnologiyalar
Veb-ilova to'liq "Client-side" (Mijoz tomoni) usulida ishlab chiqilgan bo'lib, quyidagi texnologiyalardan foydalanildi:
*   **HTML5:** Veb-ilovaning strukturasi va semantikasi uchun.
*   **CSS3 (Vanilla):** Dizayn va vizual ko'rinish. Loyihada zamonaviy **Glassmorphism** (oyna effekti) va **Dark Mode** (qorong'u mavzu) uslublaridan foydalanildi.
*   **JavaScript (ES6+):** Ilovaning mantiqiy ishlashi, qidiruv tizimi, modal oynalar, va dinamik jadvalni boshqarish uchun.
*   **LocalStorage:** Ma'lumotlar bazasi o'rnida foydalanuvchining brauzer xotirasidan foydalanildi. Bu internetga ulanmagan holatda ham tez ishlash imkonini beradi.
*   **FontAwesome:** Veb-ilovada tushunarli va chiroyli ikonkalardan foydalanish uchun.

## 4. Tizimning Asosiy Imkoniyatlari (Features)

### 4.1. Asosiy Panel (Dashboard)
Asosiy oynada 3 ta muhim ko'rsatkich animatsiya yordamida foydalanuvchiga taqdim etiladi:
1.  **Jami Mahsulot Turlari:** Tizimga kiritilgan barcha mahsulotlarning umumiy soni.
2.  **Kam Qolgan:** Zaxirasi minimal chegaradan (masalan, 10 donadan) kamayib qolgan mahsulotlar soni.
3.  **Tugagan:** Ombor qoldig'i 0 ga teng bo'lgan mahsulotlar soni.

### 4.2. Mahsulotlarni Boshqarish (Jadval)
Barcha mahsulotlar qulay jadval ko'rinishida taqdim etiladi. Jadval ustunlari quyidagilardan iborat:
*   **Nomi va Toifasi:** Mahsulotni identifikatsiya qilish uchun.
*   **Miqdori va Min. Chegara:** Mahsulot qoldig'i va ogohlantirish chegarasi.
*   **Holati:** Tizim avtomatik ravishda mahsulot holatini baholaydi va maxsus nishonlar (badge) bilan ko'rsatadi:
    *   🟢 **Yaxshi** - Zaxira yetarli.
    *   🟡 **Kam qolgan** - Zaxira minimal chegaraga yetgan yoki undan kam.
    *   🔴 **Tugagan** - Mahsulot zaxirasi umuman qolmagan.
*   **Amallar:** Mahsulot ma'lumotlarini tahrirlash va o'chirish tugmalari.

### 4.3. Aqlli Qidiruv
Tizim yuqori qismida joylashgan qidiruv maydoni orqali mahsulot nomiga yoki toifasiga ko'ra jadvaldan bir zumda ma'lumotlarni saralab (filtr) topish imkonini beradi. Qidiruv jarayoni real vaqt rejimida ishlaydi (har bir harf kiritilganda jadval yangilanadi).

### 4.4. Modal Oyna Orqali Qo'shish va Tahrirlash
Yangi mahsulot kiritish yoki mavjudini tahrirlashda alohida sahifaga o'tmasdan, ekranning markazida ochiluvchi interaktiv **Modal oyna**dan foydalaniladi. Bunda quyidagi ma'lumotlar kiritiladi:
*   Mahsulot nomi
*   Toifasi
*   Qoldiq miqdori
*   O'lchov birligi (dona, kg, litr, quti, metr va h.k.)
*   Minimal ogohlantirish chegarasi

## 5. Arxitektura va Kod Tuzilishi
*   **CSS O'zgaruvchilari (Variables):** Ranglar panitrasini boshqarish uchun `:root` da barcha ranglar e'lon qilingan.
*   **Interfeys Mantiqi:** Asosiy interfeys ikkiga ajratilgan: Sidebar (chap panel) va Main Content (asosiy qism).
*   **State Management (Holatni boshqarish):** Barcha mahsulotlar bitta global massivida saqlanadi. Har qanday o'zgarish (qo'shish, o'chirish, tahrirlash) ushbu massivda amalga oshiriladi va darhol `saveData()` funksiyasi orqali `LocalStorage`ga sinxronlanadi. Shundan so'ng DOM interfeysi yangilanadi.

## 6. Kod Namunasi va Ishlash Mantiqi
Tizimning eng muhim qismlaridan biri ma'lumotlarni brauzer xotirasiga saqlash (`LocalStorage`) va uni ekranga chizishdir. Quyida jadvalni dinamik yaratuvchi JavaScript funksiyasidan qisqacha namuna keltirilgan:

```javascript
// Mahsulotning qoldig'iga qarab vizual holatini (status) aniqlash
let statusHtml = '';
if (product.quantity <= 0) {
    statusHtml = '<span class="status-badge status-danger">Tugagan</span>';
} else if (product.quantity <= product.min) {
    statusHtml = '<span class="status-badge status-warning">Kam qolgan</span>';
} else {
    statusHtml = '<span class="status-badge status-normal">Yaxshi</span>';
}
```
Yuqoridagi kod yordamida har bir mahsulot ombordagi minimal miqdoriga qarab, avtomatlashgan tarzda qizil ("Tugagan"), sariq ("Kam qolgan") yoki yashil ("Yaxshi") maqomlariga o'tadi. Bu orqali omborchi qaysi mahsulot tugayotganini bitta qarashda bilib oladi.

## 7. Xulosa va Kelgusidagi Rejalar
Yaratilgan mazkur "Omborxona" nazorati tizimi kichik va o'rta biznes vakillari uchun qog'ozbozlikdan voz kechish, ma'lumotlarni xatosiz saqlash va eng muhimi – **mahsulotlar yetishmovchiligining oldini olishda** juda qulay vosita bo'lib xizmat qiladi.

**Kelgusida loyihani rivojlantirish uchun quyidagi imkoniyatlarni qo'shish tavsiya qilinadi:**
1.  **Backend Integratsiyasi:** Node.js / Python kabi tillar orqali ma'lumotlarni markazlashtirilgan server ma'lumotlar bazasida saqlash.
2.  **Foydalanuvchilar Rollari (Auth):** Tizimga kirish tizimi (Admin, omborchi, kassir kabi).
3.  **Eksport va Import:** Jadvaldagi hisobotlarni PDF yoki Excel formatida yuklab olish funksiyasi hamda Exceldan ma'lumotlarni birdaniga tizimga kiritish.
4.  **Harakatlar Tarixi (History):** Qachon va kim tomonidan qancha mahsulot kirim qilingani yoki chiqim qilingani tarixini yuritish.
