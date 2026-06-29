import aiohttp
import asyncio
import random
import string
import time
import base64
import json
from datetime import datetime

FUNBYPASS_API_KEY = "FUN-33KUYP1WTQP4W91M"
FUNBYPASS_BASE_URL = "https://api.funbypass.com"
ROBLOX_SIGNUP_URL = "https://auth.roblox.com/v2/signup"
ROBLOX_USERNAME_CHECK_URL = "https://auth.roblox.com/v1/usernames/validate"
ROBLOX_CAPTCHA_KEY = "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"
OUTPUT_FILE = "accounts.txt"

PROXY = "http://1I2zNUuGf_lightning_proxy-country-any:0azv9rghjq@resident.lightningproxies.net:8080"

ADJECTIVES = [
    "Cool", "Epic", "Swift", "Dark", "Bright", "Silent", "Wild", "Lucky", "Brave", "Mighty",
    "Crazy", "Happy", "Sneaky", "Royal", "Golden", "Silver", "Crystal", "Shadow", "Storm", "Fire"
]

NOUNS = [
    "Wolf", "Dragon", "Phoenix", "Tiger", "Eagle", "Lion", "Shark", "Bear", "Hawk", "Cobra",
    "Panther", "Viper", "Fox", "Raven", "Falcon", "Jaguar", "Lynx", "Puma", "Raptor", "Storm"
]

NAMES = [
    "Alex", "Max", "Jake", "Ryan", "Kyle", "Mike", "Nick", "Sam", "Chris", "Matt",
    "Luke", "Zack", "Cole", "Drew", "Seth", "Josh", "Evan", "Adam", "Eric", "Mark"
]


def generate_username() -> str:
    style = random.randint(1, 5)
    if style == 1:
        return f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(1, 999)}"
    elif style == 2:
        return f"{random.choice(NAMES)}{random.choice(NOUNS)}{random.randint(0, 99)}"
    elif style == 3:
        return f"{random.choice(NAMES)}{random.choice(['_', 'x', ''])}{random.randint(100, 9999)}"
    elif style == 4:
        return f"{random.choice(ADJECTIVES)}{random.choice(NAMES)}{random.randint(1, 99)}"
    else:
        return f"{random.choice(NOUNS)}{random.choice(NOUNS)}{random.randint(1, 99)}"


def generate_password() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


def generate_birthday() -> str:
    year = random.randint(datetime.now().year - 25, datetime.now().year - 18)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}T00:00:00.000Z"


async def check_username(session: aiohttp.ClientSession, username: str) -> bool:
    params = {"username": username, "birthday": generate_birthday(), "context": "Signup"}
    try:
        async with session.get(ROBLOX_USERNAME_CHECK_URL, params=params) as resp:
            data = await resp.json()
            return data.get("code") == 0
    except:
        return False


async def get_csrf_token(session: aiohttp.ClientSession) -> str:
    try:
        async with session.post(ROBLOX_SIGNUP_URL, json={}) as resp:
            return resp.headers.get("x-csrf-token", "")
    except:
        return ""


async def solve_captcha(proxy: str, blob: str = None) -> dict:
    async with aiohttp.ClientSession() as session:
        task = {
            "type": "FunCaptchaTask",
            "websiteURL": "https://www.roblox.com",
            "websitePublicKey": ROBLOX_CAPTCHA_KEY,
            "websiteSubdomain": "roblox-api",
            "proxy": proxy,
            "enablePOW": True,
        }

        if blob:
            task["data"] = json.dumps({"blob": blob})

        payload = {"clientKey": FUNBYPASS_API_KEY, "task": task}

        print(f"[*] Creating captcha task...")
        async with session.post(f"{FUNBYPASS_BASE_URL}/createTask", json=payload) as resp:
            result = await resp.json()
            print(f"[*] Response: {result}")
            if result.get("errorId") != 0:
                return {"success": False, "error": result.get("errorDescription", result.get("errorCode", "Failed"))}
            task_id = result.get("taskId")
            print(f"[*] Task ID: {task_id}")

        for i in range(300):
            await asyncio.sleep(0.5)
            async with session.get(f"{FUNBYPASS_BASE_URL}/getTaskResult/{task_id}") as resp:
                result = await resp.json()
                status = result.get("status")
                if i % 10 == 0:
                    print(f"[*] Status: {status}")
                if status == "ready":
                    if result.get("errorId") == 0:
                        return {"success": True, "token": result.get("solution", {}).get("token")}
                    return {"success": False, "error": result.get("errorDescription", "Failed")}
                elif status == "failure":
                    return {"success": False, "error": result.get("errorDescription", result.get("errorCode", "Failed"))}

        return {"success": False, "error": "Timeout"}


async def continue_challenge(session: aiohttp.ClientSession, challenge_id: str, captcha_token: str, unified_captcha_id: str) -> dict:
    """Continue the challenge after solving captcha"""
    url = "https://apis.roblox.com/challenge/v1/continue"

    challenge_metadata = {
        "unifiedCaptchaId": unified_captcha_id,
        "captchaToken": captcha_token,
        "actionType": "Signup"
    }

    payload = {
        "challengeId": challenge_id,
        "challengeType": "captcha",
        "challengeMetadata": json.dumps(challenge_metadata)
    }

    async with session.post(url, json=payload) as resp:
        return await resp.json()


