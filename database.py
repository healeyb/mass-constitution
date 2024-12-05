import mysql.connector

class Database:
    def __init__(self):
        self.connect()

    def connect(self):
        self.db = mysql.connector.connect(
            host="127.0.0.1",
            user="macon",
            password="a6GHsb6aj",
            database="macon",
        )

        self.cursor = self.db.cursor()

    def disconnect(self):
        self.cursor.close()
        self.db.close()

    def select_all(self, sql, variables=()):
        self.cursor.execute(sql, variables)
        return self.cursor.fetchall()