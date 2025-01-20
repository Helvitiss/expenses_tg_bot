from datetime import datetime

import aiomysql
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from database import connect_db, upload_new_expense, get_current_budget, add_income, get_user_categories
from keyboards import main_menu_keyboard, create_category_keyboard
router = Router()


# Определение состояний FSM
class AddExpenseState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_new_category = State()


class DeleteExpenseState(StatesGroup):
    waiting_for_expense_id = State()


class AddIncomeState(StatesGroup):
    waiting_for_amount = State()


# отработка команды старт
@router.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    async with await connect_db() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("INSERT IGNORE INTO users (user_id, username) VALUES (%s, %s)",
                                     (user_id, username))
                await conn.commit()
            await message.answer("Выберите команду:", reply_markup=main_menu_keyboard)
        except Exception as e:
            await message.answer(f"Ошибка при регистрации: {str(e)}")


# Хендлер для команды /addexpense — начало процесса
@router.message(F.text == 'Добавить траты')
async def start_add_expense(message: Message, state: FSMContext):
    user_id = message.from_user.id
    categories = await get_user_categories(user_id)

    if categories:
        await message.answer(
            "Выберите категорию или добавьте новую:",
            reply_markup=create_category_keyboard(categories)
        )
    else:
        await message.answer(
            "У вас пока нет категорий. Пожалуйста, добавьте новую.",
            reply_markup=create_category_keyboard([])
        )
    await state.set_state(AddExpenseState.waiting_for_category)


# Выбор категории при добавлении трат
@router.callback_query(AddExpenseState.waiting_for_category)
async def choose_category(callback: CallbackQuery, state: FSMContext):
    if callback.data == "new_category":
        await callback.message.edit_text(text='Введите новую категорию')
        await state.set_state(AddExpenseState.waiting_for_new_category)
    else:
        category_id = int(callback.data.split('_')[1])
        category_name = callback.data.split('_')[2]
        await state.update_data(category_id=category_id)
        await state.update_data(category_name=category_name)
        await state.set_state(AddExpenseState.waiting_for_amount)

        await callback.message.edit_text(
            "Введите сумму для расходов:",
            reply_markup=None  # Удаление клавиатуры
        )
        await callback.answer()


# добавление новой категории
@router.message(AddExpenseState.waiting_for_new_category)
async def create_new_category(message: Message, state: FSMContext):
    category_name = message.text.strip()
    user_id = message.from_user.id

    async with await connect_db() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO categories (user_id, category_name) VALUES (%s, %s)
                """, (user_id, category_name))
                category_id = cursor.lastrowid
                await conn.commit()
            await state.update_data(category_id=category_id)
            await state.update_data(category_name=category_name)
            await message.answer(f"Категория '{category_name}' успешно добавлена. Введите сумму для расходов:")
            await state.set_state(AddExpenseState.waiting_for_amount)
        except Exception as e:
            await message.answer(f"Ошибка при добавлении категории: {str(e)}")


#  добавление суммы траты
@router.message(AddExpenseState.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        category_name = data['category_name']
        category_id = data.get("category_id")
        amount = float(message.text.strip())
        user_id = message.from_user.id

        expense = {
            'category_id': category_id,
            'amount': amount,
            'expense_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        await upload_new_expense(expense, user_id)

        await message.answer(
            f"""Расход добавлен:\nСумма: {amount}\nКатегория: {category_name}""")
        await state.clear()
    except ValueError:
        await message.answer("Введите корректную сумму.")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


# получения трат за текущий месяц
@router.message(F.text == 'Траты за последний месяц')
async def show_expenses(message: Message):
    try:
        user_id = message.from_user.id
        async with await connect_db() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                user_db_id = await cursor.fetchone()
                if not user_db_id:
                    await message.answer("Пожалуйста, начните с команды /start.")
                    return
                user_db_id = user_db_id['user_id']

                today = datetime.now()
                start_of_month = today.replace(day=1).strftime('%Y-%m-%d')

                await cursor.execute("""
                    SELECT c.category_name AS category, SUM(e.amount) AS total 
                    FROM expenses e
                    JOIN categories c ON e.category_id = c.category_id
                    WHERE e.user_id = %s AND e.expense_date >= %s
                    GROUP BY c.category_name
                    ORDER BY total DESC
                """, (user_db_id, start_of_month))
                expenses = await cursor.fetchall()

                if expenses:
                    message_text = "Ваши расходы за текущий месяц:\n\n"
                    total_sum = 0
                    for expense in expenses:
                        message_text += f"- {expense['category']}: {expense['total']} руб.\n"
                        total_sum += expense['total']
                    message_text += f"\nИтого: {total_sum} руб."
                else:
                    message_text = "У вас нет расходов за текущий месяц."

                await message.answer(message_text)
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


# Хендлер для получения истории транзакций
@router.message(F.text == 'Транзакции')
async def show_history(message: Message):
    user_id = message.from_user.id
    async with await connect_db() as conn:
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT e.expense_id, c.category_name AS category, e.amount, e.expense_date 
                    FROM expenses e
                    JOIN categories c ON e.category_id = c.category_id
                    WHERE e.user_id = %s
                    ORDER BY e.expense_date DESC
                    LIMIT 10
                """, (user_id,))
                expenses = await cursor.fetchall()

            if expenses:
                message_text = "История трат:\n\n"
                for expense in expenses:
                    message_text += f"- {expense['expense_date']} - {expense['category']}: {expense['amount']} руб.\n"
            else:
                message_text = "У вас пока нет записанных трат."

            await message.answer(message_text)
        except Exception as e:
            await message.answer(f"Произошла ошибка: {str(e)}")