async def signup(proxy: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://www.roblox.com",
        "Referer": "https://www.roblox.com/",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        print("[*] Finding available username...")
        username = None
        for _ in range(20):
            candidate = generate_username()
            if await check_username(session, candidate):
                username = candidate
                print(f"[+] Username available: {username}")
                break

        if not username:
            return {"success": False, "error": "Could not find available username"}

        password = generate_password()
        birthday = generate_birthday()

        csrf = await get_csrf_token(session)
        if csrf:
            session.headers.update({"x-csrf-token": csrf})

        payload = {
            "username": username,
            "password": password,
            "birthday": birthday,
            "gender": random.randint(1, 2),
            "isTosAgreementBoxChecked": True,
            "agreementIds": [],
        }

        # First request to get challenge
        print("[*] Initial signup request...")
        async with session.post(ROBLOX_SIGNUP_URL, json=payload) as resp:
            resp_text = await resp.text()
            print(f"[*] Status: {resp.status}")
            print(f"[*] Headers: {dict(resp.headers)}")

            if resp.status == 200:
                data = json.loads(resp_text)
                cookie = resp.cookies.get(".ROBLOSECURITY")
                return {"success": True, "username": username, "password": password, "userId": data.get("userId"), "cookie": str(cookie) if cookie else None}

            challenge_id = resp.headers.get("rblx-challenge-id")
            challenge_metadata_b64 = resp.headers.get("rblx-challenge-metadata")

            print(f"[*] Challenge ID: {challenge_id}")
            print(f"[*] Challenge Metadata: {challenge_metadata_b64}")

            if not challenge_id or not challenge_metadata_b64:
                try:
                    data = json.loads(resp_text)
                    errors = data.get("errors", [])
                    err = errors[0].get("message", resp_text) if errors else resp_text
                except:
                    err = resp_text
                return {"success": False, "error": err}

            # Decode metadata
            try:
                metadata = json.loads(base64.b64decode(challenge_metadata_b64))
                print(f"[*] Decoded metadata: {metadata}")
                blob = metadata.get("dataExchangeBlob")
                unified_captcha_id = metadata.get("unifiedCaptchaId")
            except Exception as e:
                return {"success": False, "error": f"Failed to parse metadata: {e}"}

        # Solve captcha
        print("[*] Solving captcha...")
        captcha = await solve_captcha(proxy, blob)
        if not captcha.get("success"):
            return {"success": False, "error": f"Captcha: {captcha.get('error')}"}

        captcha_token = captcha.get("token")
        print(f"[+] Captcha solved! Token: {captcha_token[:50]}...")

        # Continue the challenge
        print("[*] Continuing challenge...")
        csrf = await get_csrf_token(session)
        if csrf:
            session.headers.update({"x-csrf-token": csrf})

        continue_result = await continue_challenge(session, challenge_id, captcha_token, unified_captcha_id)
        print(f"[*] Continue result: {continue_result}")

        # Retry signup with challenge headers
        challenge_response = {
            "unifiedCaptchaId": unified_captcha_id,
            "captchaToken": captcha_token,
            "actionType": "Signup"
        }

        session.headers.update({
            "rblx-challenge-id": challenge_id,
            "rblx-challenge-type": "captcha",
            "rblx-challenge-metadata": base64.b64encode(json.dumps(challenge_response).encode()).decode(),
        })

        print("[*] Final signup attempt...")
        async with session.post(ROBLOX_SIGNUP_URL, json=payload) as resp:
            resp_text = await resp.text()
            print(f"[*] Status: {resp.status}")

            if resp.status == 200:
                data = json.loads(resp_text)
                cookie = resp.cookies.get(".ROBLOSECURITY")
                return {"success": True, "username": username, "password": password, "userId": data.get("userId"), "cookie": str(cookie) if cookie else None}

            try:
                data = json.loads(resp_text)
                errors = data.get("errors", [])
                err = errors[0].get("message", resp_text) if errors else resp_text
            except:
                err = resp_text
            return {"success": False, "error": err}


async def main():
    print("=" * 50)
    print("Roblox Account Generator")
    print("=" * 50)

    if not PROXY:
        print("[!] Set PROXY in script")
        return

    print(f"[*] Proxy: {PROXY[:40]}...")

    try:
        count = int(input("\nHow many accounts? "))
    except ValueError:
        count = 1

    success_count = 0
    for i in range(count):
        print(f"\n[{i+1}/{count}] Creating account...")
        result = await signup(PROXY)

        if result.get("success"):
            combo = f"{result['username']}:{result['password']}"
            print(f"[+] SUCCESS: {combo}")
            with open(OUTPUT_FILE, "a") as f:
                f.write(combo + "\n")
            success_count += 1
        else:
            print(f"[-] FAILED: {result.get('error')}")

        if i < count - 1:
            await asyncio.sleep(5)

    print(f"\n{'=' * 50}")
    print(f"Done! {success_count}/{count} accounts")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
