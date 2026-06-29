import asyncio
import aiohttp
import random
import string
import base64
import json
import time
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
FUNBYPASS_API_KEY = "FUN-7HDZBUU7UJPO2OB9"

# Roblox — Signup site key (from FunBypass supported sites)
ROBLOX_SIGNUP_KEY = "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"

OUTPUT_FILE = "accounts.txt"

# Pass Roblox's per-session blob to the solver (True) or let FunBypass
# handle the whole session generically (False). Flip this to compare.
USE_BLOB = True

# Proxies: socks5://user:pass@host:port  (rotated per account)
PROXIES = [
    "socks5://uorder40767_fastmode-true_country-US_city-los angeles_session-jzctm6154b_sesstime-1440:dpPri5RW6ocHSyoN@budget.legionproxy.io:1337",
    "socks5://uorder40767_fastmode-true_country-US_city-los angeles_session-veudj8l3ap_sesstime-1440:dpPri5RW6ocHSyoN@budget.legionproxy.io:1337",
    "socks5://uorder40767_fastmode-true_country-US_city-los angeles_session-6kys2vifd5_sesstime-1440:dpPri5RW6ocHSyoN@budget.legionproxy.io:1337",
    "socks5://uorder40767_fastmode-true_country-US_city-los angeles_session-0gmmanexcp_sesstime-1440:dpPri5RW6ocHSyoN@budget.legionproxy.io:1337",
    "socks5://uorder40767_fastmode-true_country-US_city-los angeles_session-0qv1hwdbrh_sesstime-1440:dpPri5RW6ocHSyoN@budget.legionproxy.io:1337",
]

# ─────────────────────────────────────────────────────────────
# WORD LISTS (human-like usernames)
# ─────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────
# FUNBYPASS CLIENT (based on official async example)
# ─────────────────────────────────────────────────────────────
class FunBypass:
    BASE_URL = "https://api.funbypass.com"

    def __init__(self, client_key: str):
        self.client_key = client_key

    async def get_balance(self, session: aiohttp.ClientSession) -> float:
        async with session.post(f"{self.BASE_URL}/getBalance", json={"clientKey": self.client_key}) as resp:
            if resp.status != 200:
                raise Exception(f"API gateway returned {resp.status} (FunBypass server flaky)")
            data = await resp.json(content_type=None)
            if data.get("errorId", 1) != 0:
                raise Exception(f"{data.get('errorCode')}: {data.get('errorDescription')}")
            return data["balance"]

    async def create_task(self, session, website_url, website_public_key, website_subdomain, proxy, data=None) -> str:
        task = {
            "type": "FunCaptchaTask",
            "websiteURL": website_url,
            "websitePublicKey": website_public_key,
            "websiteSubdomain": website_subdomain,
            "proxy": proxy,
            "enablePOW": True,
        }
        if data:
            task["data"] = data

        async with session.post(f"{self.BASE_URL}/createTask", json={"clientKey": self.client_key, "task": task}) as resp:
            result = await resp.json(content_type=None)
            if result.get("errorId", 1) != 0:
                raise Exception(f"{result.get('errorCode')}: {result.get('errorDescription')}")
            return result["taskId"]

    async def get_task_result(self, session, task_id, interval=1.0, timeout=180) -> str:
        elapsed = 0
        while elapsed < timeout:
            async with session.get(f"{self.BASE_URL}/getTaskResult/{task_id}") as resp:
                try:
                    result = await resp.json(content_type=None)
                except Exception:
                    body = await resp.text()
                    print(f"    [funbypass] non-JSON ({resp.status}): {body[:120]}")
                    await asyncio.sleep(interval)
                    elapsed += interval
                    continue

            status = result.get("status")
            if int(elapsed) % 5 == 0:
                print(f"    [funbypass] status={status} ({int(elapsed)}s)")

            if status == "ready":
                if result.get("errorId", 0) == 0:
                    sol = result.get("solution") or {}
                    token = sol.get("token")
                    if token:
                        return token
                    print(f"    [funbypass] ready but no token. raw: {result}")
                    raise Exception("ready without token")
                raise Exception(f"{result.get('errorCode')}: {result.get('errorDescription')}")
            if status == "failure":
                print(f"    [funbypass] failure raw: {result}")
                raise Exception(f"{result.get('errorCode')}: {result.get('errorDescription')}")

            await asyncio.sleep(interval)
            elapsed += interval

        raise TimeoutError(f"Task {task_id} timed out")

    async def solve(self, session, website_url, website_public_key, website_subdomain, proxy, data=None) -> str:
        task_id = await self.create_task(session, website_url, website_public_key, website_subdomain, proxy, data)
        print(f"    [funbypass] task created: {task_id}")
        return await self.get_task_result(session, task_id)


