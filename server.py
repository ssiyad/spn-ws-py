from flask.json import loads
import timeago
from datetime import datetime
from threading import Timer
from typing import Dict, Any, Optional
from flask import Flask, request
from flask_socketio import SocketIO, send


app = Flask(__name__)
sock = SocketIO(app, cors_allowed_origins='*')


# default interval for status update
INTERVAL_DEFAULT = 60

# initial value for count of conneted clients
CLIENT_COUNT = 0

# store start time of every client
CLIENT_TIMES: Dict[str, datetime] = {}

# store interval and timer of individual sessions
INTERVALS: Dict[str, Dict[str, Any]] = {}


def status_update(sid, interval: Optional[int] = None):
    sock.send('Connected', to=sid)

    i = interval or INTERVALS.get(sid, {}).get('interval', INTERVAL_DEFAULT)
    t = Timer(i, status_update, [sid])

    INTERVALS[sid] = {
        'timer': t,
        'interval': i,
    }

    t.start()


def timer_stop(sid):
    t = INTERVALS.get(sid)
    if not t: return;

    t = t.get('timer')
    if not t: return;

    t.cancel()


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

    status_update(request.sid)


@sock.event
def disconnect():
    """
    handle `disconnect` event
    """
    # `sid` is injected to the reqeust context by socketIO
    del CLIENT_TIMES[request.sid]

    # reduce the number of clients connected
    global CLIENT_COUNT
    CLIENT_COUNT -= 1

    t = INTERVALS.get(request.sid, {}).get('timer')
    if not t: return

    t.cancel()


@sock.on('config')
def handle_config(d):
    match d.get('key'):
        case 'interval':
            try:
                value = int(d.get('value', INTERVAL_DEFAULT))
            except:
                send('value must be an integer')
                return
                
            timer_stop(request.sid)
            status_update(request.sid, value)

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
    sock.run(app)
