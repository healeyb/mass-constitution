import os
import pymysql

from dotenv import load_dotenv
load_dotenv(override=True)

class Database:
    db = None

    def connect(self):
        if not self.db:
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
        self.db = None

    def select_all(self, sql, variables=()):
        self.connect()

        self.cursor.execute(sql, variables)
        data = self.cursor.fetchall()

        self.disconnect()
        return data

    def select_one(self, sql, variables=()):
        self.connect()

        self.cursor.execute(sql, variables)
        data = self.cursor.fetchall()

        self.disconnect()
        return data[0] if data else None

    def insert(self, sql, variables=()):
        self.connect()

        self.cursor.execute(sql, variables)
        self.db.commit()

        last_row_id = self.cursor.lastrowid

        self.disconnect()
        return last_row_id

    def mutate(self, sql, variables=()):
        self.connect()

        self.cursor.execute(sql, variables)
        self.db.commit()

        row_cnt = self.cursor.rowcount

        self.disconnect()
        return row_cnt