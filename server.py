import timeago
from datetime import datetime
from threading import Lock
from typing import Dict
from flask import Flask, request
from flask_socketio import SocketIO, send


app = Flask(__name__)
sock = SocketIO(app, cors_allowed_origins='*')


# initial value for count of conneted clients
CLIENT_COUNT = 0

# store start time of every client
CLIENT_TIMES: Dict[str, datetime] = {}


def status_update():
    """
    broadcast a message every minute
    """
    while True:
        sock.send('Connected')
        sock.sleep(60)


@sock.event
def connect():
    """
    handle `connect` event
    """
    # `sid` is injected to the reqeust context by socketIO
    CLIENT_TIMES[request.sid] = datetime.now()

    # increase the number of clients connected
    global CLIENT_COUNT
    CLIENT_COUNT += 1


@sock.event
def disconnect():
    """
    handle `disconnect]` event
    """
    # `sid` is injected to the reqeust context by socketIO
    del CLIENT_TIMES[request.sid]

    # reduce the number of clients connected
    global CLIENT_COUNT
    CLIENT_COUNT -= 1


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

