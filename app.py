import logging

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
    from handlers.users.subscription import blog_task, blog_task_for_channel, points_task
    from handlers.users.subscription import job_task
    try:
        dp.loop.create_task(job_task(60*60*12))
    except Exception as e:
        logging.error('ERROR: ', e)
    try:
        dp.loop.create_task(blog_task(3000))
    except Exception as e:
        logging.error('ERROR: ', e)
    try:
        dp.loop.create_task(blog_task_for_channel(3500))
    except Exception as e:
        logging.error('ERROR: ', e)
    try:
        dp.loop.create_task(check_new_answers_task(7000))
    except Exception as e:
        logging.error('ERROR: ', e)
    try:
        dp.loop.create_task(unanswered_questions_task_group(60*60*24*7))
    except Exception as e:
        logging.error('ERROR: ', e)
    try:
        dp.loop.create_task(unanswered_questions_task_users(60*60*24*7))
    except Exception as e:
        logging.error('ERROR: ', e)
    try:
        dp.loop.create_task(points_task(60*60*24*7))
    except Exception as e:
        logging.error('ERROR: ', e)
    executor.start_polling(dp, on_startup=on_startup)
