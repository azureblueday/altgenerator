import aiohttp
import asyncio
import random
import string
import time
from datetime import datetime

FUNBYPASS_API_KEY = "FUN-33KUYP1WTQP4W91M"
FUNBYPASS_BASE_URL = "https://api.funbypass.com"
ROBLOX_SIGNUP_URL = "https://auth.roblox.com/v2/signup"
ROBLOX_USERNAME_CHECK_URL = "https://auth.roblox.com/v1/usernames/validate"
ROBLOX_CAPTCHA_KEY = "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"
OUTPUT_FILE = "accounts.txt"

ADJECTIVES = [
    "Cool", "Epic", "Swift", "Dark", "Bright", "Silent", "Wild", "Lucky", "Brave", "Mighty",
    "Crazy", "Happy", "Sneaky", "Royal", "Golden", "Silver", "Crystal", "Shadow", "Storm", "Fire",
    "Ice", "Thunder", "Mystic", "Cosmic", "Turbo", "Ultra", "Mega", "Super", "Hyper", "Pro",
    "Elite", "Prime", "Alpha", "Omega", "Nova", "Neon", "Pixel", "Cyber", "Ninja", "Phantom",
    "Rapid", "Stealth", "Blaze", "Frost", "Atomic", "Sonic", "Laser", "Rocket", "Venom", "Titan"
]

NOUNS = [
    "Wolf", "Dragon", "Phoenix", "Tiger", "Eagle", "Lion", "Shark", "Bear", "Hawk", "Cobra",
    "Panther", "Viper", "Fox", "Raven", "Falcon", "Jaguar", "Lynx", "Puma", "Raptor", "Scorpion",
    "Blade", "Storm", "Knight", "Warrior", "Hunter", "Ranger", "Sniper", "Raider", "Slayer", "Master",
    "King", "Lord", "Boss", "Chief", "Ace", "Star", "Legend", "Hero", "Champ", "Wizard",
    "Gamer", "Player", "Killer", "Winner", "Runner", "Rider", "Striker", "Crusher", "Breaker", "Blazer"
]

NAMES = [
    "Alex", "Max", "Jake", "Ryan", "Kyle", "Mike", "Nick", "Sam", "Chris", "Matt",
    "Luke", "Zack", "Cole", "Drew", "Seth", "Josh", "Evan", "Adam", "Eric", "Mark",
    "Lily", "Emma", "Mia", "Zoe", "Luna", "Aria", "Nova", "Ivy", "Ruby", "Sky",
    "Jack", "Leo", "Kai", "Finn", "Owen", "Liam", "Noah", "Eli", "Jax", "Rex"
]


def generate_username() -> str:
    style = random.randint(1, 5)
    if style == 1:
        return f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(1, 999)}"
    elif style == 2:
        num = random.randint(0, 99)
        base = f"{random.choice(NAMES)}{random.choice(NOUNS)}"
        return f"{base}{num}" if num > 0 else base
    elif style == 3:
        return f"{random.choice(NAMES)}{random.choice(['_', 'x', 'X', ''])}{random.randint(100, 9999)}"
    elif style == 4:
        return f"{random.choice(ADJECTIVES)}{random.choice(NAMES)}{random.randint(1, 99)}"
    else:
        return f"{random.choice(NOUNS)}{random.choice(['_', '', 'x'])}{random.choice(NOUNS)}{random.randint(1, 99)}"


def generate_password() -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=10))


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


async def solve_captcha() -> dict:
    async with aiohttp.ClientSession() as session:
        payload = {
            "clientKey": FUNBYPASS_API_KEY,
            "task": {
                "type": "FunCaptchaTask",
                "websiteURL": "https://www.roblox.com/account/signupredir",
                "websitePublicKey": ROBLOX_CAPTCHA_KEY,
                "websiteSubdomain": "roblox-api",
            }
        }

        async with session.post(f"{FUNBYPASS_BASE_URL}/createTask", json=payload) as resp:
            result = await resp.json()
            if result.get("errorId") != 0:
                return {"success": False, "error": result.get("errorDescription", "Task creation failed")}
            task_id = result.get("taskId")

        start = time.time()
        while time.time() - start < 120:
            await asyncio.sleep(1)
            async with session.get(f"{FUNBYPASS_BASE_URL}/getTaskResult/{task_id}") as resp:
                result = await resp.json()
                if result.get("status") == "ready":
                    return {"success": True, "token": result.get("solution", {}).get("token")}
                elif result.get("status") == "failure" or result.get("errorId") == 1:
                    return {"success": False, "error": result.get("errorDescription", "Solve failed")}

        return {"success": False, "error": "Timeout"}


async def signup() -> dict:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
            print(f"[-] Taken: {candidate}")

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

        print("[*] Attempting signup...")
        async with session.post(ROBLOX_SIGNUP_URL, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                cookie = resp.cookies.get(".ROBLOSECURITY")
                return {"success": True, "username": username, "password": password, "userId": data.get("userId"), "cookie": str(cookie) if cookie else None}

            data = await resp.json()
            errors = data.get("errors", [])

            if any(e.get("code") == 2 for e in errors):
                print("[*] Captcha required, solving...")
                captcha = await solve_captcha()
                if not captcha.get("success"):
                    return {"success": False, "error": f"Captcha failed: {captcha.get('error')}"}

                print("[+] Captcha solved!")
                payload["captchaToken"] = captcha.get("token")
                payload["captchaProvider"] = "PROVIDER_ARKOSE_LABS"

                csrf = await get_csrf_token(session)
                if csrf:
                    session.headers.update({"x-csrf-token": csrf})

                async with session.post(ROBLOX_SIGNUP_URL, json=payload) as retry:
                    if retry.status == 200:
                        data = await retry.json()
                        cookie = retry.cookies.get(".ROBLOSECURITY")
                        return {"success": True, "username": username, "password": password, "userId": data.get("userId"), "cookie": str(cookie) if cookie else None}
                    else:
                        data = await retry.json()
                        err = data.get("errors", [{}])[0].get("message", "Unknown error")
                        return {"success": False, "error": err}

            err = errors[0].get("message", "Unknown error") if errors else "Unknown error"
            return {"success": False, "error": err}


async def main():
    print("=" * 50)
    print("Roblox Account Generator")
    print("=" * 50)

    try:
        count = int(input("How many accounts? "))
    except ValueError:
        count = 1

    success_count = 0
    for i in range(count):
        print(f"\n[{i+1}/{count}] Creating account...")
        result = await signup()

        if result.get("success"):
            combo = f"{result['username']}:{result['password']}"
            print(f"[+] SUCCESS: {combo}")
            with open(OUTPUT_FILE, "a") as f:
                f.write(combo + "\n")
            success_count += 1
        else:
            print(f"[-] FAILED: {result.get('error')}")

        if i < count - 1:
            print("[*] Waiting 5 seconds...")
            await asyncio.sleep(5)

    print(f"\n{'=' * 50}")
    print(f"Done! Created {success_count}/{count} accounts")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
