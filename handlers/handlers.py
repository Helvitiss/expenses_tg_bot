from datetime import datetime

import mysql.connector
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config.config import DB_CONFIG
from keyboards import my_keyboard

router = Router()


# Определение состояний FSM
class AddExpenseState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()

class DeleteExpenseState(StatesGroup):
    waiting_for_expense_id = State()



# Хендлер для главного меню (команды)
@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Выберите команду:", reply_markup=my_keyboard)


# Функция подключения к базе данных
def connect_db():
    return mysql.connector.connect(**DB_CONFIG)


# Хендлер для команды /addexpense — начало процесса
@router.message(F.text == 'Добавить траты')
async def start_add_expense(message: Message, state: FSMContext):
    await message.answer("Введите сумму расхода:")
    await state.set_state(AddExpenseState.waiting_for_amount)


# Хендлер для получения суммы
@router.message(AddExpenseState.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError("Сумма должна быть больше нуля.")
        # Сохраняем сумму в состояние
        await state.update_data(amount=amount)
        await message.answer("Введите категорию расхода:")
        await state.set_state(AddExpenseState.waiting_for_category)
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}. Попробуйте снова.")


# Хендлер для получения категории
@router.message(AddExpenseState.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    category = message.text.strip()
    data = await state.get_data()
    amount = data['amount']
    user_id = message.from_user.id

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Проверяем пользователя
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
        user_db_id = cursor.fetchone()
        if not user_db_id:
            await message.answer("Пожалуйста, начните с команды /start.")
            return
        user_db_id = user_db_id['id']

        # Проверяем категорию
        cursor.execute("SELECT id FROM categories WHERE name = %s AND user_id = %s",
                       (category, user_db_id))
        category_db_id = cursor.fetchone()
        if not category_db_id:
            cursor.execute("INSERT INTO categories (user_id, name) VALUES (%s, %s)",
                           (user_db_id, category))
            conn.commit()
            category_db_id = cursor.lastrowid
        else:
            category_db_id = category_db_id['id']

        # Добавляем запись о транзакции
        cursor.execute("""
            INSERT INTO transactions (user_id, category_id, amount, type, date) 
            VALUES (%s, %s, %s, 'expense', CURDATE())
        """, (user_db_id, category_db_id, amount))
        conn.commit()

        await message.answer(f"Расход добавлен:\nСумма: {amount}\nКатегория: {category}")
    finally:
        cursor.close()
        conn.close()

    # Завершаем состояние
    await state.clear()


# Хендлер для получения трат за определенный период
@router.message(F.text == 'Траты за последний месяц')
async def show_expenses(message: Message):
    try:
        user_id = message.from_user.id

        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        try:
            # Проверяем, зарегистрирован ли пользователь
            cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
            user_db_id = cursor.fetchone()
            if not user_db_id:
                await message.answer("Пожалуйста, начните с команды /start.")
                return
            user_db_id = user_db_id['id']

            # Определяем текущую дату и начало текущего месяца
            today = datetime.now()
            start_of_month = today.replace(day=1).strftime('%Y-%m-%d')

            # Получаем расходы за текущий месяц, сгруппированные по категориям
            cursor.execute("""
                SELECT c.name AS category, SUM(t.amount) AS total 
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s AND t.type = 'expense' AND t.date >= %s
                GROUP BY c.name
                ORDER BY total DESC
            """, (user_db_id, start_of_month))
            expenses = cursor.fetchall()

            # Формируем сообщение для пользователя
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
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


@router.message(F.text == 'Транзакции')
async def show_history(message: Message):
    user_id = message.from_user.id
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # Проверка существования пользователя
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
        user_db_id = cursor.fetchone()
        if not user_db_id:
            await message.answer("Пожалуйста, начните с команды /start.")
            return

        # Получение истории трат
        cursor.execute("""
            SELECT c.name AS category, t.amount, t.date 
            FROM transactions t
            JOIN categories c ON t.category_id = c.id 
            WHERE t.user_id = %s
            ORDER BY t.date DESC
            LIMIT 10
        """, (user_db_id['id'],))

        expenses = cursor.fetchall()
        if expenses:
            message_text = "История трат:\n\n"
            for expense in expenses:
                message_text += f"- {expense['date']} - {expense['category']}: {expense['amount']} руб.\n"
        else:
            message_text = "У вас пока нет записанных трат."

        await message.answer(message_text)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()



# Хендлер для команды /deleteexpense
@router.message(F.text == 'Удалить транзакцию')
async def delete_expense(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # Проверяем существование пользователя
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
        user_db_id = cursor.fetchone()
        if not user_db_id:
            await message.answer("Пожалуйста, начните с команды /start.")
            return

        # Получаем все траты
        cursor.execute("""
            SELECT t.id, c.name AS category, t.amount, t.date 
            FROM transactions t
            JOIN categories c ON t.category_id = c.id 
            WHERE t.user_id = %s
            ORDER BY t.date DESC
        """, (user_db_id['id'],))

        expenses = cursor.fetchall()
        if expenses:
            message_text = "Ваши траты:\n\n"
            for expense in expenses:
                message_text += f"- ID: {expense['id']}, {expense['date']} - {expense['category']}: {expense['amount']} руб.\n"
            message_text += "\nВведите ID трат для удаления:"
            await message.answer(message_text)

            # Устанавливаем состояние для ожидания ввода ID
            await state.set_state(DeleteExpenseState.waiting_for_expense_id)
        else:
            await message.answer("У вас пока нет записанных трат.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Хендлер для получения ID трат и их удаления
@router.message(DeleteExpenseState.waiting_for_expense_id)
async def process_expense_id(message: Message, state: FSMContext):
    expense_id = message.text.strip()
    user_id = message.from_user.id

    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # Проверяем существование пользователя
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
        user_db_id = cursor.fetchone()
        if not user_db_id:
            await message.answer("Пожалуйста, начните с команды /start.")
            return

        # Проверяем существование трат
        cursor.execute("SELECT id FROM transactions WHERE id = %s AND user_id = %s", (expense_id, user_db_id['id']))
        expense_db_id = cursor.fetchone()
        if not expense_db_id:
            await message.answer("Траты с таким ID не найдены.")
            return

        # Удаление трат
        cursor.execute("DELETE FROM transactions WHERE id = %s", (expense_id,))
        conn.commit()

        await message.answer("Траты успешно удалены.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()
    await state.clear()

@router.message()
async def echo(message: Message, state: FSMContext):
    await message.answer(text='Нет такой команды, для доступных комманд откройте клавиатуру')


