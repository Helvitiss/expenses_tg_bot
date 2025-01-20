from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Добавить траты')],
        [KeyboardButton(text='Траты за последний месяц')],
        [KeyboardButton(text='Транзакции')],
        [KeyboardButton(text='Удалить транзакцию')],
        [KeyboardButton(text='Ввести доход')],
        [KeyboardButton(text='Текущий бюджет')]
    ],
    resize_keyboard=True
)

# Функция для генерации клавиатуры для выбора категорий
def create_category_keyboard(categories):
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category['category_name'],
                       callback_data=f"category_{category['category_id']}_{category['category_name']}")

    # Генерируем клавиатуру
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="Новая категория", callback_data="new_category"))
    return builder.as_markup()
