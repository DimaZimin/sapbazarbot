def check_user_requirements(user_id, url) -> str:
    """
    Validate if a url associated with a job on the website satisfies user requirements regarding category and location
    of a job.
    :param user_id: user chat_id
    :param url: url as a string
    :return: URL as a string if satisfies user's subscription records
    """
    user_categories = db_manager.get_user_categories(user_id)
    user_location = db_manager.get_user_location(user_id)
    html = parser.HTMLParser(url)
    if html.location() == user_location and html.category() in user_categories:
        return url


async def scheduled_task(wait_time):
    """
    Main task function that runs every 'wait_time'. Entry parameter must be an integer and corresponds to seconds.
    :param wait_time: integer - seconds
    """
    while True:
        await asyncio.sleep(wait_time)
        logging.info(f'SCHEDULED TASK PERFORMING...')
        json_file = parser.JSONContextManager(json_db)
        xml = parser.XMLParser()
        old_ads = json_file.json_old_ads()
        logging.info(f'CURRENT ADS IDS ({len(xml.get_ids())}) : {xml.get_ids()}\n')
        logging.info(f'OLD ADS : {len(old_ads)}{old_ads}\n')
        logging.info(f'DIFF (NEW ADS): {len(xml.get_ids()) - len(old_ads)}')
        logging.info(f'JSON FILE UPDATING...')
        json_file.update_json()
        subscribers = [sub[0] for sub in db_manager.get_active_subscriptions()]
        new_ads = json_file.json_new_ads()
        logging.info(f'NEW ADS: {new_ads}')
        if new_ads:
            for subscriber in subscribers:
                for url in new_ads:
                    link = check_user_requirements(subscriber, url)
                    if link:
                        html = parser.HTMLParser(link)
                        logging.info(f'URL {link} SENT TO USER ID: {subscriber}')
                        await bot.send_message(subscriber, text=f"<a href='{link}'>New job openning: "
                                                                f"{html.job_title()}</a>",
                                               parse_mode='HTML')