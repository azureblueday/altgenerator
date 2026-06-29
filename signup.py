import aiohttp
import asyncio
import random
import string
import time
import json
from datetime import datetime

FUNBYPASS_API_KEY = "FUN-GDZ8I8EUY01J0C97"
FUNBYPASS_BASE_URL = "https://api.funbypass.com"
ROBLOX_SIGNUP_URL = "https://auth.roblox.com/v2/signup"
ROBLOX_USERNAME_CHECK_URL = "https://auth.roblox.com/v1/usernames/validate"
ROBLOX_CAPTCHA_KEY = "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"
OUTPUT_FILE = "accounts.txt"

PROXY = "http://RXClbNH987_lightning_proxy-country-any:1853reph11@resident.lightningproxies.net:8080"

ADJECTIVES = ["Cool", "Epic", "Swift", "Dark", "Bright", "Silent", "Wild", "Lucky", "Brave", "Mighty", "Crazy", "Happy", "Royal", "Golden", "Silver", "Shadow", "Storm", "Fire", "Ice", "Thunder"]
NOUNS = ["Wolf", "Dragon", "Phoenix", "Tiger", "Eagle", "Lion", "Shark", "Bear", "Hawk", "Cobra", "Panther", "Fox", "Raven", "Falcon", "Jaguar", "Blade", "Knight", "Warrior", "Hunter", "Ranger"]
NAMES = ["Alex", "Max", "Jake", "Ryan", "Kyle", "Mike", "Nick", "Sam", "Chris", "Matt", "Luke", "Zack", "Cole", "Drew", "Josh", "Evan", "Adam", "Eric", "Mark", "Leo"]


def generate_username() -> str:
    style = random.randint(1, 4)
    if style == 1:
        return f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(1, 999)}"
    elif style == 2:
        return f"{random.choice(NAMES)}{random.choice(NOUNS)}{random.randint(1, 99)}"
    elif style == 3:
        return f"{random.choice(NAMES)}{random.randint(100, 9999)}"
    else:
        return f"{random.choice(ADJECTIVES)}{random.choice(NAMES)}{random.randint(1, 99)}"


def generate_password() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


def generate_birthday() -> str:
    year = random.randint(datetime.now().year - 25, datetime.now().year - 18)
    return f"{year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}T00:00:00.000Z"


async def check_username(session: aiohttp.ClientSession, username: str) -> bool:
    try:
        async with session.get(ROBLOX_USERNAME_CHECK_URL, params={"username": username, "birthday": generate_birthday(), "context": "Signup"}) as resp:
            data = await resp.json()
            return data.get("code") == 0
    except:
        return False


async def get_csrf(session: aiohttp.ClientSession) -> str:
    try:
        async with session.post("https://auth.roblox.com/v2/login", json={}) as resp:
            return resp.headers.get("x-csrf-token", "")
    except:
        return ""


