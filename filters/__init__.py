from aiogram import Dispatcher
from .filters import IsCategory
from .filters import IsLocation
from .filters import SubscriptionCategories
from .filters import SubscriptionLocations
from .filters import JobCategory
from .filters import JobLocation


def setup(dp: Dispatcher):
    dp.filters_factory.bind(IsCategory)
    dp.filters_factory.bind(IsLocation)
    dp.filters_factory.bind(SubscriptionCategories)
    dp.filters_factory.bind(SubscriptionLocations)
    dp.filters_factory.bind(JobCategory)
    dp.filters_factory.bind(JobLocation)
    pass
