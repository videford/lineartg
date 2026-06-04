reg-ask-name = Xush kelibsiz! Ism va familiyangizni kiriting (masalan: Alisher Karimov) — ular vazifalarda koʻrsatiladi.
reg-name-invalid = Iltimos, ism va familiyani boʻsh joy bilan kiriting (masalan: Alisher Karimov).
reg-done = Tayyor, { $name }! Profil saqlandi.
whoami = Siz: { $name }
    { $status }

# status / profile
status-admin = 👑 Administrator (toʻliq huquq)
status-lead = ⭐ Loyiha lideri: { $projects }
status-member = 👤 Aʼzo
profile-card = 👤 Profil
    Ism: { $name }
    Holat: { $status }
profile-change-name = ✏️ Ismni oʻzgartirish
profile-send-name = Yangi ism va familiyangizni yuboring (masalan: Ali Valiyev).
profile-name-updated = Tayyor, ism yangilandi: { $name }

start-welcome = Salom, { $name }!
    { $status }
start-choose-lang = Interfeys tilini tanlang:
lang-set = Tayyor, til saqlandi.
help-body =
    Buyruqlar:
    /task — vazifa yaratish
    /my — mening vazifalarim
    /assign — vazifa biriktirish (lead/admin)
    /connect — Linearni ulash (admin)
    /bind — ushbu chatni bogʻlash (admin)
    /setrole — rolni oʻzgartirish (admin)
    Sizning rolingiz: { $role }

err-no-permission = Bu amal uchun ruxsatingiz yoʻq.
err-no-workspace = Linear hali ulanmagan. Admin /connect buyrugʻini bajarishi kerak.
err-no-projects = Linearda mavjud loyihalar yoʻq.
err-unknown-member = Foydalanuvchi botda topilmadi.

task-choose-project = Loyihani tanlang:
task-send-title = Vazifa matnini bitta xabarda yuboring.
task-send-title-seeded = Vazifa matnini yuboring (yoki asl xabarni qayta yuboring).
task-created = ✅ Vazifa yaratildi { $identifier }: { $url }

assign-choose-member = Kimga biriktirilsin?
assign-dm-failed = { $name }ga shaxsiy xabar yuborilmadi — u /start orqali botni ochsin.
assigned-dm = 📌 Sizga vazifa biriktirildi { $identifier }: { $title } (biriktirdi: { $by })
assign-no-team = Bu loyihada hali aʼzolar yoʻq. Ularni 📂 Loyihalar orqali qoʻshing.
assign-not-in-team = Bu foydalanuvchi loyiha jamoasida emas.

my-title = Mening vazifalarim
search-results = Qidiruv natijalari
list-count = jami: { $n }
list-empty = Bu filtr boʻyicha vazifalar yoʻq.
list-f-all = Hammasi
list-f-todo = Bajariladi
list-f-inprogress = Jarayonda
list-f-done = Tayyor
list-f-backlog = Backlog
list-prev = ◀
list-next = ▶
list-page = { $page }/{ $total }
my-no-label = Profilingiz hali bogʻlanmagan. /start ni bajaring.
my-empty = Sizda faol vazifalar yoʻq.
my-issue-line = { $identifier } · { $title }
    Holat: { $state } · Loyiha: { $project }

status-changed = 🔁 { $identifier } → { $state }
comment-prompt = Izoh matnini yozing:
comment-added = 💬 Izoh qoʻshildi.

connect-link = Havolani oching va Linearda ilovani avtorizatsiya qiling:
    { $url }
bind-ok = Chat bogʻlandi. Linear bildirishnomalari shu yerga keladi.

setrole-usage = Foydalanish: aʼzo xabariga javoban /setrole <member|lead|admin>
setrole-ok = { $name } roli { $role } ga oʻzgartirildi.

notify-comment = 💬 { $user }: { $body }
notify-status = 🔁 { $identifier } → { $state }

