reg-ask-name = Добро пожаловать! Введите ваши имя и фамилию (например: Иван Петров) — они будут отображаться в задачах.
reg-name-invalid = Пожалуйста, введите имя и фамилию через пробел (например: Иван Петров).
reg-done = Готово, { $name }! Профиль сохранён.
whoami = Вы: { $name }
    { $status }

# status / profile
status-admin = 👑 Администратор (полный доступ)
status-lead = ⭐ Лид проектов: { $projects }
status-member = 👤 Участник
profile-card = 👤 Профиль
    Имя: { $name }
    Статус: { $status }
profile-change-name = ✏️ Изменить имя
profile-send-name = Отправьте новое имя и фамилию (например: Иван Петров).
profile-name-updated = Готово, имя обновлено: { $name }

start-welcome = Привет, { $name }!
    { $status }
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

draft-title = 🆕 Черновик задачи
draft-send-title = Напишите название задачи одним сообщением.
draft-send-desc = Напишите описание задачи (или нажмите «Пропустить»).
draft-desc-skip = ⏭ Пропустить
draft-f-title = Название
draft-f-desc = Описание
draft-btn-assignee = 👤 Исполнитель
draft-btn-sub = 🔔 Подписать
draft-btn-publish = ✅ Опубликовать
draft-btn-cancel = ❌ Отмена
draft-hint = Проверьте поля и нажмите «Опубликовать».
draft-canceled = Создание задачи отменено.

assign-choose-member = Кому назначить?
assign-dm-failed = Не удалось отправить ЛС пользователю { $name } — пусть откроет бота через /start.
assigned-dm = 📌 Вам назначена задача { $identifier }: { $title } (назначил: { $by })
assign-no-team = В этом проекте пока нет участников. Добавьте их через 📂 Проекты.
assign-none = ➖ Без исполнителя
assign-not-in-team = Этот пользователь не входит в команду проекта.

my-title = Мои задачи
search-results = Результаты поиска
list-count = всего: { $n }
list-empty = Нет задач по этому фильтру.
list-f-all = Все
list-f-todo = К выполнению
list-f-inprogress = В работе
list-f-done = Готово
list-f-backlog = Бэклог
list-prev = ◀
list-next = ▶
list-page = { $page }/{ $total }
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
bind-ok-topic = Привязано к этому топику. Бот будет работать и слать уведомления только здесь.

setrole-usage = Использование: ответьте на сообщение участника командой /setrole <member|lead|admin>
setrole-ok = Роль пользователя { $name } изменена на { $role }.

notify-new-task = 🆕 Новая задача { $identifier } · { $title }
notify-comment = 💬 { $user }: { $body }
notify-status = 🔁 { $identifier } → { $state }

# task card
card-not-found = Задача не найдена.
card-f-status = Статус
card-f-priority = Приоритет
card-f-project = Проект
card-f-assignee = Исполнитель
card-f-due = Дедлайн
card-f-estimate = Оценка
card-f-labels = Метки
card-f-subscribers = Подписчики