# обработка удаления транзакций
@router.message(F.text == 'Удалить транзакцию')
async def delete_expense(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        async with await connect_db() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                user_db_id = await cursor.fetchone()
                if not user_db_id:
                    await message.answer("Пожалуйста, начните с команды /start.")
                    return

                user_db_id = user_db_id['user_id']

                await cursor.execute("""
                    SELECT e.expense_id, c.category_name AS category, e.amount, e.expense_date 
                    FROM expenses e
                    JOIN categories c ON e.category_id = c.category_id 
                    WHERE e.user_id = %s
                    ORDER BY e.expense_date DESC
                """, (user_db_id,))
                expenses = await cursor.fetchall()

                if expenses:
                    message_text = "Ваши траты:\n\n"
                    for expense in expenses:
                        message_text += f"- ID: {expense['expense_id']}, {expense['expense_date']} - {expense['category']}: {expense['amount']} руб.\n"
                    message_text += "\nВведите ID трат для удаления:"
                    await message.answer(message_text)

                    await state.set_state(DeleteExpenseState.waiting_for_expense_id)
                else:
                    await message.answer("У вас пока нет записанных трат.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")


# Хендлер для получения ID трат и их удаления
@router.message(DeleteExpenseState.waiting_for_expense_id)
async def process_expense_id(message: Message, state: FSMContext):
    expense_id = message.text.strip()
    user_id = message.from_user.id

    async with await connect_db() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    DELETE FROM expenses 
                    WHERE expense_id = %s AND user_id = %s
                """, (expense_id, user_id))
                await conn.commit()
                await message.answer("Трата успешно удалена.")
                await state.clear()
        except Exception as e:
            await message.answer(f"Ошибка при удалении: {str(e)}")


# Хендлер для ввода дохода
@router.message(F.text == 'Ввести доход')
async def start_add_income(message: Message, state: FSMContext):
    await message.answer("Введите сумму вашего дохода:")
    await state.set_state(AddIncomeState.waiting_for_amount)


@router.message(AddIncomeState.waiting_for_amount)
async def process_income_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        user_id = message.from_user.id

        await add_income(user_id, amount)

        await message.answer(f"Доход в размере {amount} руб. успешно добавлен.")
        await state.clear()
    except ValueError:
        await message.answer("Введите корректную сумму.")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


# Хендлер для отображения текущего бюджета
@router.message(F.text == 'Текущий бюджет')
async def show_current_budget(message: Message):
    user_id = message.from_user.id
    current_budget = await get_current_budget(user_id)
    await message.answer(f"Ваш текущий бюджет: {current_budget} руб.")


# хендлер для нераспознанных команд
@router.message()
async def echo(message: Message, state: FSMContext):
    await message.answer(text='Нет такой команды, для доступных команд откройте клавиатуру')
