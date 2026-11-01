"""
Python Server for Local Code Execution
Copy this file to your machine and run: python python_server.py
"""

from collections.abc import Awaitable, Callable
from threading import Timer

import eryx
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Python Runner API")

session = eryx.Session(
    resource_limits=eryx.ResourceLimits(max_memory_bytes=256_000_000),
    result_variable="",
    volumes=[("./session", "/", False)],
)

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
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
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

    session.reset()

    if req.input:
        testInput = req.input.strip()

        print(f"Received input: {testInput!r}")
        print(f"Input length: {len(testInput)}")

        _ = session.execute(f"""
import sys
import io
sys.stdin = io.StringIO({testInput!r})
""")
        session.clear_state()

    try:
        token = eryx.CancelToken()
        Timer(timeout, token.cancel).start()
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
    except Exception as e:  # noqa
        return RunResult(
            stdout="", stderr="", exit_code=None, timed_out=False, error=str(e)
        )


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("Requires: pip install fastapi uvicorn pyeryx")
    uvicorn.run("__main__:app", host="127.0.0.1", port=8001, reload=False)
