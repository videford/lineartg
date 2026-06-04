reg-ask-name = Welcome! Please enter your first and last name (e.g. John Smith) — it will be shown on tasks.
reg-name-invalid = Please enter both first and last name separated by a space (e.g. John Smith).
reg-done = Done, { $name }! Profile saved.
whoami = You are: { $name }. Role: { $role }.

start-welcome = Hi, { $name }! Your role: { $role }.
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

setrole-usage = Usage: reply to a member's message with /setrole <member|lead|admin>
setrole-ok = { $name }'s role changed to { $role }.

notify-comment = 💬 { $user }: { $body }
notify-status = 🔁 { $identifier } → { $state }

# task card
card-not-found = Issue not found.
toast-saved = Saved
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
menu-my = 📋 My tasks
menu-create = ➕ Create
menu-assign = 👥 Assign
menu-search = 🔎 Search
menu-settings = ⚙️ Settings
menu-help = ❓ Help
menu-admin = 🛠 Manage

settings-title = Settings:
settings-language = 🌐 Language
settings-profile = 👤 My profile

admin-title = Management:
admin-connect = 🔗 Connect Linear
admin-sync = 🔄 Sync projects
admin-setlead = 👑 Assign lead
admin-leads = 📜 Leads list

search-prompt = Type part of an issue title to search:
search-empty = Nothing found.
