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
assign-not-in-team = This user is not part of the project team.

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
sub-on = 🔔 Subscribed
sub-off = 🔕 Unsubscribed
sub-other-done = Subscribed: { $name }
sub-added-dm = 🔔 You were subscribed to task { $identifier } (by { $by })
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
menu-projects = 📂 Projects

# project team management
team-no-projects = You have no projects to manage a team for.
team-choose-project = Choose a project:
team-view = Team of "{ $project }":
    { $members }
    Tap ❌ to remove a member, or Add.
team-add-btn = ➕ Add member
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

search-prompt = Type part of an issue title to search:
search-empty = Nothing found.
