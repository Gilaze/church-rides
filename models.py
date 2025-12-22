from flask_login import UserMixin
from db import get_db_connection

class User(UserMixin):
    def __init__(self, id, username, full_name, is_driver):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.is_driver = is_driver

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        # Handle SQLite vs Postgres placeholder syntax (? vs %s)
        # This example assumes SQLite syntax for local simplicity
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cur.fetchone()
        conn.close()
        if not user_data:
            return None
        return User(user_data['id'], user_data['username'], user_data['full_name'], user_data['is_driver'])

# Inheritance Example
class Student(User):
    def __init__(self, id, username, full_name):
        super().__init__(id, username, full_name, is_driver=False)

class Driver(User):
    def __init__(self, id, username, full_name):
        super().__init__(id, username, full_name, is_driver=True)

    def add_vehicle(self, vehicle_name, capacity):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO vehicles (driver_id, vehicle_name, capacity) VALUES (?, ?, ?)",
                    (self.id, vehicle_name, capacity))
        conn.commit()
        conn.close()