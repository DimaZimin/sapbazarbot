from aiogram import Dispatcher


from .admin_filter import IsCategory

def setup(dp: Dispatcher):
    dp.filters_factory.bind(IsCategory)
    pass
