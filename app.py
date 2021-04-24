from handlers.users.my_questions import check_new_answers_task, \
    unanswered_questions_task_users, unanswered_questions_task_group


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
    dp.loop.create_task(blog_task_for_channel(3500))
    dp.loop.create_task(check_new_answers_task(7000))
    dp.loop.create_task(unanswered_questions_task_group(1000))
    dp.loop.create_task(unanswered_questions_task_users(1000))
    executor.start_polling(dp, on_startup=on_startup)