# card buttons
btn-status = 🔁 Статус
btn-edit = ✏️ Изменить
btn-assign = 👤 Назначить
btn-comment = 💬 Комментарий
btn-subscribe = 🔔 Подписаться
btn-unsubscribe = 🔕 Отписаться
btn-owner = 🔔 Исполнитель
btn-subscribe-other = 👁 Подписать
btn-refresh = 🔄 Обновить
btn-open-linear = ↗️ В Linear
btn-title = 📝 Заголовок
btn-desc = 🧾 Описание
btn-priority = ⚑ Приоритет
btn-due = 📅 Дедлайн
btn-estimate = 🔢 Оценка
btn-labels = 🏷 Метки
btn-clear = ✖ Снять
btn-done = ✅ Готово
due-today = Сегодня
due-tomorrow = Завтра
due-3d = +3 дня
due-7d = +7 дней
due-custom-btn = 📅 Ввести дату
sub-owner-locked = Вы исполнитель этой задачи — отписаться нельзя.
sub-on = 🔔 Вы подписаны
sub-off = 🔕 Подписка отменена
sub-other-done = Подписан: { $name }
sub-added-dm = 🔔 Вас подписали на задачу { $identifier } (подписал: { $by })
toast-saved = Сохранено
due-prompt = Отправьте дату в формате ГГГГ-ММ-ДД или ДД.ММ.ГГГГ (например: 2026-06-30).
due-invalid = Не понял дату. Формат: ГГГГ-ММ-ДД или ДД.ММ.ГГГГ.
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
start-group-hint = В группе доступен дашборд: /board. Управление и личные действия — в личном чате со мной.
menu-my = 📋 Мои задачи
menu-create = ➕ Создать
menu-assign = 👥 Назначить
menu-search = 🔎 Поиск
menu-settings = ⚙️ Настройки
menu-help = ❓ Помощь
menu-admin = 🛠 Управление
menu-projects = 📂 Мои проекты
menu-browse = 🗂 Задачи
menu-people = 👥 Участники

# team dashboard (/board)
board-title = 📊 Дашборд команды — выберите раздел:
board-who = 👥 Кто чем занят
board-due = 🔥 Дедлайны
board-free = 🆓 Без исполнителя
board-open = 📋 Все открытые
board-empty = Ничего нет.
board-more = …и ещё { $n }. Откройте бот в личке для полного списка.
board-bind-first = Эта группа не привязана. Админу нужно выполнить /bind в нужном топике.

# people directory
people-title = Участники компании ({ $n }):
people-current = Сейчас в работе:
people-recent = Недавно завершено:
people-following = Подписан:
people-linear-unavailable = ⚠️ Данные Linear недоступны (нужно переподключить через /connect).

# browse all tasks
browse-no-projects = Проекты ещё не загружены. Обратитесь к администратору.
browse-choose-project = Выберите проект, чтобы посмотреть задачи:
browse-empty = В этом проекте нет задач.
browse-list = Задачи проекта:

# project team management
team-no-projects = У вас нет проектов для управления командой.
team-choose-project = Выберите проект:
team-view = Команда проекта «{ $project }»:
    { $members }
team-add-btn = ➕ Добавить участника
team-remove-btn = ➖ Удалить участника
team-remove-choose = Кого убрать из команды?
team-none-removable = Некого убирать (остались только лиды).
team-add-choose = Кого добавить в команду?
team-back = ⬅️ Назад
team-added = Добавлен
team-removed = Убран
team-no-candidates = Все зарегистрированные пользователи уже в команде.
team-lead-hint = Это лид проекта. Лидов меняют через 🛠 → Назначить лида.

nav-back = ⬅️ Назад
nav-close = ✖ Закрыть
settings-title = Настройки:
settings-language = 🌐 Язык
settings-profile = 👤 Мой профиль

admin-title = Управление:
admin-connect = 🔗 Подключить Linear
admin-sync = 🔄 Синхронизировать проекты
admin-setlead = 👑 Назначить лида
admin-leads = 📜 Список лидов
admin-roles = 👑 Роли
admin-groups = 🔔 Объявления в группах

groups-title = Группы (нажмите, чтобы включить/выключить сообщения бота):
groups-empty = Пока нет привязанных групп. Привяжите через /bind в группе.
groups-on = 🔔 Объявления включены
groups-off = 🔕 Объявления выключены

roles-choose-user = Кому изменить роль?
roles-choose-role = { $name }: выберите роль
roles-set-member = 👤 Участник
roles-set-admin = 👑 Администратор
roles-confirm-admin = ⚠️ Точно назначить «{ $name }» администратором? У него будет полный доступ.
roles-yes = ✅ Да, назначить
roles-no = ❌ Отмена
roles-done = Роль «{ $name }» изменена на { $role }.
roles-no-self = Свою роль изменить нельзя.
roles-bootstrap-locked = Это постоянный администратор — роль менять нельзя.

search-prompt = Введите часть названия задачи для поиска:
search-empty = Ничего не найдено.
