

async def on_startup(dp):
    import filters
    import middlewares
    filters.setup(dp)
    middlewares.setup(dp)

    from utils.notify_admins import on_startup_notify
    await on_startup_notify(dp)


if __name__ == '__main__':
    from aiogram import executor
    from handlers import dp
    from handlers.users.subscription import blog_task
    from handlers.users.subscription import scheduled_task
    dp.loop.create_task(scheduled_task(1200))
    dp.loop.create_task(blog_task(600))
    executor.start_polling(dp, on_startup=on_startup)
