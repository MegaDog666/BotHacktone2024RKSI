from aiogram.fsm.state import State, StatesGroup

class PreferencesForm(StatesGroup):
    cuisine = State()
    interests = State()
    user_id = State()
    username = State()

class PreferencesFormEdit(StatesGroup):
    cuisine_edit = State()
    interests_edit = State()
    user_id_edit = State()

class pointForm(StatesGroup):
    waiting_for_location = State()

# class RateForm(StatesGroup):
#     place = State()
#     rating = State()
