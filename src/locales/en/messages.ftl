reg-ask-name = Welcome! Please enter your first and last name (e.g. John Smith) — it will be shown on tasks.
reg-name-invalid = Please enter both first and last name separated by a space (e.g. John Smith).
reg-done = Done, { $name }! Profile saved.
whoami = You are: { $name }
    { $status }

# status / profile
status-admin = 👑 Admin (full access)
status-lead = ⭐ Lead of: { $projects }
status-member = 👤 Member
profile-card = 👤 Profile
    Name: { $name }
    Status: { $status }
profile-change-name = ✏️ Change name
profile-send-name = Send your new first and last name (e.g. John Smith).
profile-name-updated = Done, name updated: { $name }

start-welcome = Hi, { $name }!
    { $status }
start-choose-lang = Choose your language:
lang-set = Done, language saved.
help-body =
    Commands:
    /task — create a task
    /my — my tasks
    /assign — assign a task (lead/admin)
    /connect — connect Linear (admin)
    /bind — bind this chat (admin)
    /setrole — change a role (admin)
    Your role: { $role }

err-no-permission = You don't have permission for this action.
err-no-workspace = Linear is not connected yet. An admin must run /connect.
err-no-projects = No accessible projects in Linear.
err-unknown-member = User not found in the bot.

task-choose-project = Choose a project:
task-send-title = Send the task text in one message.
task-send-title-seeded = Send the task text (or forward the original message again).
task-created = ✅ Created task { $identifier }: { $url }

assign-choose-member = Assign to whom?
assign-dm-failed = Couldn't DM { $name } — ask them to open the bot via /start.
assigned-dm = 📌 You've been assigned task { $identifier }: { $title } (by { $by })
assign-no-team = This project has no team members yet. Add them via 📂 Projects.
assign-none = ➖ No assignee
assign-not-in-team = This user is not part of the project team.

my-title = My tasks
search-results = Search results
list-count = total: { $n }
list-empty = No tasks for this filter.
list-f-all = All
list-f-todo = Todo
list-f-inprogress = In Progress
list-f-done = Done
list-f-backlog = Backlog
list-prev = ◀
list-next = ▶
list-page = { $page }/{ $total }
my-no-label = Your profile isn't linked yet. Run /start.
my-empty = You have no active tasks.
my-issue-line = { $identifier } · { $title }
    Status: { $state } · Project: { $project }

status-changed = 🔁 { $identifier } → { $state }
comment-prompt = Write your comment:
comment-added = 💬 Comment added.

connect-link = Open the link and authorize the app in Linear:
    { $url }
bind-ok = Chat bound. Linear notifications will be delivered here.
bind-ok-topic = Bound to this topic. The bot will work and post only here.

setrole-usage = Usage: reply to a member's message with /setrole <member|lead|admin>
setrole-ok = { $name }'s role changed to { $role }.

notify-new-task = 🆕 New task { $identifier } · { $title }
notify-comment = 💬 { $user }: { $body }
notify-status = 🔁 { $identifier } → { $state }

# task card
card-not-found = Issue not found.
card-f-status = Status
card-f-priority = Priority
card-f-project = Project
card-f-assignee = Assignee
card-f-due = Due
card-f-estimate = Estimate
card-f-labels = Labels
card-f-subscribers = Subscribers

# card buttons
btn-status = 🔁 Status
btn-edit = ✏️ Edit
btn-assign = 👤 Assign
btn-comment = 💬 Comment
btn-subscribe = 🔔 Subscribe
btn-unsubscribe = 🔕 Unsubscribe
btn-owner = 🔔 Assignee
btn-subscribe-other = 👁 Subscribe user
btn-refresh = 🔄 Refresh
btn-open-linear = ↗️ Open in Linear
btn-title = 📝 Title
btn-desc = 🧾 Description
btn-priority = ⚑ Priority
btn-due = 📅 Due date
btn-estimate = 🔢 Estimate
btn-labels = 🏷 Labels
btn-clear = ✖ Clear
btn-done = ✅ Done
due-today = Today
due-tomorrow = Tomorrow
due-3d = +3 days
due-7d = +7 days
due-custom-btn = 📅 Enter date
sub-owner-locked = You are the assignee of this task — you can't unsubscribe.
sub-on = 🔔 Subscribed
sub-off = 🔕 Unsubscribed
sub-other-done = Subscribed: { $name }
sub-added-dm = 🔔 You were subscribed to task { $identifier } (by { $by })
toast-saved = Saved
due-prompt = Send a date as YYYY-MM-DD or DD.MM.YYYY (e.g. 2026-06-30).
due-invalid = Couldn't parse the date. Use YYYY-MM-DD or DD.MM.YYYY.
edit-send-title = Send the new title.
edit-send-desc = Send the new description.

