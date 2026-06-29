from threading import Lock

from generate_counter import GenerateCounter
from output import Output
from roblox_profile import RobloxProfile
from session import Session
from auth_intent import AuthIntent
from util import Util
from custom_solver import get_token
from json import loads, dumps
from base64 import b64encode, b64decode
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

LOCK = Lock()


class Generate:
    @staticmethod
    def gen(generate_counter: GenerateCounter) -> None:
        while True:
            try:
                username, password = RobloxProfile.get_username(), RobloxProfile.get_password()
                birthday, gender = RobloxProfile.get_birth_day(), RobloxProfile.get_gender()

                Output("INFO").log(f"Generating account {username}")

                session = Session.session()

                resp = session.get("https://www.roblox.com/")

                cookie_header = '; '.join(
                    [f"{key}={value}" for key, value in resp.cookies.items()])
                if resp.status_code == 429:
                    raise ValueError("Rate limited")

                session.headers = Session.set_image_request_headers(
                    session.headers)
                session.headers = Util.sort_dict_order(session.headers)

                session.get("https://www.roblox.com/timg/rbx")

                if resp.status_code == 429:
                    raise ValueError("Rate limited")

                if 'data-token=' in resp.text:
                    session.headers = {
                        **session.headers,
                        "x-csrf-token": resp.text.split('data-token="')[1].split('"')[0]
                    }

                session.headers = Session.set_api_request_headers(
                    session.headers)
                session.headers = Util.sort_dict_order(session.headers)

                payload = {
                    'username': username,
                    'context': 'Signup',
                    'birthday': birthday,
                }

                resp = session.post(
                    "https://auth.roblox.com/v1/usernames/validate", json=payload)

                if resp.status_code == 429:
                    raise ValueError("Rate limited")

                while resp.status_code != 200 or resp.json()["code"] != 0:
                    username = RobloxProfile.get_username()
                    payload["username"] = username

                    resp = session.post(
                        "https://auth.roblox.com/v1/usernames/validate", json=payload)

                    csrf = resp.headers.get("x-csrf-token")

                    if csrf:
                        session.headers = {
                            **session.headers,
                            "x-csrf-token": csrf
                        }

                    if resp.status_code == 429:
                        raise ValueError("Rate limited")

                payload = {
                    'username': username,
                    'password': password
                }

                session.post(
                    "https://auth.roblox.com/v2/passwords/validate", json=payload)

                if resp.status_code == 429:
                    raise ValueError("Rate limited")

                auth_intent = AuthIntent.get_auth_intent(session)

                signup_payload = {"username": username, "password": password, "birthday": birthday, "gender": 1, "isTosAgreementBoxChecked": True, "agreementIds": ["306cc852-3717-4996-93e7-086daafd42f6", "2ba6b930-4ba8-4085-9e8c-24b919701f15"], "auditSystemContent": {
                    "capturedAuditContent": {"Authentication.SignUp.Label.Birthday": {"translationKey": "Label.Birthday", "translationNamespace": "Authentication.SignUp.Label.Birthday", "translatedSourceString": "Birthday"}, "Authentication.SignUp.Label.Username": {"translationKey": "Label.Username", "translationNamespace": "Authentication.SignUp.Label.Username", "translatedSourceString": "Username"}, "Authentication.SignUp.Label.Password": {"translationKey": "Label.Password", "translationNamespace": "Authentication.SignUp.Label.Password", "translatedSourceString": "Password"}, "Authentication.SignUp.Label.OptionalGender": {"translationKey": "Label.OptionalGender", "translationNamespace": "Authentication.SignUp.Label.OptionalGender", "translatedSourceString": "Gender (optional)"}, "Authentication.SignUp.Description.SignUpAgreement.FullCopy": {"translationKey": "Description.SignUpAgreement.FullCopy", "translationNamespace": "Authentication.SignUp.Description.SignUpAgreement.FullCopy", "translatedSourceString": "By clicking Sign Up, you are agreeing to our {termsOfUseLink} (including arbitration) and acknowledge our {privacyPolicyLink}. If you are under 18, you agree that your parent/guardian permits you to create this account and agrees to our Terms of Use.", "parameters": {"termsOfUseLink": "<a target=\"_blank\" href=\"https://www.roblox.com/info/terms\">Terms of Use</a>", "privacyPolicyLink": "<a target=\"_blank\" href=\"https://www.roblox.com/info/privacy\">Privacy Policy</a>"}}}, "additionalAuditContent": {}}, "secureAuthenticationIntent": auth_intent}

                resp = session.post(
                    "https://auth.roblox.com/v2/signup", json=signup_payload)

                if resp.status_code == 429:
                    raise ValueError("Rate limited")
                challenge_id = resp.headers.get("rblx-challenge-id")
                metadata = loads(b64decode(resp.headers.get(
                    "rblx-challenge-metadata").encode("utf-8")).decode("utf-8"))
                blob = metadata.get("dataExchangeBlob")
                captcha_id = metadata.get("unifiedCaptchaId")

                Output("CAPTCHA").log("Solving captcha")

                solution = get_token(
                    session, blob, session.proxy, cookie_header)

                if solution == None:
                    raise ValueError("Failed to solve captcha")

                token = solution.split("|")[0]
                token_info = solution.split(
                    "pk=A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F|")[1].split("|cdn_url=")[0]

                Output("CAPTCHA").log(f"Solved captcha | {token}|{token_info}")

                challenge_metadata = dumps({
                    "unifiedCaptchaId": captcha_id,
                    "captchaToken": solution,
                    "actionType": "Signup"
                }, separators=(',', ':'))

                payload = dumps({
                    "challengeId": challenge_id,
                    "challengeType": "captcha",
                    "challengeMetadata": challenge_metadata
                }, separators=(',', ':'))

                resp = session.post(
                    "https://apis.roblox.com/challenge/v1/continue", content=payload.encode("utf-8"))

                if resp.status_code != 200:
                    raise ValueError("Rejected by continue API")

                session.headers = {
                    **session.headers,
                    "rblx-challenge-id": challenge_id,
                    "rblx-challenge-metadata": b64encode(challenge_metadata.encode("utf-8")).decode("utf-8"),
                    "rblx-challenge-type": "captcha"
                }

                session.headers = Util.sort_dict_order(session.headers)

                resp = session.post(
                    "https://auth.roblox.com/v2/signup", json=signup_payload)

                if resp.status_code != 200:
                    raise ValueError("Rejected by signup API")

                session.headers = Session.set_page_request_headers(
                    session.headers)
                session.headers = Util.sort_dict_order(session.headers)

                session.get("https://www.roblox.com/home?nu=true")

                generate_counter.increase_generated()

                Output("SUCCESS").log(
                    f"Successfully generated account | {username}")

                account_cookie = resp.cookies['.ROBLOSECURITY']

                with LOCK:
                    with open("output/accounts.txt", "a", encoding="utf-8") as file:
                        file.write(f"{username}:{password}:{account_cookie}\n")
                    with open("output/cookies.txt", "a", encoding="utf-8") as file:
                        file.write(f"{account_cookie}\n")

            except Exception as e:
                if "Failed to perform" in str(e):
                    Output("ERROR").log("Error | Proxy failed to make request")
                else:
                    Output("ERROR").log(f"Error | {str(e)}")
