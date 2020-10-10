from aiogram.dispatcher.filters.state import StatesGroup, State


class JobCreation(StatesGroup):
    job_name = State()
    job_category = State()
    job_location = State()
    job_description = State()
