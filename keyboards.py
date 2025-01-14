from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

addexpenses = KeyboardButton(text='Добавить траты', )
expenses = KeyboardButton(text='Траты за последний месяц')
transactions  = KeyboardButton(text='Транзакции')
del_transaction = KeyboardButton(text='Удалить транзакцию')

my_keyboard = ReplyKeyboardMarkup(
    keyboard=[[addexpenses], [expenses], [transactions], [del_transaction]],
    resize_keyboard=True
)
