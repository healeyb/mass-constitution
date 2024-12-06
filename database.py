import os
import pymysql

from dotenv import load_dotenv
load_dotenv(override=True)

class Database:
    def __init__(self):
        self.connect()

    def connect(self):
        self.db = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"],
            database="macon",
            cursorclass=pymysql.cursors.DictCursor,
        )

        if self.db.open:
            self.cursor = self.db.cursor()

    def disconnect(self):
        self.cursor.close()
        self.db.close()

    def select_all(self, sql, variables=()):
        self.cursor.execute(sql, variables)
        return self.cursor.fetchall()