async def solve_captcha(proxy: str) -> dict:
    print("[*] Solving captcha (this may take 30-60 seconds)...")

    async with aiohttp.ClientSession() as session:
        task = {
            "type": "FunCaptchaTask",
            "websiteURL": "https://www.roblox.com/account/signupredir",
            "websitePublicKey": ROBLOX_CAPTCHA_KEY,
            "websiteSubdomain": "client-api",
            "proxy": proxy,
            "enablePOW": True,
        }

        async with session.post(f"{FUNBYPASS_BASE_URL}/createTask", json={"clientKey": FUNBYPASS_API_KEY, "task": task}) as resp:
            if resp.status != 200:
                text = await resp.text()
                print(f"[-] API error ({resp.status}): {text[:100]}")
                return {"success": False, "error": f"API returned {resp.status}"}
            try:
                result = await resp.json()
            except:
                text = await resp.text()
                return {"success": False, "error": f"Invalid response: {text[:100]}"}
            if result.get("errorId") != 0:
                return {"success": False, "error": result.get("errorCode", result.get("errorDescription", "Task failed"))}
            task_id = result.get("taskId")
            print(f"[*] Task: {task_id}")

        start = time.time()
        while time.time() - start < 180:
            await asyncio.sleep(1)
            async with session.get(f"{FUNBYPASS_BASE_URL}/getTaskResult/{task_id}") as resp:
                result = await resp.json()
                status = result.get("status")

                elapsed = int(time.time() - start)
                if elapsed % 5 == 0:
                    print(f"[*] Status: {status} ({elapsed}s)")

                if status == "ready":
                    if result.get("errorId") == 0:
                        token = result.get("solution", {}).get("token")
                        print(f"[+] Solved!")
                        return {"success": True, "token": token}
                    err = f"{result.get('errorCode')}: {result.get('errorDescription')}"
                    print(f"[-] Error: {err}")
                    return {"success": False, "error": err}
                elif status == "failure":
                    err = f"{result.get('errorCode')}: {result.get('errorDescription')}"
                    print(f"[-] Failed: {err}")
                    print(f"[-] Full response: {result}")
                    return {"success": False, "error": err}

        return {"success": False, "error": "Timeout"}


async def signup(proxy: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://www.roblox.com",
        "Referer": "https://www.roblox.com/",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # Find username
        print("[*] Finding username...")
        username = None
        for _ in range(15):
            candidate = generate_username()
            if await check_username(session, candidate):
                username = candidate
                print(f"[+] Found: {username}")
                break

        if not username:
            return {"success": False, "error": "No available username"}

        password = generate_password()
        birthday = generate_birthday()

        # Solve captcha FIRST
        captcha = await solve_captcha(proxy)
        if not captcha.get("success"):
            return {"success": False, "error": f"Captcha: {captcha.get('error')}"}

        # Get CSRF
        csrf = await get_csrf(session)
        if csrf:
            session.headers.update({"x-csrf-token": csrf})

        # Signup with captcha token
        payload = {
            "username": username,
            "password": password,
            "birthday": birthday,
            "gender": 2,
            "isTosAgreementBoxChecked": True,
            "agreementIds": ["54d8a8f0-d9c8-4cf3-9b6f-5a8e2f9a7a7a"],
            "captchaId": ROBLOX_CAPTCHA_KEY,
            "captchaToken": captcha.get("token"),
            "captchaProvider": "PROVIDER_ARKOSE_LABS",
        }

        print("[*] Signing up...")
        async with session.post(ROBLOX_SIGNUP_URL, json=payload) as resp:
            text = await resp.text()
            print(f"[*] Response ({resp.status}): {text[:200]}")

            if resp.status == 200:
                data = json.loads(text)
                cookie = None
                for c in resp.cookies.values():
                    if c.key == ".ROBLOSECURITY":
                        cookie = c.value
                return {"success": True, "username": username, "password": password, "userId": data.get("userId"), "cookie": cookie}

            # Try to parse error
            try:
                data = json.loads(text)
                err = data.get("errors", [{}])[0].get("message", text)
            except:
                err = text
            return {"success": False, "error": err}


async def main():
    print("=" * 50)
    print("Roblox Account Generator")
    print("=" * 50)
    print(f"Proxy: {PROXY[:50]}...")

    try:
        count = int(input("\nHow many accounts? "))
    except:
        count = 1

    success = 0
    for i in range(count):
        print(f"\n[{i+1}/{count}] Creating account...")
        result = await signup(PROXY)

        if result.get("success"):
            combo = f"{result['username']}:{result['password']}"
            print(f"[+] SUCCESS: {combo}")
            with open(OUTPUT_FILE, "a") as f:
                f.write(combo + "\n")
            success += 1
        else:
            print(f"[-] FAILED: {result.get('error')}")

        if i < count - 1:
            await asyncio.sleep(3)

    print(f"\nDone! {success}/{count} created")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
