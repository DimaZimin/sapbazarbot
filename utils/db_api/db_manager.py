import sqlite3


class SQLContextManager:
    """
    SQLite Context Manager
    """

    def __init__(self, database):
        """Connect to database and save connection cursor"""
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def add_subscriber(self, user_id, subscription=True):
        """Add new subscriber"""
        with self.connection:
            try:
                return self.cursor.execute("INSERT INTO `users` (`user_id`, `subscription`) VALUES(?,?)",
                                           (user_id, subscription))
            except sqlite3.IntegrityError:
                return ''

    def get_active_subscriptions(self, subscription=True):
        """Get active subscribers"""
        with self.connection:
            return self.cursor.execute("SELECT * FROM `users` WHERE `subscription` = ?",
                                       (subscription,)).fetchall()

    def subscriber_exists(self, user_id):
        """Checks if user does exist in db"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `users` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def update_subscription(self, user_id, status: bool):
        """Update subscription status of a subscriber"""
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `subscription` = ? WHERE `user_id` = ?",
                                       (status, user_id))

    def update_location(self, user_id, location):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `location` = ? WHERE `user_id` = ?",
                                       (location, user_id))

    def add_user_category(self, user_id, category):
        with self.connection:
            if not self.is_user_category(user_id, category):
                return self.cursor.execute("INSERT INTO `subscriptions` (`user_id`, `category`)  VALUES(?,?)",
                                           (user_id, category))

    def is_user_category(self, user_id, category):
        """Validate if user already have category in subscription """
        with self.connection:
            return self.cursor.execute('SELECT * FROM `subscriptions` WHERE `user_id`= ? AND `category` = ?',
                                       (user_id, category)).fetchall()

    def get_user_categories(self, user_id):
        with self.connection:
            subscribed_categries = self.cursor.execute('SELECT `category` FROM `subscriptions` WHERE `user_id` = ?',
                                                       (user_id,)).fetchall()
            return [cat[0] for cat in subscribed_categries]

    def get_user_location(self, user_id):
        with self.connection:
            location = self.cursor.execute('SELECT `location` FROM `users` where `user_id` = ?',
                                           (user_id,)).fetchone()
            return location[0]

    def remove_subscription(self, user_id):
        with self.connection:
            return self.cursor.execute('DELETE FROM `subscriptions` WHERE `user_id` = ? ', (user_id,))

    def close(self):
        """close connection with db"""
        self.connection.close()
