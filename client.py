import json
from urllib.request import Request, urlopen

with open("./client/code.py") as codeFile, open("./client/input.txt") as inputFile, open("./client/output.json", 'w') as outputFile:
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

    result = json.loads(urlopen(req).read())
    _ = outputFile.write(json.dumps(result, indent=2))

    print('```')
    if result["error"]:
        print(result["error"])
    else:
        print(result["stdout"])
    print('```')
