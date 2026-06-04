reg-ask-name = Xush kelibsiz! Ism va familiyangizni kiriting (masalan: Alisher Karimov) — ular vazifalarda koʻrsatiladi.
reg-name-invalid = Iltimos, ism va familiyani boʻsh joy bilan kiriting (masalan: Alisher Karimov).
reg-done = Tayyor, { $name }! Profil saqlandi.
whoami = Siz: { $name }. Rol: { $role }.

start-welcome = Salom, { $name }! Sizning rolingiz: { $role }.
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
toast-saved = Saqlandi
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
