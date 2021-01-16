

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
    from handlers.users.subscription import blog_task, blog_task_for_channel
    from handlers.users.subscription import job_task
    dp.loop.create_task(job_task(2500))
    dp.loop.create_task(blog_task(3000))
    dp.loop.create_task(blog_task_for_channel(5))
    executor.start_polling(dp, on_startup=on_startup)
