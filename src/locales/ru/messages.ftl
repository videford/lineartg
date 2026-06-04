reg-ask-name = Добро пожаловать! Введите ваши имя и фамилию (например: Иван Петров) — они будут отображаться в задачах.
reg-name-invalid = Пожалуйста, введите имя и фамилию через пробел (например: Иван Петров).
reg-done = Готово, { $name }! Профиль сохранён.
whoami = Вы: { $name }. Роль: { $role }.

start-welcome = Привет, { $name }! Ваша роль: { $role }.
start-choose-lang = Выберите язык интерфейса:
lang-set = Готово, язык сохранён.
help-body =
    Команды:
    /task — создать задачу
    /my — мои задачи
    /assign — назначить задачу (lead/admin)
    /connect — подключить Linear (admin)
    /bind — привязать этот чат (admin)
    /setrole — изменить роль (admin)
    Ваша роль: { $role }

err-no-permission = Недостаточно прав для этого действия.
err-no-workspace = Linear ещё не подключён. Администратор должен выполнить /connect.
err-no-projects = В Linear нет доступных проектов.
err-unknown-member = Пользователь не найден в боте.

task-choose-project = Выберите проект:
task-send-title = Отправьте текст задачи одним сообщением.
task-send-title-seeded = Отправьте текст задачи (или перешлите исходное сообщение ещё раз).
task-created = ✅ Создана задача { $identifier }: { $url }

assign-choose-member = Кому назначить?
assign-dm-failed = Не удалось отправить ЛС пользователю { $name } — пусть откроет бота через /start.
assigned-dm = 📌 Вам назначена задача { $identifier }: { $title } (назначил: { $by })

my-no-label = Ваш профиль ещё не привязан. Выполните /start.
my-empty = У вас нет активных задач.
my-issue-line = { $identifier } · { $title }
    Статус: { $state } · Проект: { $project }

status-changed = 🔁 { $identifier } → { $state }
comment-prompt = Напишите текст комментария:
comment-added = 💬 Комментарий добавлен.

connect-link = Откройте ссылку и авторизуйте приложение в Linear:
    { $url }
bind-ok = Чат привязан. Уведомления Linear будут приходить сюда.

setrole-usage = Использование: ответьте на сообщение участника командой /setrole <member|lead|admin>
setrole-ok = Роль пользователя { $name } изменена на { $role }.

notify-comment = 💬 { $user }: { $body }
notify-status = 🔁 { $identifier } → { $state }

# task card
card-not-found = Задача не найдена.
toast-saved = Сохранено
edit-send-title = Отправьте новый заголовок.
edit-send-desc = Отправьте новое описание.

# leads & projects
sync-done = Синхронизировано проектов: { $count }.
leads-no-projects = Сначала выполните /syncprojects, чтобы подтянуть проекты.
setlead-choose-project = Выберите проект, на который назначить лида:
setlead-choose-member = Кого назначить лидом?
setlead-ok = { $name } назначен(а) лидом проекта «{ $project }».
unsetlead-choose-project = Выберите проект, с которого снять лида:
unsetlead-ok = { $name } больше не лид проекта «{ $project }».
leads-list = Лиды по проектам:
    { $body }
leads-empty = Лиды ещё не назначены.

# main menu (buttons)
menu-title = Главное меню — выбирайте кнопками 👇
menu-group-hint = Меню доступно в личке с ботом. Откройте чат со мной и нажмите /menu.
menu-my = 📋 Мои задачи
menu-create = ➕ Создать
menu-assign = 👥 Назначить
menu-search = 🔎 Поиск
menu-settings = ⚙️ Настройки
menu-help = ❓ Помощь
menu-admin = 🛠 Управление

settings-title = Настройки:
settings-language = 🌐 Язык
settings-profile = 👤 Мой профиль

admin-title = Управление:
admin-connect = 🔗 Подключить Linear
admin-sync = 🔄 Синхронизировать проекты
admin-setlead = 👑 Назначить лида
admin-leads = 📜 Список лидов

search-prompt = Введите часть названия задачи для поиска:
search-empty = Ничего не найдено.
