import sys
import os
import pytest
import asyncio
from database import get_user_categories, upload_new_expense, get_current_budget, add_income

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.mark.asyncio
async def test_get_user_categories():
    user_id = 1
    categories = await get_user_categories(user_id)
    assert isinstance(categories, tuple), "Функция должна возвращать кортеж"

@pytest.mark.asyncio
async def test_upload_new_expense():
    expense = {
        'category_id': 1,
        'amount': 100,
        'expense_date': '2025-01-20 11:15:24'
    }
    user_id = 1
    await upload_new_expense(expense, user_id)

@pytest.mark.asyncio
async def test_get_current_budget():
    user_id = 1
    budget = await get_current_budget(user_id)
    assert isinstance(budget, (int, float)), "Функция должна возвращать число"

@pytest.mark.asyncio
async def test_add_income():
    user_id = 1
    amount = 200
    await add_income(user_id, amount)
