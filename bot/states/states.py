from aiogram.fsm.state import State, StatesGroup


class Reg(StatesGroup):
    name = State()


class NewOperation(StatesGroup):
    type = State()
    amount = State()
    date = State()