fb = FunBypass(FUNBYPASS_API_KEY)


# ─────────────────────────────────────────────────────────────
# ROBLOX SIGNUP
# ─────────────────────────────────────────────────────────────
ROBLOX_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Origin": "https://www.roblox.com",
    "Referer": "https://www.roblox.com/",
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


async def get_csrf(session: aiohttp.ClientSession) -> str:
    async with session.post("https://auth.roblox.com/v2/signup", json={}) as resp:
        return resp.headers.get("x-csrf-token", "")


async def check_username(session: aiohttp.ClientSession, username: str, birthday: str) -> bool:
    url = "https://auth.roblox.com/v1/usernames/validate"
    params = {"username": username, "birthday": birthday, "context": "Signup"}
    try:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            return data.get("code") == 0
    except Exception:
        return False


async def signup_once(proxy: str) -> dict:
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(headers=ROBLOX_HEADERS, timeout=timeout) as session:
        # 1. Find an available username
        print("  [*] Finding username...")
        username = None
        birthday = generate_birthday()
        for _ in range(15):
            cand = generate_username()
            if await check_username(session, cand, birthday):
                username = cand
                break
        if not username:
            return {"success": False, "error": "No available username"}
        print(f"  [+] Username: {username}")

        password = generate_password()

        # 2. CSRF token
        csrf = await get_csrf(session)
        session.headers["x-csrf-token"] = csrf

        payload = {
            "username": username,
            "password": password,
            "birthday": birthday,
            "isTosAgreementBoxChecked": True,
            "agreementIds": [],
            "gender": random.randint(1, 2),
        }

        # 3. First signup attempt -> expect a challenge (403)
        print("  [*] Requesting challenge...")
        async with session.post("https://auth.roblox.com/v2/signup", json=payload) as resp:
            text = await resp.text()
            if resp.status == 200:
                data = json.loads(text)
                cookie = next((c.value for c in resp.cookies.values() if c.key == ".ROBLOSECURITY"), None)
                return {"success": True, "username": username, "password": password, "userId": data.get("userId"), "cookie": cookie}

            challenge_id = resp.headers.get("rblx-challenge-id")
            challenge_metadata_b64 = resp.headers.get("rblx-challenge-metadata")

            if not challenge_id or not challenge_metadata_b64:
                try:
                    err = json.loads(text)["errors"][0]["message"]
                except Exception:
                    err = text[:160]
                return {"success": False, "error": err}

        # 4. Decode challenge metadata -> blob + unifiedCaptchaId + actionType
        try:
            meta = json.loads(base64.b64decode(challenge_metadata_b64))
            print(f"  [debug] challenge meta: {meta}")
            blob = meta.get("dataExchangeBlob") or meta.get("blob")
            unified_captcha_id = meta.get("unifiedCaptchaId")
            action_type = meta.get("actionType") or "Generic"
        except Exception as e:
            return {"success": False, "error": f"Bad challenge metadata: {e}"}

        if USE_BLOB and not blob:
            return {"success": False, "error": "No blob in challenge metadata"}

        # 5. Solve FunCaptcha (optionally with the Roblox blob)
        data_arg = json.dumps({"blob": blob}) if (USE_BLOB and blob) else None
        print(f"  [*] Solving captcha (blob={'yes' if data_arg else 'no'})...")
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=200)) as fb_session:
            token = await fb.solve(
                fb_session,
                website_url="https://www.roblox.com/account/signupredir",
                website_public_key=ROBLOX_SIGNUP_KEY,
                website_subdomain="roblox-api",
                proxy=proxy,
                data=data_arg,
            )
        print("  [+] Captcha solved!")

        # 6. Continue the challenge with the solved token (reuse actionType from Roblox)
        solved_meta = json.dumps({
            "unifiedCaptchaId": unified_captcha_id,
            "captchaToken": token,
            "actionType": action_type,
        })
        continue_meta_b64 = base64.b64encode(solved_meta.encode()).decode()

        async with session.post("https://apis.roblox.com/challenge/v1/continue", json={
            "challengeId": challenge_id,
            "challengeType": "captcha",
            "challengeMetadata": solved_meta,
        }) as cont_resp:
            cont_text = await cont_resp.text()
            print(f"  [debug] continue ({cont_resp.status}): {cont_text[:160]}")

        # 7. Re-submit signup with challenge headers
        csrf = await get_csrf(session)
        session.headers["x-csrf-token"] = csrf
        session.headers["rblx-challenge-id"] = challenge_id
        session.headers["rblx-challenge-type"] = "captcha"
        session.headers["rblx-challenge-metadata"] = continue_meta_b64

        print("  [*] Finalizing signup...")
        async with session.post("https://auth.roblox.com/v2/signup", json=payload) as resp:
            text = await resp.text()
            if resp.status == 200:
                data = json.loads(text)
                cookie = next((c.value for c in resp.cookies.values() if c.key == ".ROBLOSECURITY"), None)
                return {"success": True, "username": username, "password": password, "userId": data.get("userId"), "cookie": cookie}

            try:
                err = json.loads(text)["errors"][0]["message"]
            except Exception:
                err = text[:160]
            return {"success": False, "error": err}


