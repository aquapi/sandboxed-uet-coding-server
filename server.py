"""
Python Server for Local Code Execution
Copy this file to your machine and run: python python_server.py
"""

from threading import Timer

import eryx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.base import RequestResponseEndpoint

app = FastAPI(title="Python Runner API")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Add middleware to handle preflight requests with Private Network Access
@app.middleware("http")
async def add_private_network_access_headers(
    request: Request, call_next: RequestResponseEndpoint
):
    response = await call_next(request)
    # Enable Private Network Access for Chrome/Edge
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


class RunRequest(BaseModel):
    code: str = Field(..., min_length=1)
    input: str | None = Field(description="Input data for the program")
    timeout: int | None = Field(
        description="Seconds before killing the run (default 5)"
    )


class RunResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool = False
    error: str | None = None


@app.post("/run", response_model=RunResult)
def run_code(req: RunRequest):
    timeout = req.timeout or 5
    if timeout > 30:
        raise HTTPException(status_code=400, detail="Malicious timeout (max 30s).")

    code = req.code.strip()
    if len(code) > 20000:
        raise HTTPException(
            status_code=400, detail="Code too large (max 20000 characters)."
        )

    print("Received code: ```py")
    print(code if len(code) < 500 else code[:500] + "...")
    print("```")

    session = eryx.Session(
        resource_limits=eryx.ResourceLimits(max_memory_bytes=256_000_000),
        result_variable="",
    )

    if req.input:
        testInput = req.input.strip()

        print(f"Received input: {testInput!r}")
        print(f"Input length: {len(testInput)}")

        _ = session.execute(f"""
def f():
    import builtins
    import io

    stdin = io.StringIO({testInput!r})

    def finput(prompt = ""):
        line = stdin.readline()
        if line == "":
            raise EOFError

        if line.endswith("\\n"):
            line = line[:-1]
        if line.endswith("\\r"):
            line = line[:-1]

        return line

    builtins.input = finput
f()
del f
""")

    token = eryx.CancelToken()
    Timer(timeout, token.cancel).start()

    try:
        result = session.execute(code, cancel=token)

        return RunResult(
            stdout=result.stdout_text,
            stderr=result.stderr_text,
            exit_code=0,
            timed_out=False,
        )
    except eryx.CancelledError:
        return RunResult(
            stdout="",
            stderr="Process killed due to timeout",
            exit_code=None,
            timed_out=True,
        )
    except Exception as e:
        return RunResult(
            stdout="", stderr="", exit_code=None, timed_out=False, error=str(e)
        )


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("Starting Python Code Execution Server...")
    print("Server will run at: http://127.0.0.1:8001")
    print("Make sure you have installed: pip install fastapi uvicorn pyeryx")
    print("Ready to execute Python code locally!")
    uvicorn.run("__main__:app", host="127.0.0.1", port=8001, reload=False)
