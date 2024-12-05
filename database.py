import os
import pymysql

class Database:
    def __init__(self):
        self.connect()

    def connect(self):
        self.db = pymysql.connect(
            host=os.environ["DB_HOST"],
            user="macon",
            password="a6GHsb6aj",
            database="macon",
        )

        if self.db.open:
            self.cursor = self.db.cursor()

    def disconnect(self):
        self.cursor.close()
        self.db.close()

    def select_all(self, sql, variables=()):
        self.cursor.execute(sql, variables)
        return self.cursor.fetchall()