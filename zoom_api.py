import random

from config import *

import jwt
import requests
import json
from time import time
from jose import jwt
from datetime import datetime


def generateToken(key, sec):
    token = jwt.encode(
        {'iss': key, 'exp': time() + 5000},
        sec,
        algorithm='HS256'
    )
    return token


def createMeeting(key, sec):
    meetingdetails = {"topic": "Видеозвонок medsenger",
                      "type": 2,
                      "password": random.randint(100000, 999999),
                      "start_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                      "duration": "60",
                      "timezone": "Europe/Moscow",
                      "settings": {"host_video": "true",
                                   "participant_video": "true",
                                   "join_before_host": "true",
                                   }
                      }

    headers = {'authorization': 'Bearer ' + generateToken(key, sec),
               'content-type': 'application/json'}
    r = requests.post(
        f'https://api.zoom.us/v2/users/me/meetings',
        headers=headers, data=json.dumps(meetingdetails))

    y = json.loads(r.text)

    return y['id'], y['password']