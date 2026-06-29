from util import Util
from time import sleep
from curl_cffi import requests
import json

config = Util.get_config()

SOLVER_KEY = config["solverKey"]

def get_token(roblox_session: requests.Session, blob, proxy, cookies):
    session = requests.Session()

    task_payload = {
        "clientKey": SOLVER_KEY,
        "task": {
            "type": "FunCaptchaTask",
            "websiteURL": "https://www.roblox.com/",
            "websitePublicKey": "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F",
            "websiteSubdomain": "roblox.com",
            "data": json.dumps({"blob": blob}),
            "headers": {
                "cookie": cookies
            },
            "proxy": proxy,
        },
    }

    response = session.post("https://api.funbypass.com/createTask", json=task_payload, timeout=60).json()

    task_id = response.get("taskId")

    if task_id == None:
        return None
    
    counter = 0

    while counter < 120:
        sleep(1)

        result_data = session.get(f"https://api.funbypass.com/getTaskResult/{task_id}", timeout=30).json()

        if result_data.get("status") == "ready":
            solution = result_data.get("solution")
            if isinstance(solution, dict) and "token" in solution:
                return solution["token"]
            if isinstance(solution, str):
                return solution
            return None
        
        elif result_data.get("status") == "failure":
            return None
        
        counter += 1

    return None
