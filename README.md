# Finance Telegram Bot

> Первый Telegram-бот на aiogram 3 — личный учёт финансов. Создан для отработки FSM, асинхронной работы с БД и inline-клавиатур.

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.17-009688?logo=telegram&logoColor=white)](https://aiogram.dev/)
[![MySQL](https://img.shields.io/badge/MySQL-8.x-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)

---

## О проекте

Бот для ведения личного бюджета прямо в Telegram. Пользователь создаёт собственные категории расходов, записывает траты и доходы, смотрит статистику за месяц и управляет историей транзакций.

Проект написан как первый опыт работы с aiogram 3 — с упором на FSM-сценарии, асинхронную работу с MySQL и inline-клавиатуры с динамическим контентом.

---

## Функциональность

- Регистрация пользователя при первом `/start`
- Добавление расходов с выбором категории из inline-клавиатуры
- Создание новых категорий прямо в процессе добавления траты
- Добавление доходов
- Просмотр расходов за текущий месяц с группировкой по категориям и итоговой суммой
- История последних 10 транзакций
- Удаление транзакции по ID
- Текущий баланс (доходы минус расходы)
- Обработчик нераспознанных команд

---

## Что практиковалось

| Тема | Как применено |
|---|---|
| FSM | Многошаговые сценарии добавления расхода и дохода через `StatesGroup` |
| Inline-клавиатуры | Динамическая генерация категорий через `InlineKeyboardBuilder` |
| Async БД | Асинхронные запросы через `aiomysql` без блокировки event loop |
| SQL | `JOIN`, `GROUP BY`, `SUM`, `INSERT IGNORE`, `DELETE` |
| Тесты | `pytest-asyncio` — покрытие функций работы с БД |

---

## Технологический стек

| | |
|---|---|
| **Bot framework** | aiogram 3.17 |
| **База данных** | MySQL + aiomysql (async) |
| **Конфигурация** | python-dotenv |
| **Тесты** | pytest, pytest-asyncio |

---

## Быстрый старт

```bash
git clone https://github.com/Helvitiss/TG_BOT_pet_project.git
cd TG_BOT_pet_project

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Создай `.env` в корне проекта:

```env
BOT_TOKEN=your_bot_token
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
```

Запустить:

```bash
python main.py
```

---

## Команды и кнопки

| Команда / кнопка | Описание |
|---|---|
| `/start` | Регистрация и главное меню |
| `Добавить траты` | Выбор категории → ввод суммы |
| `Ввести доход` | Ввод суммы дохода |
| `Траты за последний месяц` | Расходы по категориям с итогом |
| `Транзакции` | Последние 10 записей |
| `Удалить транзакцию` | Список с ID → удаление по ID |
| `Текущий бюджет` | Доходы − Расходы |

---

## Тесты

```bash
pytest tests/ -v
```

Покрыты основные функции работы с базой данных: получение категорий, добавление расхода и дохода, расчёт бюджета.

---

## Планы по развитию

- Переход на SQLAlchemy + Repository pattern
- Статистика за произвольный период
- Лимиты по категориям с уведомлениями при превышении
- Docker-окружение

---

## Лицензия

[MIT](LICENSE)
