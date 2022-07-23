from datetime import datetime
from typing import Any, Dict, List
import PySimpleGUI as sg
import socketio


sock = socketio.Client()
sock.connect('http://localhost:5000')


# keep a list of recent messages
MSG_LIST: List[Dict[str, Any]]= []


# define layout
layout = [
    [sg.Text(key='__output__')],
    [
        sg.Button('Server Timestamp', key='server_timestamp'),
        sg.Button('Clients Count', key='clients_count'),
        sg.Button('Connection Time', key='connection_start'),
    ],
    [sg.Button('Quit')],
]


# create the window
window = sg.Window('WS Client', layout)


def event_timestamp(ts: datetime):
    """
    generate a message prefix for given timestamp

    :param ts datetime: timestamp to be used
    """
    return '[' + ts.strftime('%H:%M:%S') + ']'


def format_msg(m: Dict[str, Any]):
    """
    format message object with timestamp and content

    :param m Dict[str, Any]: message object
    """
    return event_timestamp(m.get('at', datetime.now())) + ' ' + m.get('message', '')


@sock.on('message')
def handle_messages(data):
    """
    listen for server responses
    """
    o = window['__output__']

    # keep a list of recent messages by deleting older ones
    if len(MSG_LIST) > 10: MSG_LIST.pop(0)
    MSG_LIST.append(
        {
            'message': data,
            'at': datetime.now()
        }
    )

    # update output with list of messages
    o.update('' + '\n'.join(map(format_msg, MSG_LIST)))


# run a loop to listen to window events
while True:
    event, _ = window.read()

    # break loop if user want to quit
    if event == sg.WINDOW_CLOSED or event == 'Quit': break

    # send a message to server, as defined in layout
    sock.emit('query', event)


# disconnect socket
sock.disconnect()

# close window
window.close()

