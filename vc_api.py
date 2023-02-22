from config import *
import jwt
import requests
import json


def createMeeting():
    headers = {'auth': VC_KEY,
               'content-type': 'application/json'}
    r = requests.post(
        VC_URL + f'/admin/rooms',
        headers=headers)

    y = json.loads(r.text)

    return y['id'], \
           VC_URL + '/?access_key=' + y['keys']['doctor'], \
           VC_URL + '/?access_key=' + y['keys']['patient']


def getMeetingInfo(room_id):
    headers = {'auth': VC_KEY,
               'content-type': 'application/json'}
    r = requests.get(
        VC_URL + f'/admin/rooms/' + str(room_id),
        headers=headers)

    y = json.loads(r.text)

    return y['message']