# task card
card-not-found = Vazifa topilmadi.
card-f-status = Holat
card-f-priority = Muhimlik
card-f-project = Loyiha
card-f-assignee = Ijrochi
card-f-due = Muddat
card-f-estimate = Baho
card-f-labels = Teglar
sub-on = 🔔 Obuna boʻldingiz
sub-off = 🔕 Obuna bekor qilindi
sub-other-done = Obuna qilindi: { $name }
sub-added-dm = 🔔 Sizni { $identifier } vazifasiga obuna qilishdi (kim: { $by })
toast-saved = Saqlandi
due-prompt = Sanani YYYY-MM-DD yoki DD.MM.YYYY koʻrinishida yuboring (masalan: 2026-06-30).
due-invalid = Sana tushunarsiz. Format: YYYY-MM-DD yoki DD.MM.YYYY.
edit-send-title = Yangi sarlavhani yuboring.
edit-send-desc = Yangi tavsifni yuboring.

# leads & projects
sync-done = Loyihalar sinxronlandi: { $count }.
leads-no-projects = Avval /syncprojects ni bajarib loyihalarni yuklang.
setlead-choose-project = Lider tayinlanadigan loyihani tanlang:
setlead-choose-member = Kim lider boʻlsin?
setlead-ok = { $name } endi "{ $project }" loyihasi lideri.
unsetlead-choose-project = Liderni olib tashlash uchun loyihani tanlang:
unsetlead-ok = { $name } endi "{ $project }" loyihasi lideri emas.
leads-list = Loyiha liderlari:
    { $body }
leads-empty = Hali liderlar tayinlanmagan.

# main menu (buttons)
menu-title = Asosiy menyu — tugmalardan foydalaning 👇
menu-group-hint = Menyu bot bilan shaxsiy chatda mavjud. Men bilan chatni oching va /menu bosing.
menu-my = 📋 Mening vazifalarim
menu-create = ➕ Yaratish
menu-assign = 👥 Biriktirish
menu-search = 🔎 Qidirish
menu-settings = ⚙️ Sozlamalar
menu-help = ❓ Yordam
menu-admin = 🛠 Boshqaruv
menu-projects = 📂 Loyihalar
menu-browse = 🗂 Vazifalar

# browse all tasks
browse-no-projects = Loyihalar hali yuklanmagan. Administratorga murojaat qiling.
browse-choose-project = Vazifalarni koʻrish uchun loyihani tanlang:
browse-empty = Bu loyihada vazifalar yoʻq.
browse-list = Loyiha vazifalari:

# project team management
team-no-projects = Jamoasini boshqarish uchun loyihangiz yoʻq.
team-choose-project = Loyihani tanlang:
team-view = "{ $project }" loyihasi jamoasi:
    { $members }
    Aʼzoni olib tashlash uchun ❌ yoki Qoʻshish bosing.
team-add-btn = ➕ Aʼzo qoʻshish
team-add-choose = Jamoaga kimni qoʻshamiz?
team-back = ⬅️ Orqaga
team-added = Qoʻshildi
team-removed = Olib tashlandi
team-no-candidates = Barcha roʻyxatdan oʻtgan foydalanuvchilar allaqachon jamoada.
team-lead-hint = Bu loyiha lideri. Liderlar 🛠 → Lider tayinlash orqali boshqariladi.

nav-back = ⬅️ Orqaga
nav-close = ✖ Yopish
settings-title = Sozlamalar:
settings-language = 🌐 Til
settings-profile = 👤 Mening profilim

admin-title = Boshqaruv:
admin-connect = 🔗 Linearni ulash
admin-sync = 🔄 Loyihalarni sinxronlash
admin-setlead = 👑 Lider tayinlash
admin-leads = 📜 Liderlar roʻyxati

search-prompt = Qidirish uchun vazifa nomining bir qismini kiriting:
search-empty = Hech narsa topilmadi.
