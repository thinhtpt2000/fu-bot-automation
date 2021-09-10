import sqlite3

import bot_utils as utils


def init_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # create query
    query = """CREATE TABLE IF NOT EXISTS USERS(
            ID VARCHAR(50) PRIMARY KEY NOT NULL,
            EMAIL VARCHAR(200) NOT NULL, 
            PASSWORD VARCHAR(500) NOT NULL)"""
    cursor.execute(query)
    # commit and close
    conn.commit()
    conn.close()


def create(user_id, email, password):
    conn = sqlite3.connect('users.db')
    hashPwd = utils.encode(password)
    query = ('INSERT INTO USERS (ID, EMAIL, PASSWORD) '
             'VALUES (:ID, :EMAIL, :PASSWORD);')
    params = {
        'ID': user_id,
        'EMAIL': email,
        'PASSWORD': hashPwd
    }
    conn.execute(query, params)
    # commit and close
    conn.commit()
    conn.close()


def update(user_id, email, password):
    conn = sqlite3.connect('users.db')
    hashPwd = utils.encode(password)
    query = ('UPDATE USERS SET EMAIL = :EMAIL, PASSWORD = :PASSWORD '
             'WHERE ID=:ID;')
    params = {
        'ID': user_id,
        'EMAIL': email,
        'PASSWORD': hashPwd
    }
    conn.execute(query, params)
    # commit and close
    conn.commit()
    conn.close()


def update_pwd(user_id, password):
    conn = sqlite3.connect('users.db')
    hashPwd = utils.encode(password)
    query = ('UPDATE USERS SET PASSWORD = :PASSWORD '
             'WHERE ID=:ID;')
    params = {
        'ID': user_id,
        'PASSWORD': hashPwd
    }
    conn.execute(query, params)
    # commit and close
    conn.commit()
    conn.close()


def delete(user_id):
    conn = sqlite3.connect('users.db')
    query = ('DELETE from USERS WHERE ID=:ID;')
    params = {
        'ID': user_id,
    }
    conn.execute(query, params)
    # commit and close
    conn.commit()
    conn.close()


def read(user_id):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT EMAIL, PASSWORD FROM USERS WHERE ID=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row
