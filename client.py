import json
from urllib.request import Request, urlopen

with open("./client/code.py") as codeFile, open("./client/input.txt") as inputFile, open("./client/output.json", 'wb') as outputFile:
    req = Request(
        "http://127.0.0.1:8001/run",
        data=json.dumps(
            {
                "code": codeFile.read(),
                "input": inputFile.read(),
                "timeout": 5,
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    response = urlopen(req).read()
    _ = outputFile.write(response)

    result = json.loads(response)

    if result["error"]:
        print(result["error"])
    else:
        print(result["stdout"])
