# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import bot
import db_utils as db


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    db.init_table()
    bot.run()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
