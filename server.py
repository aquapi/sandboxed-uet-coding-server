"""
Python Server for Local Code Execution
Copy this file to your machine and run: python python_server.py
"""

import logging
import logging.config
import os
from collections.abc import Awaitable, Callable
from threading import Timer

import eryx
import uvicorn
import uvicorn.config
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# use uvicorn logger
logging.config.dictConfig(uvicorn.config.LOGGING_CONFIG)
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Python Runner API")

VFS_MOUNT_PATH = "./.uet-coding-fs"
session: eryx.Session

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
    code = req.code.strip()
    if len(code) > 20000:
        raise HTTPException(
            status_code=400, detail="Code too large (max 20000 characters)."
        )

    logger.info(f"Code:\n```py\n{code if len(code) < 500 else code[:500] + '...'}\n```")

    if req.input:
        testInput = req.input.strip()

        logger.info(f"Input:\n```\n{testInput!r}\n``` ({len(testInput)} characters)")

        # inject input into current session
        _ = session.execute(f"""
import sys
import io
sys.stdin = io.StringIO({testInput!r})
""")

        # clear sys & io variable
        session.clear_state()

    try:
        token = eryx.CancelToken()
        Timer(req.timeout if req.timeout and req.timeout <= 15 else 15, token.cancel).start()

        result = session.execute(code, cancel=token)
        session.reset()

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
    except eryx.ExecutionError as e:
        return RunResult(
            stdout="", stderr="", exit_code=None, timed_out=False, error=str(e)
        )


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # create vfs target mount directory
    try:
        os.mkdir(VFS_MOUNT_PATH)
        logger.info(f"Created `{VFS_MOUNT_PATH}`.")
    except FileExistsError:
        logger.info(f"Created `{VFS_MOUNT_PATH}` (already existed).")
    except:
        raise

    # create WASM sandbox session
    session = eryx.Session(
        result_variable="",
        volumes=[(VFS_MOUNT_PATH, "/", False)],
    )
    logger.info("Created WASM sandbox.")

    uvicorn.run("__main__:app", host="127.0.0.1", port=8001, reload=False)
