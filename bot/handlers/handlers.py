from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from datetime import datetime
from decimal import Decimal
from bot.keyboards.inline import operation_type_keyboard, currency_keyboard, operation_choice_keyboard
from bot.client.client import rate_get
from bot.states.states import Reg, NewOperation
from bot.database.tables import conn

router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Салют! Используй команду /reg, чтобы использовать функционал бота.")


@router.message(Command("reg"))
async def registration_command(message: Message, state: FSMContext):
    user_id = message.chat.id
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE chat_id = %s", (user_id,))
        user_exists = cur.fetchone()
    if user_exists:
        await message.answer("Вы уже зарегистрированы!")
    else:
        await message.answer("Введите ваш логин:")
        await state.set_state(Reg.name)


@router.message(Reg.name)
async def process_registration(message: Message, state: FSMContext):
    name = message.text
    user_id = message.chat.id
    if len(name) > 50:
        await message.answer("Логин не может превышать 50 символов! Придумайте новый!")
    else:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (chat_id, name) VALUES (%s, %s)", (user_id, name))
            conn.commit()
        await message.answer(f"Вы успешно зарегистрированы. Ваш логин: {name}")
        await state.clear()


@router.message(Command("add_operation"))
async def add_operation_command(message: Message):
    user_id = message.chat.id
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE chat_id = %s", (user_id,))
        user_exists = cur.fetchone()
    if not user_exists:
        await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь с помощью команды /reg.")
    else:
        await message.answer("Выберите тип операции:", reply_markup=operation_type_keyboard)


@router.callback_query(F.data.startswith("type:"))
async def process_operation_type(callback: CallbackQuery, state: FSMContext):
    operation_type = callback.data.split(":")[1]
    await state.update_data(type=operation_type)
    await callback.message.answer("Введите сумму операции в рублях:")
    await state.set_state(NewOperation.amount)
    await callback.answer()


@router.message(NewOperation.amount)
async def process_operation_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        await state.update_data(amount=amount)
        await message.answer("Введите дату операции в формате ДД.ММ.ГГГГ:")
        await state.set_state(NewOperation.date)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму в рублях.")


@router.message(NewOperation.date)
async def process_operation_date(message: Message, state: FSMContext):
    try:
        operation_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        data = await state.get_data()
        operation_type = data["type"]
        amount = data["amount"]
        user_id = message.chat.id
        with conn.cursor() as cur:
            cur.execute("INSERT INTO operations (date, sum, chat_id, type_operation) VALUES (%s, %s, %s, %s)",
                        (operation_date, amount, user_id, operation_type))
            conn.commit()
        await message.answer("Операция успешно добавлена!")
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.")


@router.message(Command("operations"))
async def operations_command(message: Message):
    user_id = message.chat.id
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE chat_id = %s", (user_id,))
        user_exists = cur.fetchone()
    if not user_exists:
        await message.answer("Вы не зарегистрированы. Пожалуйста, зарегистрируйтесь с помощью команды /reg.")
    else:
        await message.answer("Выберите валюту для просмотра операций:", reply_markup=currency_keyboard)


@router.callback_query(F.data.startswith("currency:"))
async def process_currency(callback: CallbackQuery):
    currency = callback.data.split(":")[1]
    if currency in ["EUR", "USD"]:
        rate = await rate_get(currency)
        if rate is None:
            await callback.message.answer("Произошла ошибка при получении курса валюты. Попробуйте еще раз позже.")
            await callback.answer()
            return
    else:
        rate = Decimal(1)
    await callback.message.answer("Выберите тип операций для вывода:",
                                  reply_markup=operation_choice_keyboard(rate, currency))
    await callback.answer()


@router.callback_query(F.data.startswith("choice:"))
async def process_choice(callback: CallbackQuery):
    choice, rate, currency = callback.data.split(":")[1:]
    rate = Decimal(rate)
    user_id = callback.message.chat.id
    with conn.cursor() as cur:
        if choice == "expense":
            cur.execute("SELECT * FROM operations WHERE chat_id = %s AND type_operation = 'РАСХОД'", (user_id,))
        elif choice == "income":
            cur.execute("SELECT * FROM operations WHERE chat_id = %s AND type_operation = 'ДОХОД'", (user_id,))
        else:
            cur.execute("SELECT * FROM operations WHERE chat_id = %s", (user_id,))
        operations = cur.fetchall()
    if not operations:
        await callback.message.answer("У вас пока нет операций выбранного типа.")
    else:
        operations_text = "Ваши операции:\n"
        for operation in operations:
            operation_date = operation[1].strftime("%d.%m.%Y")
            amount = operation[2] / rate
            amount = round(amount, 2)
            operation_type = operation[4]
            operations_text += f"{operation_date} - {amount} {currency} ({operation_type})\n"
        await callback.message.answer(operations_text)
    await callback.answer()
