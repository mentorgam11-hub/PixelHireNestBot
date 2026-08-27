import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Set BOT_TOKEN environment variable before starting the bot.")

bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Vacancy(StatesGroup):
    title = State()
    category = State()
    description = State()
    requirements = State()
    salary = State()
    employment = State()
    timezone = State()
    contact = State()
    confirm = State()

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Создать вакансию", callback_data="create")
    kb.button(text="🔎 Найти вакансию", callback_data="search")
    kb.button(text="📋 Мои вакансии", callback_data="mine")
    kb.button(text="⭐ Избранное", callback_data="favorites")
    kb.button(text="👤 Профиль", callback_data="profile")
    kb.adjust(1)
    return kb.as_markup()

def categories():
    kb = InlineKeyboardBuilder()
    for x in ["UI/UX", "Графический дизайн", "Web-дизайн", "3D", "Motion", "Иллюстрация", "Другое"]:
        kb.button(text=x, callback_data=f"cat:{x}")
    kb.adjust(2)
    return kb.as_markup()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🎨 <b>PixelHireNest</b>\n\n"
        "Удалённые вакансии для дизайнеров.\n"
        "Создавай вакансии, находи работу и сохраняй интересные предложения.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Создание вакансии отменено.", reply_markup=main_menu())

@dp.callback_query(F.data == "create")
async def create(call: CallbackQuery, state: FSMContext):
    await state.set_state(Vacancy.title)
    await call.message.answer("📝 Введи название вакансии.\nНапример: <b>UI/UX Designer</b>", parse_mode="HTML")
    await call.answer()

@dp.message(Vacancy.title)
async def title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(Vacancy.category)
    await message.answer("🎨 Выбери направление:", reply_markup=categories())

@dp.callback_query(Vacancy.category, F.data.startswith("cat:"))
async def category(call: CallbackQuery, state: FSMContext):
    await state.update_data(category=call.data[4:])
    await state.set_state(Vacancy.description)
    await call.message.answer("📄 Опиши работу: задачи, компанию и чем предстоит заниматься.")
    await call.answer()

@dp.message(Vacancy.description)
async def description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(Vacancy.requirements)
    await message.answer("✅ Напиши требования к кандидату.")

@dp.message(Vacancy.requirements)
async def requirements(message: Message, state: FSMContext):
    await state.update_data(requirements=message.text)
    await state.set_state(Vacancy.salary)
    await message.answer("💰 Укажи зарплату.\nНапример: $1000–1500 в месяц или «по договорённости».")

@dp.message(Vacancy.salary)
async def salary(message: Message, state: FSMContext):
    await state.update_data(salary=message.text)
    await state.set_state(Vacancy.employment)
    kb = InlineKeyboardBuilder()
    for x in ["Full-time", "Part-time", "Проектная", "Стажировка"]:
        kb.button(text=x, callback_data=f"emp:{x}")
    kb.adjust(2)
    await message.answer("⏰ Тип занятости:", reply_markup=kb.as_markup())

@dp.callback_query(Vacancy.employment, F.data.startswith("emp:"))
async def employment(call: CallbackQuery, state: FSMContext):
    await state.update_data(employment=call.data[4:])
    await state.set_state(Vacancy.timezone)
    await call.message.answer("🌍 Укажи часовой пояс или напиши «любой».\nНапример: UTC+3")
    await call.answer()

@dp.message(Vacancy.timezone)
async def timezone(message: Message, state: FSMContext):
    await state.update_data(timezone=message.text)
    await state.set_state(Vacancy.contact)
    await message.answer("📩 Укажи контакт для отклика: @username, email или ссылку.")

@dp.message(Vacancy.contact)
async def contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    text = (
        f"🎨 <b>{data['title']}</b>\n"
        f"🏷 Направление: {data['category']}\n"
        f"🌍 Удалённо\n"
        f"💰 Зарплата: {data['salary']}\n"
        f"⏰ {data['employment']}\n"
        f"🕐 Часовой пояс: {data['timezone']}\n\n"
        f"<b>Описание</b>\n{data['description']}\n\n"
        f"<b>Требования</b>\n{data['requirements']}\n\n"
        f"📩 Контакт: {data['contact']}"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Опубликовать", callback_data="publish")
    kb.button(text="❌ Отменить", callback_data="abort")
    kb.adjust(2)
    await state.set_state(Vacancy.confirm)
    await message.answer("👀 <b>Предпросмотр вакансии:</b>\n\n" + text, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(Vacancy.confirm, F.data == "publish")
async def publish(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # MVP: сохраняем опубликованные вакансии в памяти процесса.
    published.append({
        "user_id": call.from_user.id,
        **data
    })
    await state.clear()
    await call.message.answer(
        "🎉 Вакансия создана!\n\n"
        "Сейчас она сохранена в боте. В следующей версии можно подключить "
        "базу данных и автоматическую публикацию в канал.",
        reply_markup=main_menu()
    )
    await call.answer()

@dp.callback_query(Vacancy.confirm, F.data == "abort")
async def abort(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Вакансия не опубликована.", reply_markup=main_menu())
    await call.answer()

published = []

@dp.callback_query(F.data == "mine")
async def mine(call: CallbackQuery):
    mine = [x for x in published if x["user_id"] == call.from_user.id]
    if not mine:
        await call.message.answer("📋 У тебя пока нет созданных вакансий.")
    else:
        await call.message.answer(f"📋 У тебя опубликовано вакансий: {len(mine)}")
    await call.answer()

@dp.callback_query(F.data == "search")
async def search(call: CallbackQuery):
    if not published:
        await call.message.answer("🔎 Пока опубликованных вакансий нет.")
    else:
        for x in published[-10:]:
            await call.message.answer(
                f"🎨 <b>{x['title']}</b>\n"
                f"🏷 {x['category']}\n"
                f"💰 {x['salary']}\n"
                f"⏰ {x['employment']}\n\n"
                f"{x['description']}\n\n"
                f"📩 {x['contact']}",
                parse_mode="HTML"
            )
    await call.answer()

@dp.callback_query(F.data.in_({"favorites", "profile"}))
async def simple(call: CallbackQuery):
    text = "⭐ Избранное пока пусто." if call.data == "favorites" else "👤 Профиль будет расширен в следующей версии."
    await call.message.answer(text)
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
