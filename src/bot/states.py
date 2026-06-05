from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_lang = State()
    waiting_full_name = State()


class Search(StatesGroup):
    waiting_query = State()


class Profile(StatesGroup):
    waiting_name = State()


class SetLead(StatesGroup):
    waiting_project = State()
    waiting_member = State()


class CreateTask(StatesGroup):
    waiting_project = State()
    waiting_title = State()


class AssignTask(StatesGroup):
    waiting_project = State()
    waiting_assignee = State()
    waiting_title = State()


class CommentTask(StatesGroup):
    waiting_text = State()


class DraftTask(StatesGroup):
    """Draft task creation: collect title + description, then a preview card
    where due/priority/assignee/subscribers are set before publishing. Nothing
    is created in Linear until the user presses Publish — no accidental tasks."""

    waiting_project = State()
    waiting_title = State()
    waiting_desc = State()
    waiting_due = State()
    preview = State()


class Card(StatesGroup):
    """Active task-card editing. The card's issue_id is kept in FSM data
    (`card_issue`) so action callbacks stay within Telegram's 64-byte limit."""

    waiting_title = State()
    waiting_desc = State()
    waiting_comment = State()
    waiting_labels = State()
    waiting_due = State()
