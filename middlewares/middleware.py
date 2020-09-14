from aiogram.dispatcher.filters.state import State, StatesGroup

class Form(StatesGroup):
    state = State()

class CreateJob(StatesGroup):
    job_name = State()
    company_name = ()
    job_description = State()
    job_category = State()
    job_category_add = State()
    job_location = State()
    job_location_add = State()
    send_invoice = State()