# leads & projects
sync-done = Projects synced: { $count }.
leads-no-projects = Run /syncprojects first to load projects.
setlead-choose-project = Choose a project to assign a lead to:
setlead-choose-member = Who should be the lead?
setlead-ok = { $name } is now lead of "{ $project }".
unsetlead-choose-project = Choose a project to remove a lead from:
unsetlead-ok = { $name } is no longer lead of "{ $project }".
leads-list = Project leads:
    { $body }
leads-empty = No leads assigned yet.

# main menu (buttons)
menu-title = Main menu — use the buttons 👇
menu-group-hint = The menu lives in the bot DM. Open a chat with me and press /menu.
start-group-hint = In groups use the dashboard: /board. Management and personal actions are in the bot DM.
menu-my = 📋 My tasks
menu-create = ➕ Create
menu-assign = 👥 Assign
menu-search = 🔎 Search
menu-settings = ⚙️ Settings
menu-help = ❓ Help
menu-admin = 🛠 Manage
menu-projects = 📂 My projects
menu-browse = 🗂 Tasks
menu-people = 👥 People

# team dashboard (/board)
board-title = 📊 Team dashboard — choose a section:
board-who = 👥 Who's busy
board-due = 🔥 Deadlines
board-free = 🆓 Unassigned
board-open = 📋 All open
board-empty = Nothing here.
board-more = …and { $n } more. Open the bot DM for the full list.
board-bind-first = This group isn't bound. An admin must run /bind in the desired topic.

# people directory
people-title = Company members ({ $n }):
people-current = Currently in progress:
people-recent = Recently completed:
people-following = Following (not assignee):

# browse all tasks
browse-no-projects = Projects aren't loaded yet. Contact an admin.
browse-choose-project = Choose a project to view its tasks:
browse-empty = This project has no tasks.
browse-list = Project tasks:

# project team management
team-no-projects = You have no projects to manage a team for.
team-choose-project = Choose a project:
team-view = Team of "{ $project }":
    { $members }
team-add-btn = ➕ Add member
team-remove-btn = ➖ Remove member
team-remove-choose = Who to remove from the team?
team-none-removable = No one to remove (only leads remain).
team-add-choose = Who to add to the team?
team-back = ⬅️ Back
team-added = Added
team-removed = Removed
team-no-candidates = All registered users are already on the team.
team-lead-hint = This is a project lead. Manage leads via 🛠 → Assign lead.

nav-back = ⬅️ Back
nav-close = ✖ Close
settings-title = Settings:
settings-language = 🌐 Language
settings-profile = 👤 My profile

admin-title = Management:
admin-connect = 🔗 Connect Linear
admin-sync = 🔄 Sync projects
admin-setlead = 👑 Assign lead
admin-leads = 📜 Leads list
admin-roles = 👑 Roles

roles-choose-user = Whose role to change?
roles-choose-role = { $name }: choose a role
roles-set-member = 👤 Member
roles-set-admin = 👑 Admin
roles-confirm-admin = ⚠️ Make "{ $name }" an admin? They will get full access.
roles-yes = ✅ Yes, grant
roles-no = ❌ Cancel
roles-done = { $name }'s role changed to { $role }.
roles-no-self = You can't change your own role.
roles-bootstrap-locked = This is a permanent admin — role can't be changed.

search-prompt = Type part of an issue title to search:
search-empty = Nothing found.
