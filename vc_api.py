from config import *
import jwt
import requests
import json


def createMeeting():
    headers = {'auth': VC_KEY,
               'content-type': 'application/json'}
    r = requests.post(
        f'https://vc.medsenger.ru/admin/rooms',
        headers=headers)

    y = json.loads(r.text)

    return 'https://vc.medsenger.ru/?access_key=' + y['keys']['doctor'], \
           'https://vc.medsenger.ru/?access_key=' + y['keys']['patient']

def getMeetingInfo():
    headers = {'auth': VC_KEY,
               'content-type': 'application/json'}
    r = requests.get(
        f'https://vc.medsenger.ru/admin/rooms',
        headers=headers)

    y = json.loads(r.text)

    return y['message']

