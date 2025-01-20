import aiomysql
from config.config import DB_CONFIG
# Функция для подключения к БД
async def connect_db():
    # Асинхронное подключение к базе данных
    return await aiomysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        db=DB_CONFIG['database']
    )

# Функция для получения категорий пользователя
async def get_user_categories(user_id):
    async with await connect_db() as conn:
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT category_id, category_name 
                    FROM categories 
                    WHERE user_id = %s
                """, (user_id,))

                return await cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении категорий: {e}")
            return []

# Функция для добавления нового расхода
async def upload_new_expense(expense, user_id):
    async with await connect_db() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO expenses 
                    (user_id, category_id, amount, expense_date) 
                    VALUES (%s, %s, %s, %s)
                """, (user_id, expense['category_id'], expense['amount'], expense['expense_date']))
                await conn.commit()
        except Exception as e:
            print(f"Ошибка при добавлении расхода: {e}")

# Функция для добавления дохода
async def add_income(user_id, amount):
    async with await connect_db() as conn:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO incomes (user_id, amount) VALUES (%s, %s)
                """, (user_id, amount))
                await conn.commit()
        except Exception as e:
            print(f"Ошибка при добавлении дохода: {e}")

# Функция для получения текущего бюджета
async def get_current_budget(user_id):
    async with await connect_db() as conn:
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Получаем общую сумму доходов
                await cursor.execute("""
                    SELECT SUM(amount) AS total_income FROM incomes
                    WHERE user_id = %s
                """, (user_id,))
                income_result = await cursor.fetchone()
                total_income = income_result['total_income'] if income_result['total_income'] else 0

                # Получаем общую сумму расходов
                await cursor.execute("""
                    SELECT SUM(amount) AS total_expense FROM expenses
                    WHERE user_id = %s
                """, (user_id,))
                expense_result = await cursor.fetchone()
                total_expense = expense_result['total_expense'] if expense_result['total_expense'] else 0

                # Вычисляем текущий бюджет
                current_budget = total_income - total_expense
                return current_budget
        except Exception as e:
            print(f"Ошибка при получении текущего бюджета: {e}")
            return 0