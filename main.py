import asyncio
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import *
from dotenv import load_dotenv
from connection import create_table
from service import *

load_dotenv()
token = os.getenv("BOT_TOKEN")

bot = Bot(token)
dp = Dispatcher()

class AddNote(StatesGroup):
    title = State()
    content = State()


class EditNote(StatesGroup):
    content = State()


router = Router()

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/add"),
            KeyboardButton(text="/my_notes"),
        ]
    ],
    resize_keyboard=True,
)


def note_keyboard(note_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Open", callback_data=f"open:{note_id}"),
                InlineKeyboardButton(text="Update", callback_data=f"update:{note_id}"),
                InlineKeyboardButton(text="Delete", callback_data=f"delete:{note_id}"),
            ]
        ]
    )


@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Hello! I am your notes bot.", reply_markup=keyboard)


@router.message(Command("help"))
async def help(message: Message):
    await message.answer(
        "/start - Start bot\n"
        "/add - Add note\n"
        "/notes - Show notes",
        reply_markup=keyboard,
    )


@router.message(Command("add"))
async def add(message: Message, state: FSMContext):
    await state.set_state(AddNote.title)
    await message.answer("Enter note title:")


@router.message(AddNote.title)
async def title(message: Message, state: FSMContext):
    title = (message.text or "").strip()

    if not title:
        await message.answer("Title cannot be empty.")
        return

    if len(title) > 150:
        await message.answer("Title must be under 150 characters.")
        return

    await state.update_data(title=title)
    await state.set_state(AddNote.content)
    await message.answer("Enter note content:")


@router.message(AddNote.content)
async def content(message: Message, state: FSMContext):
    content = (message.text or "").strip()

    if not content:
        await message.answer("Content cannot be empty.")
        return

    data = await state.get_data()

    result = await add_note(
        message.from_user.id,
        message.from_user.username,
        data["title"],
        content,
    )

    await state.clear()

    if result:
        await message.answer("Note added successfully!", reply_markup=keyboard)
    else:
        await message.answer("Failed to add note.", reply_markup=keyboard)


@router.message(Command("notes"))
@router.message(Command("my_notes"))
async def notes(message: Message):
    notes = await show_notes(message.from_user.id)

    if not notes:
        await message.answer("You don't have any notes.", reply_markup=keyboard)
        return

    for note in notes:
        await message.answer(
            f"#{note['id']} {note['title']}",
            reply_markup=note_keyboard(note["id"]),
        )


@router.callback_query(F.data.startswith("open:"))
async def open_note(callback):
    note_id = int(callback.data.split(":")[1])
    note = await get_note(note_id, callback.from_user.id)

    if not note:
        await callback.answer("Note not found.", show_alert=True)
        return

    await callback.message.answer(
        f"Title: {note['title']}\n\n{note['content']}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("Update:"))
async def update(callback, state: FSMContext):
    note_id = int(callback.data.split(":")[1])
    note = await get_note(note_id, callback.from_user.id)

    if not note:
        await callback.answer("Note not found.", show_alert=True)
        return

    await state.update_data(note_id=note_id)
    await state.set_state(EditNote.content)
    await callback.message.answer("Enter new content:")
    await callback.answer()


@router.message(EditNote.content)
async def edit_content(message: Message, state: FSMContext):
    content = (message.text or "").strip()

    if not content:
        await message.answer("Content cannot be empty.")
        return

    data = await state.get_data()

    if await edit_note(data["note_id"], message.from_user.id, content):
        await message.answer("Note updated!", reply_markup=keyboard)
    else:
        await message.answer("Failed to update note.", reply_markup=keyboard)

    await state.clear()


@router.callback_query(F.data.startswith("delete:"))
async def delete(callback):
    note_id = int(callback.data.split(":")[1])

    if await delete_note(note_id, callback.from_user.id):
        await callback.message.edit_text("Note deleted.")
        await callback.answer()
    else:
        await callback.answer("Failed to delete note.", show_alert=True)


async def main():
    await create_table()
    dp.include_router(router)
    await dp.start_polling(bot)
    print("Bot started!")


if __name__ == "__main__":
    asyncio.run(main())