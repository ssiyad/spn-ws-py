# spn-ws-py

## Setup
```
git clone https://github.com/ssiyad/spn-ws-py spn-ws-py
cd spn-ws-py
pipenv install
```

## Server
```
pipenv run python server.py
```
#### Events
- `query` with body
    - `server_timestamp` returns timetamp (iso 8601)
    - `clients_count` returns number of clients connected at the moment
    - `connection_length` returns time at which current connection was established

