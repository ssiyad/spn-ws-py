import timeago
from threading import Lock
from datetime import datetime
from typing import Dict
from flask import Flask, request
from flask_socketio import SocketIO, send


app = Flask(__name__)
sock = SocketIO(app, cors_allowed_origins='*')


# default interval for status update
INTERVAL_DEFAULT = 6

# initial value for count of conneted clients
CLIENT_COUNT = 0

# store start time of every client
CLIENT_TIMES: Dict[str, datetime] = {}

# store intervals of individual sessions
INTERVALS: Dict[str, int] = {}


def status_update():
    # init counter as 0
    c = 0

    while True:
        # filter intervals by checking if `interval` is a multile of `counter`
        for i in dict(filter(lambda x: c % x[1] == 0, INTERVALS.items())):
            sock.send('Connected', to=i)

        sock.sleep(1)

        # increase counter
        c += 1


@sock.event
def connect():
    """
    handle `connect` event
    """
    # `sid` is injected to the reqeust context by socketIO
    CLIENT_TIMES[request.sid] = datetime.now()
    INTERVALS[request.sid] = INTERVAL_DEFAULT

    # increase the number of clients connected
    global CLIENT_COUNT
    CLIENT_COUNT += 1


@sock.event
def disconnect():
    """
    handle `disconnect` event
    """
    # `sid` is injected to the reqeust context by socketIO
    del CLIENT_TIMES[request.sid]
    del INTERVALS[request.sid]

    # reduce the number of clients connected
    global CLIENT_COUNT
    CLIENT_COUNT -= 1


@sock.on('config')
def handle_config(d):
    match d.get('key'):
        case 'interval':
            try:
                value = int(d.get('value', INTERVAL_DEFAULT))
            except:
                send('value must be an integer')
                return
                
            INTERVALS[request.sid] = value
            send('interval set to ' + str(value))
        case _:
            send('unknown config key')


@sock.on('query')
def handle_query(d):
    """
    handle `query events`
    """
    match d:
        case 'server_timestamp':
            send('Current server timestamp is ' + datetime.now().isoformat())
        case 'clients_count':
            send('Number of clients connected is ' + str(CLIENT_COUNT))
        case 'connection_start':
            t_started = CLIENT_TIMES.get(request.sid)

            # force `connect` if record does not exist
            if not t_started:
                connect()
                t_started = datetime.now()

            t_formatted = timeago.format(t_started, datetime.now())
            send('Connection started ' + t_formatted)
        case _:
            send('unknown query')


if __name__ == '__main__':
    # start a start background task for broadcast
    with Lock(): sock.start_background_task(status_update)
    sock.run(app)