async def signup(proxy_pool) -> dict:
    """Try signup, rotating proxies if the captcha solve fails."""
    last_err = "unknown"
    for attempt in range(4):
        proxy = random.choice(proxy_pool)
        try:
            result = await signup_once(proxy)
            if result.get("success"):
                return result
            last_err = result.get("error", "unknown")
            # If it's a username/non-captcha error, no point rotating proxy
            if "captcha" not in last_err.lower() and "blob" not in last_err.lower() and "challenge" not in last_err.lower():
                return result
            print(f"  [*] Attempt {attempt+1}/4 failed ({last_err}), rotating proxy...")
        except Exception as e:
            last_err = str(e)
            print(f"  [*] Attempt {attempt+1}/4 error ({last_err}), rotating proxy...")
        await asyncio.sleep(1)
    return {"success": False, "error": last_err}


async def main():
    print("=" * 50)
    print("Roblox Account Generator")
    print("=" * 50)
    print(f"Loaded {len(PROXIES)} proxies")

    # Balance check
    try:
        async with aiohttp.ClientSession() as s:
            bal = await fb.get_balance(s)
            print(f"[+] FunBypass balance: ${bal}")
    except Exception as e:
        print(f"[!] Balance check failed: {e} (continuing)")

    try:
        count = int(input("\nHow many accounts? "))
    except Exception:
        count = 1

    success = 0
    for i in range(count):
        print(f"\n[{i+1}/{count}] Creating account...")
        result = await signup(PROXIES)

        if result.get("success"):
            combo = f"{result['username']}:{result['password']}"
            print(f"[+] SUCCESS: {combo}")
            with open(OUTPUT_FILE, "a") as f:
                f.write(combo + "\n")
            success += 1
        else:
            print(f"[-] FAILED: {result.get('error')}")

        if i < count - 1:
            await asyncio.sleep(2)

    print(f"\n{'=' * 50}")
    print(f"Done! {success}/{count} created")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
