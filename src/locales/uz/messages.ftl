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

draft-title = 🆕 Vazifa qoralamasi
draft-send-title = Vazifa nomini bitta xabarda yuboring.
draft-send-desc = Tavsif yuboring (yoki «Oʻtkazib yuborish» tugmasini bosing).
draft-desc-skip = ⏭ Oʻtkazib yuborish
draft-f-title = Nomi
draft-f-desc = Tavsif
draft-btn-assignee = 👤 Ijrochi
draft-btn-sub = 🔔 Obuna qilish
draft-btn-publish = ✅ Eʼlon qilish
draft-btn-cancel = ❌ Bekor qilish
draft-hint = Maydonlarni tekshiring va «Eʼlon qilish» tugmasini bosing.
draft-canceled = Vazifa yaratish bekor qilindi.

assign-choose-member = Kimga biriktirilsin?
assign-dm-failed = { $name }ga shaxsiy xabar yuborilmadi — u /start orqali botni ochsin.
assigned-dm = 📌 Sizga vazifa biriktirildi { $identifier }: { $title } (biriktirdi: { $by })
assign-no-team = Bu loyihada hali aʼzolar yoʻq. Ularni 📂 Loyihalar orqali qoʻshing.
assign-none = ➖ Ijrochisiz
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
bind-ok-topic = Shu mavzuga bogʻlandi. Bot faqat shu yerda ishlaydi va xabar yuboradi.

setrole-usage = Foydalanish: aʼzo xabariga javoban /setrole <member|lead|admin>
setrole-ok = { $name } roli { $role } ga oʻzgartirildi.

notify-new-task = 🆕 Yangi vazifa { $identifier } · { $title }
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
card-f-subscribers = Obunachilar

# card buttons
btn-status = 🔁 Holat
btn-edit = ✏️ Tahrirlash
btn-assign = 👤 Biriktirish
btn-comment = 💬 Izoh
btn-subscribe = 🔔 Obuna
btn-unsubscribe = 🔕 Obunani bekor qilish
btn-owner = 🔔 Ijrochi
btn-subscribe-other = 👁 Obuna qilish
btn-refresh = 🔄 Yangilash
btn-open-linear = ↗️ Linearda ochish
btn-title = 📝 Sarlavha
btn-desc = 🧾 Tavsif
btn-priority = ⚑ Muhimlik
btn-due = 📅 Muddat
btn-estimate = 🔢 Baho
btn-labels = 🏷 Teglar
btn-clear = ✖ Olib tashlash
btn-done = ✅ Tayyor
due-today = Bugun
due-tomorrow = Ertaga
due-3d = +3 kun
due-7d = +7 kun
due-custom-btn = 📅 Sana kiritish
sub-owner-locked = Siz bu vazifaning ijrochisisiz — obunani bekor qila olmaysiz.
sub-on = 🔔 Obuna boʻldingiz
sub-off = 🔕 Obuna bekor qilindi
sub-other-done = Obuna qilindi: { $name }
sub-added-dm = 🔔 Sizni { $identifier } vazifasiga obuna qilishdi (kim: { $by })
toast-saved = Saqlandi
due-prompt = Sanani DD.MM.YYYY koʻrinishida yuboring (masalan: 30.06.2026).
due-invalid = Sana tushunarsiz. Format: DD.MM.YYYY (masalan: 30.06.2026).
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
start-group-hint = Guruhda dashboard mavjud: /board. Boshqaruv va shaxsiy amallar — bot bilan shaxsiy chatda.
menu-my = 📋 Mening vazifalarim
menu-create = ➕ Yaratish
menu-assign = 👥 Biriktirish
menu-search = 🔎 Qidirish
menu-settings = ⚙️ Sozlamalar
menu-help = ❓ Yordam
menu-admin = 🛠 Boshqaruv
menu-projects = 📂 Mening loyihalarim
menu-browse = 🗂 Vazifalar
menu-people = 👥 Aʼzolar

# team dashboard (/board)
board-title = 📊 Jamoa paneli — boʻlimni tanlang:
board-who = 👥 Kim band
board-due = 🔥 Muddatlar
board-free = 🆓 Ijrochisiz
board-open = 📋 Barcha ochiq
board-empty = Hech narsa yoʻq.
board-more = …va yana { $n } ta. Toʻliq roʻyxat uchun botni shaxsiy chatda oching.
board-bind-first = Bu guruh bogʻlanmagan. Admin kerakli mavzuda /bind bajarishi kerak.

# people directory
people-title = Kompaniya aʼzolari ({ $n }):
people-current = Hozir jarayonda:
people-recent = Yaqinda yakunlangan:
people-following = Obuna:
people-linear-unavailable = ⚠️ Linear ma'lumotlari mavjud emas (/connect orqali qayta ulang).

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
team-add-btn = ➕ Aʼzo qoʻshish
team-remove-btn = ➖ Aʼzoni olib tashlash
team-remove-choose = Jamoadan kimni olib tashlaymiz?
team-none-removable = Olib tashlash uchun hech kim yoʻq (faqat liderlar qoldi).
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
admin-roles = 👑 Rollar
admin-groups = 🔔 Guruh eʼlonlari
admin-remove-user = 🗑 Foydalanuvchini oʻchirish

rmuser-choose = Botdan kimni oʻchiramiz?
rmuser-confirm = { $name } botdan oʻchirilsinmi? Uning rollari, loyihalardagi aʼzoligi va obunalari oʻchiriladi. Bu amalni ortga qaytarib boʻlmaydi.
rmuser-yes = 🗑 Oʻchirish
rmuser-done = 🗑 { $name } botdan oʻchirildi.

groups-title = Guruhlar (bot xabarlarini yoqish/oʻchirish uchun bosing):
groups-empty = Hali bogʻlangan guruhlar yoʻq. Guruhda /bind orqali bogʻlang.
groups-on = 🔔 Eʼlonlar yoqildi
groups-off = 🔕 Eʼlonlar oʻchirildi

roles-choose-user = Kimning rolini oʻzgartiramiz?
roles-choose-role = { $name }: rolni tanlang
roles-set-member = 👤 Aʼzo
roles-set-admin = 👑 Administrator
roles-confirm-admin = ⚠️ «{ $name }»ni administrator qilamizmi? Unga toʻliq huquq beriladi.
roles-yes = ✅ Ha, tayinlash
roles-no = ❌ Bekor qilish
roles-done = { $name } roli { $role } ga oʻzgartirildi.
roles-no-self = Oʻz rolingizni oʻzgartira olmaysiz.
roles-bootstrap-locked = Bu doimiy administrator — roli oʻzgartirilmaydi.

search-prompt = Qidirish uchun vazifa nomining bir qismini kiriting:
search-empty = Hech narsa topilmadi.
