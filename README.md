# Server

Local server to run python code in a WASM sandbox.

```sh
# using pip
pip install fastapi uvicorn pyeryx
python server.py

# using uv
uv sync --frozen
uv run server.py
```

Network access is not allowed.

File reading & writing is allowed only in [./session](./session) directory.

# Client

Local test client.

```sh
python client.py
```

Change test code in [./client/code.py](./client/code.py) or input in [./client/input.txt](./client/input.txt).
