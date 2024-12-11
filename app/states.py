from aiogram.fsm.state import State, StatesGroup

class PreferencesForm(StatesGroup):
    cuisine = State()
    interests = State()

class RateForm(StatesGroup):
    place = State()
    rating = State()

class pointForm(StatesGroup):
    waiting_for_location = State()