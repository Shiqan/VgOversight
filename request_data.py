import os
import time
from threading import Thread

from requests import HTTPError

from api import VaingloryApi
from flask_app import db
from models import Team
from process_data import process_batch_query

api_key = os.environ.get('API_KEY', None)
api = VaingloryApi(api_key)


class PlayerNotFound(Exception):
    pass


def get_time():
    return time.strftime("%Y-%m-%dT%H:%M%SZ")


def query_player(name, region):
    try:
        response = api.matches(region=region, limit=50, createdAtStart="2017-03-01T00:00:00Z",
                               createdAtEnd=get_time(), sort="-createdAt", player=name)
    except HTTPError as e:
        raise PlayerNotFound(e.message)

    player = [i for i in response["included"] if i["type"] == "player" and i["attributes"]["name"] == name]
    if len(player) == 1:
        return player[0]
    else:
        raise PlayerNotFound("Player {0} not found for region {1}".format(name, region))


def query_team(team_id):
    # shiqan = "2537169e-2619-11e5-91a4-06eb725f8a76"
    # shanlom = "78a83898-7193-11e4-9389-062d0b175276"
    # kanonmara = "d49ff1fe-8ede-11e5-8bec-06f4ee369f53"
    # maestro = "786c586c-8fb7-11e5-a1ef-068789513eb5"
    team = db.session.query(Team).get(team_id)
    for player in team._members:
        response = api.matches(region="eu", createdAtStart="2017-03-01T00:00:00Z",
                               createdAtEnd=get_time(), sort="-createdAt", gameMode="ranked",
                               playerId="{0}".format(player.id))

        print(len(response['data']))
        process_batch_query(response)


def process_id(player_id, gamemode="ranked"):
    return api.matches(region="eu", createdAtStart="2017-03-01T00:00:00Z",
                       createdAtEnd=get_time(), sort="-createdAt", gameMode=gamemode, playerId="{0}".format(player_id))


def process_range(id_range, store=None, gamemode="ranked"):
    if store is None:
        store = {}
    for id in id_range:
        result = process_id(id, gamemode)
        process_batch_query(result)
        store[id] = True
    return store


def threaded_process_range(nthreads, id_range, gamemode):
    """process the id range in a specified number of threads"""
    store = {}
    threads = []
    # create the threads
    for i in range(nthreads):
        ids = id_range[i::nthreads]
        t = Thread(target=process_range, args=(ids, store, gamemode))
        threads.append(t)

    # start the threads
    [t.start() for t in threads]
    # wait for the threads to finish
    [t.join() for t in threads]
    return store


if __name__ == "__main__":
    # query_player("Shiqan", "eu")
    query_team("cca544dd-8fb9-4640-97fa-d20aee017639")
