import time
import schedule
import os

from models import User
from bot_telegram import get_test


def job():
    users = User.select()
    for user in users:
        get_test(None, user)


if __name__ == '__main__':
    schedule.every(2).seconds.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)
