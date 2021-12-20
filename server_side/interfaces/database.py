import sqlite3
from server_side.util.constants import DATABASE


class DBManager:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = sqlite3.connect(DATABASE["path"])
        self.cursor = self.connection.cursor()
        return self

    def create_tables(self):
        # Create table
        self.cursor.execute("CREATE TABLE user (password int, service int)")
        self.connection.commit()

    def insert_user(self, user) -> int:
        self.cursor.execute(f" INSERT INTO user VALUES ('{user['password']}', '${user['service']}');")
        self.connection.commit()
        return self.cursor.lastrowid

    def delete_user(self, _id=1):
        self.cursor.execute(f" delete from user where rowid={_id}")
        self.connection.commit()

    def get_user(self, _id=1):
        return self.cursor.execute(f"SELECT * FROM user WHERE rowid={_id}").fetchone()

    def get_all_users(self):
        return self.cursor.execute('SELECT * FROM user').fetchall()

    def close(self):
        self.connection.close()

    def drop_tables(self):
        for table in self.cursor.execute("select name from sqlite_master where type = 'table'"):
            self.cursor.execute(f"drop table {table[0]}")
        self.connection.commit()


if __name__ == "__main__":
    db = DBManager().connect()
    db.drop_tables()
    db.create_tables()
    row_id = db.insert_user({"password": 123, "service": 1})
    print("rowid =", row_id)
    print(db.get_user(row_id))
    db.delete_user(row_id)
    print(db.get_all_users())
    db.drop_tables()
    db.close()
