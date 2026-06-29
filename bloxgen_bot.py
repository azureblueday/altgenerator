import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import time
import random
import string
from datetime import datetime, timedelta
from typing import Optional

# Try to import config, fallback to defaults if not found
try:
    from config import (
        BOT_TOKEN,
        BLOXGEN_API_KEY,
        FUNBYPASS_API_KEY,
        PREMIUM_ROLE_NAME,
        PREMIUM_COOLDOWN,
        NORMAL_COOLDOWN,
        PREMIUM_DAILY_LIMIT,
        NORMAL_DAILY_LIMIT,
        COMMAND_PREFIX,
        ADMIN_ROLE_NAME,
    )
except ImportError:
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    BLOXGEN_API_KEY = "BLOX-XXXXXXXXXXXXXXXX"
    FUNBYPASS_API_KEY = "FUN-XXXXXXXXXXXXXXXX"
    PREMIUM_ROLE_NAME = "Premium"
    PREMIUM_COOLDOWN = 30
    NORMAL_COOLDOWN = 3600
    PREMIUM_DAILY_LIMIT = 50
    NORMAL_DAILY_LIMIT = 10
    COMMAND_PREFIX = "!"
    ADMIN_ROLE_NAME = "Admin"

# API Configuration
BLOXGEN_BASE_URL = "https://core.bloxgen.net"
FUNBYPASS_BASE_URL = "https://api.funbypass.com"
ROBLOX_SIGNUP_URL = "https://auth.roblox.com/v2/signup"
ROBLOX_CAPTCHA_KEY = "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"

# Account type choices for the generate command
ACCOUNT_TYPES = [
    app_commands.Choice(name="Alt (Basic)", value="alt"),
    app_commands.Choice(name="30+ Days Old", value="+30 days old"),
    app_commands.Choice(name="1+ Year Old", value="+1 year old"),
    app_commands.Choice(name="5+ Years Old", value="5+ years old"),
    app_commands.Choice(name="Dump (Verified)", value="dump"),
    app_commands.Choice(name="Dump (Unchecked)", value="dump (unchecked)"),
]

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Tracking dictionaries
user_cooldowns = {}
user_daily_counts = {}


class BloxgenAPI:
    """Async wrapper for the Bloxgen API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = BLOXGEN_BASE_URL

    async def generate_account(self, account_type: str) -> dict:
        """Generate a Roblox account of the specified type"""
        url = f"{self.base_url}/api/generate"
        payload = {"apiKey": self.api_key, "type": account_type}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                data['status_code'] = response.status
                return data

    async def get_balance(self) -> dict:
        """Get the current account balance"""
        url = f"{self.base_url}/api/balance"
        params = {"apiKey": self.api_key}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                data['status_code'] = response.status
                return data

    async def health_check(self) -> dict:
        """Check API server status"""
        url = f"{self.base_url}/health"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                data['status_code'] = response.status
                return data


class FunbypassAPI:
    """Async wrapper for the Funbypass captcha solving API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = FUNBYPASS_BASE_URL

    async def create_task(self, blob: str = None, proxy: str = None) -> dict:
        """Create a FunCaptcha solving task"""
        url = f"{self.base_url}/createTask"

        task = {
            "type": "FunCaptchaTask",
            "websiteURL": "https://www.roblox.com/account/signupredir",
            "websitePublicKey": ROBLOX_CAPTCHA_KEY,
            "websiteSubdomain": "roblox-api",
        }

        if blob:
            task["data"] = blob
        if proxy:
            task["proxy"] = proxy

        payload = {"clientKey": self.api_key, "task": task}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()

    async def get_task_result(self, task_id: str) -> dict:
        """Get the result of a captcha solving task"""
        url = f"{self.base_url}/getTaskResult/{task_id}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    async def solve_captcha(self, blob: str = None, proxy: str = None, timeout: int = 120) -> dict:
        """Create task and poll until solved or timeout"""
        create_result = await self.create_task(blob, proxy)

        if create_result.get('errorId') != 0:
            return {
                'success': False,
                'error': create_result.get('errorCode', 'UNKNOWN_ERROR'),
                'message': create_result.get('errorDescription', 'Failed to create task')
            }

        task_id = create_result.get('taskId')
        start_time = time.time()

        while time.time() - start_time < timeout:
            await asyncio.sleep(1)
            result = await self.get_task_result(task_id)

            status = result.get('status')
            if status == 'ready':
                token = result.get('solution', {}).get('token')
                return {'success': True, 'token': token}
            elif status == 'failure' or result.get('errorId') == 1:
                return {
                    'success': False,
                    'error': result.get('errorCode', 'SOLVE_FAILED'),
                    'message': result.get('errorDescription', 'Captcha solve failed')
                }

        return {'success': False, 'error': 'TIMEOUT', 'message': 'Captcha solving timed out'}


class RobloxSignup:
    """Handle Roblox account signup"""

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

    def __init__(self, funbypass: FunbypassAPI):
        self.funbypass = funbypass
        self.csrf_token = None

    def generate_username(self) -> str:
        """Generate a human-like username"""
        style = random.randint(1, 5)

        if style == 1:
            adj = random.choice(self.ADJECTIVES)
            noun = random.choice(self.NOUNS)
            num = random.randint(1, 999)
            return f"{adj}{noun}{num}"
        elif style == 2:
            name = random.choice(self.NAMES)
            noun = random.choice(self.NOUNS)
            num = random.randint(0, 99)
            return f"{name}{noun}{num}" if num > 0 else f"{name}{noun}"
        elif style == 3:
            name = random.choice(self.NAMES)
            num = random.randint(100, 9999)
            suffix = random.choice(["_", "x", "X", ""])
            return f"{name}{suffix}{num}"
        elif style == 4:
            adj = random.choice(self.ADJECTIVES)
            name = random.choice(self.NAMES)
            num = random.randint(1, 99)
            return f"{adj}{name}{num}"
        else:
            noun1 = random.choice(self.NOUNS)
            noun2 = random.choice(self.NOUNS)
            num = random.randint(1, 99)
            sep = random.choice(["_", "", "x"])
            return f"{noun1}{sep}{noun2}{num}"

    def generate_password(self) -> str:
        """Generate a 10 character alphanumeric password"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=10))

    def generate_birthday(self) -> str:
        """Generate a random birthday (18-25 years old)"""
        current_year = datetime.now().year
        year = random.randint(current_year - 25, current_year - 18)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        return f"{year}-{month:02d}-{day:02d}T00:00:00.000Z"

    async def get_csrf_token(self, session: aiohttp.ClientSession) -> str:
        """Get CSRF token from Roblox"""
        url = "https://auth.roblox.com/v2/signup"
        try:
            async with session.post(url, json={}) as response:
                return response.headers.get('x-csrf-token', '')
        except:
            return ''

    async def signup(self, username: str = None, password: str = None, proxy: str = None) -> dict:
        """Create a new Roblox account"""
        username = username or self.generate_username()
        password = password or self.generate_password()
        birthday = self.generate_birthday()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://www.roblox.com",
            "Referer": "https://www.roblox.com/",
        }

        connector = None
        if proxy:
            connector = aiohttp.TCPConnector()

        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            csrf_token = await self.get_csrf_token(session)
            if csrf_token:
                session.headers.update({"x-csrf-token": csrf_token})

            signup_payload = {
                "username": username,
                "password": password,
                "birthday": birthday,
                "gender": random.randint(1, 2),
                "isTosAgreementBoxChecked": True,
                "agreementIds": [],
            }

            async with session.post(ROBLOX_SIGNUP_URL, json=signup_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    cookie = response.cookies.get('.ROBLOSECURITY')
                    return {
                        'success': True,
                        'username': username,
                        'password': password,
                        'userId': data.get('userId'),
                        'cookie': str(cookie) if cookie else None,
                    }

                data = await response.json()
                errors = data.get('errors', [])

                if any(e.get('code') == 2 for e in errors):
                    captcha_result = await self.funbypass.solve_captcha(proxy=proxy)
                    if not captcha_result.get('success'):
                        return {
                            'success': False,
                            'error': 'CAPTCHA_FAILED',
                            'message': captcha_result.get('message', 'Failed to solve captcha'),
                        }

                    captcha_token = captcha_result.get('token')
                    signup_payload['captchaToken'] = captcha_token
                    signup_payload['captchaProvider'] = 'PROVIDER_ARKOSE_LABS'

                    new_csrf = await self.get_csrf_token(session)
                    if new_csrf:
                        session.headers.update({"x-csrf-token": new_csrf})

                    async with session.post(ROBLOX_SIGNUP_URL, json=signup_payload) as retry_response:
                        if retry_response.status == 200:
                            retry_data = await retry_response.json()
                            cookie = retry_response.cookies.get('.ROBLOSECURITY')
                            return {
                                'success': True,
                                'username': username,
                                'password': password,
                                'userId': retry_data.get('userId'),
                                'cookie': str(cookie) if cookie else None,
                            }
                        else:
                            retry_data = await retry_response.json()
                            return {
                                'success': False,
                                'error': 'SIGNUP_FAILED',
                                'message': str(retry_data.get('errors', [{'message': 'Unknown error'}])[0].get('message')),
                            }

                first_error = errors[0] if errors else {'message': 'Unknown error'}
                return {
                    'success': False,
                    'error': 'SIGNUP_FAILED',
                    'message': first_error.get('message', 'Unknown error'),
                }


# Initialize API clients
bloxgen = BloxgenAPI(BLOXGEN_API_KEY)
funbypass = FunbypassAPI(FUNBYPASS_API_KEY)
roblox_signup = RobloxSignup(funbypass)


def has_premium_role(member: discord.Member) -> bool:
    return discord.utils.get(member.roles, name=PREMIUM_ROLE_NAME) is not None


def has_admin_role(member: discord.Member) -> bool:
    return discord.utils.get(member.roles, name=ADMIN_ROLE_NAME) is not None


def check_and_update_daily_limit(user_id: int, is_premium: bool) -> tuple[bool, int, int]:
    now = datetime.now()

    if user_id not in user_daily_counts:
        user_daily_counts[user_id] = {'count': 0, 'reset_time': now + timedelta(days=1)}

    user_data = user_daily_counts[user_id]

    if now >= user_data['reset_time']:
        user_data['count'] = 0
        user_data['reset_time'] = now + timedelta(days=1)

    limit = PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT
    if user_data['count'] >= limit:
        time_until_reset = user_data['reset_time'] - now
        hours = int(time_until_reset.total_seconds() // 3600)
        minutes = int((time_until_reset.total_seconds() % 3600) // 60)
        return False, hours, minutes

    user_data['count'] += 1
    return True, 0, 0


def check_and_update_cooldown(user_id: int, is_premium: bool) -> tuple[bool, int]:
    now = time.time()
    cooldown = PREMIUM_COOLDOWN if is_premium else NORMAL_COOLDOWN

    if user_id in user_cooldowns:
        time_passed = now - user_cooldowns[user_id]
        if time_passed < cooldown:
            return False, int(cooldown - time_passed)

    user_cooldowns[user_id] = now
    return True, 0


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('Bloxgen Bot is ready!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')


@bot.tree.command(name="generate", description="Generate a Roblox account using Bloxgen API")
@app_commands.describe(account_type="The type of account to generate")
@app_commands.choices(account_type=ACCOUNT_TYPES)
async def generate(interaction: discord.Interaction, account_type: app_commands.Choice[str]):
    """Generate a Roblox account with role-based rate limiting"""
    user_id = interaction.user.id
    is_premium = has_premium_role(interaction.user)

    within_limit, hours, minutes = check_and_update_daily_limit(user_id, is_premium)
    if not within_limit:
        limit = PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT
        embed = discord.Embed(
            title="Daily Limit Reached",
            description=f"You've reached your daily limit of **{limit} generations**.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reset Time", value=f"Resets in **{hours}h {minutes}m**", inline=False)
        if not is_premium:
            embed.add_field(
                name="Want More?",
                value=f"Get the **{PREMIUM_ROLE_NAME}** role for {PREMIUM_DAILY_LIMIT} generations/day!",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    can_use, remaining = check_and_update_cooldown(user_id, is_premium)
    if not can_use:
        mins, secs = remaining // 60, remaining % 60
        embed = discord.Embed(
            title="Cooldown Active",
            description="Please wait before using this command again.",
            color=discord.Color.orange()
        )
        time_str = f"**{mins}m {secs}s**" if mins > 0 else f"**{secs}s**"
        embed.add_field(name="Time Remaining", value=time_str, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        result = await bloxgen.generate_account(account_type.value)
    except Exception as e:
        user_daily_counts[user_id]['count'] -= 1
        embed = discord.Embed(title="API Error", description=f"Failed to connect: {str(e)}", color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    if result.get('success'):
        data = result.get('data', {})
        embed = discord.Embed(
            title="Account Generated",
            description=f"Successfully generated a **{account_type.name}** account!",
            color=discord.Color.green()
        )
        embed.add_field(name="Username", value=f"```{data.get('username', 'N/A')}```", inline=True)
        embed.add_field(name="Password", value=f"```{data.get('password', 'N/A')}```", inline=True)
        embed.add_field(name="Combo", value=f"```{data.get('username')}:{data.get('password')}```", inline=False)

        cookie = data.get('cookie', '')
        if cookie:
            truncated = cookie[:50] + "..." if len(cookie) > 50 else cookie
            embed.add_field(name="Cookie", value=f"```{truncated}```", inline=False)

        avatar_url = data.get('avatarUrl') or data.get('avatar_url')
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        cost = data.get('cost', 0)
        embed.add_field(name="Cost", value=f"${cost:.4f}", inline=True)

        user_data = user_daily_counts[user_id]
        limit = PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT
        remaining_today = limit - user_data['count']
        embed.set_footer(text=f"Remaining today: {remaining_today}/{limit}")

        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        user_daily_counts[user_id]['count'] -= 1
        message = result.get('message', 'Unknown error occurred')
        embed = discord.Embed(title="Generation Failed", description=message, color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="signup", description="Create a fresh Roblox account with captcha solving")
@app_commands.describe(username="Custom username (optional)", password="Custom password (optional)")
async def signup(interaction: discord.Interaction, username: str = None, password: str = None):
    """Create a new Roblox account using Funbypass for captcha solving"""
    user_id = interaction.user.id
    is_premium = has_premium_role(interaction.user)

    within_limit, hours, minutes = check_and_update_daily_limit(user_id, is_premium)
    if not within_limit:
        limit = PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT
        embed = discord.Embed(
            title="Daily Limit Reached",
            description=f"You've reached your daily limit of **{limit} generations**.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reset Time", value=f"Resets in **{hours}h {minutes}m**", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    can_use, remaining = check_and_update_cooldown(user_id, is_premium)
    if not can_use:
        mins, secs = remaining // 60, remaining % 60
        embed = discord.Embed(
            title="Cooldown Active",
            description="Please wait before using this command again.",
            color=discord.Color.orange()
        )
        time_str = f"**{mins}m {secs}s**" if mins > 0 else f"**{secs}s**"
        embed.add_field(name="Time Remaining", value=time_str, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    status_embed = discord.Embed(
        title="Creating Account...",
        description="Solving captcha and registering account. This may take up to 2 minutes.",
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=status_embed, ephemeral=True)

    try:
        result = await roblox_signup.signup(username=username, password=password)
    except Exception as e:
        user_daily_counts[user_id]['count'] -= 1
        embed = discord.Embed(title="Signup Error", description=f"Failed: {str(e)}", color=discord.Color.red())
        await interaction.edit_original_response(embed=embed)
        return

    if result.get('success'):
        embed = discord.Embed(
            title="Account Created",
            description="Successfully created a new Roblox account!",
            color=discord.Color.green()
        )
        embed.add_field(name="Username", value=f"```{result.get('username')}```", inline=True)
        embed.add_field(name="Password", value=f"```{result.get('password')}```", inline=True)
        embed.add_field(name="Combo", value=f"```{result.get('username')}:{result.get('password')}```", inline=False)
        embed.add_field(name="User ID", value=f"`{result.get('userId')}`", inline=True)

        cookie = result.get('cookie')
        if cookie:
            truncated = cookie[:50] + "..." if len(cookie) > 50 else cookie
            embed.add_field(name="Cookie", value=f"```{truncated}```", inline=False)

        user_data = user_daily_counts[user_id]
        limit = PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT
        remaining_today = limit - user_data['count']
        embed.set_footer(text=f"Remaining today: {remaining_today}/{limit}")

        await interaction.edit_original_response(embed=embed)
    else:
        user_daily_counts[user_id]['count'] -= 1
        error = result.get('error', 'UNKNOWN')
        message = result.get('message', 'Unknown error occurred')
        embed = discord.Embed(
            title="Signup Failed",
            description=f"**Error:** {error}\n**Details:** {message}",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=embed)


@bot.tree.command(name="balance", description="Check the Bloxgen API balance")
async def balance(interaction: discord.Interaction):
    """Check the current API balance (Admin only)"""
    if not has_admin_role(interaction.user) and not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="Permission Denied",
            description=f"You need the **{ADMIN_ROLE_NAME}** role to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        result = await bloxgen.get_balance()
    except Exception as e:
        embed = discord.Embed(title="API Error", description=f"Failed to connect: {str(e)}", color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    if result.get('success'):
        balance_amount = result.get('balance', 0)
        color = discord.Color.green() if balance_amount >= 10 else (discord.Color.orange() if balance_amount >= 1 else discord.Color.red())
        status = "Healthy" if balance_amount >= 10 else ("Low" if balance_amount >= 1 else "Critical")

        embed = discord.Embed(title="Bloxgen API Balance", color=color)
        embed.add_field(name="Balance", value=f"**${balance_amount:.2f}**", inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        message = result.get('message', 'Failed to retrieve balance')
        embed = discord.Embed(title="Balance Check Failed", description=message, color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="health", description="Check Bloxgen API server status")
async def health(interaction: discord.Interaction):
    """Check the API health status"""
    await interaction.response.defer(ephemeral=True)

    try:
        result = await bloxgen.health_check()
    except Exception as e:
        embed = discord.Embed(title="API Health Check", description="Failed to connect", color=discord.Color.red())
        embed.add_field(name="Error", value=str(e), inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    status = result.get('status', 'unknown')
    mongodb = result.get('mongodb', 'unknown')
    redis = result.get('redis', 'unknown')

    color = discord.Color.green() if status == 'healthy' else discord.Color.red()
    status_text = "Online" if status == 'healthy' else "Degraded"

    embed = discord.Embed(title="Bloxgen API Health", description=f"**Status:** {status_text}", color=color)
    embed.add_field(name="MongoDB", value="Connected" if mongodb == 'connected' else "Disconnected", inline=True)
    embed.add_field(name="Redis", value="Connected" if redis == 'connected' else "Disconnected", inline=True)

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="stats", description="View your generation statistics")
async def stats(interaction: discord.Interaction):
    """View user's generation statistics"""
    user_id = interaction.user.id
    is_premium = has_premium_role(interaction.user)

    limit = PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT
    cooldown = PREMIUM_COOLDOWN if is_premium else NORMAL_COOLDOWN

    if user_id in user_daily_counts:
        user_data = user_daily_counts[user_id]
        used_today = user_data['count']
        time_until_reset = user_data['reset_time'] - datetime.now()
        hours = int(time_until_reset.total_seconds() // 3600)
        minutes = int((time_until_reset.total_seconds() % 3600) // 60)
        reset_str = f"{hours}h {minutes}m"
    else:
        used_today = 0
        reset_str = "24h"

    remaining = limit - used_today

    if user_id in user_cooldowns:
        time_passed = time.time() - user_cooldowns[user_id]
        if time_passed < cooldown:
            cooldown_remaining = int(cooldown - time_passed)
            cooldown_str = f"{cooldown_remaining // 60}m {cooldown_remaining % 60}s" if cooldown_remaining >= 60 else f"{cooldown_remaining}s"
        else:
            cooldown_str = "Ready"
    else:
        cooldown_str = "Ready"

    embed = discord.Embed(title="Your Generation Stats", color=discord.Color.blue())
    embed.add_field(name="Tier", value="Premium" if is_premium else "Standard", inline=True)
    embed.add_field(name="Daily Limit", value=f"{limit}/day", inline=True)
    embed.add_field(name="Cooldown", value=f"{cooldown}s", inline=True)
    embed.add_field(name="Used Today", value=f"{used_today}/{limit}", inline=True)
    embed.add_field(name="Remaining", value=str(remaining), inline=True)
    embed.add_field(name="Resets In", value=reset_str, inline=True)
    embed.add_field(name="Cooldown Status", value=cooldown_str, inline=False)

    if not is_premium:
        embed.add_field(
            name="Upgrade to Premium",
            value=f"Get the **{PREMIUM_ROLE_NAME}** role for more generations!",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="types", description="View available account types")
async def types(interaction: discord.Interaction):
    """List all available account types"""
    embed = discord.Embed(
        title="Available Account Types",
        description="Use `/generate` for pre-made accounts or `/signup` for fresh accounts:",
        color=discord.Color.blue()
    )

    type_descriptions = {
        "Alt (Basic)": "Standard fresh Roblox accounts",
        "30+ Days Old": "Accounts aged at least 30 days",
        "1+ Year Old": "Accounts aged at least 1 year",
        "5+ Years Old": "Accounts aged 5 or more years",
        "Dump (Verified)": "Premium verified accounts",
        "Dump (Unchecked)": "Unverified premium accounts",
    }

    for name, desc in type_descriptions.items():
        embed.add_field(name=name, value=desc, inline=False)

    embed.add_field(name="Fresh Signup", value="Use `/signup` to create a brand new account with captcha solving", inline=False)
    embed.set_footer(text="Pricing and availability varies by type")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="help", description="Get help with Bloxgen Bot commands")
async def help_command(interaction: discord.Interaction):
    """Display help information"""
    embed = discord.Embed(
        title="Bloxgen Bot Help",
        description="Generate Roblox accounts using Bloxgen API and Funbypass",
        color=discord.Color.blue()
    )

    commands_info = [
        ("`/generate`", "Generate a pre-made account (choose type from dropdown)"),
        ("`/signup`", "Create a fresh Roblox account with captcha solving"),
        ("`/types`", "View all available account types"),
        ("`/stats`", "View your generation statistics"),
        ("`/health`", "Check API server status"),
        ("`/balance`", "Check API balance (Admin only)"),
        ("`/help`", "Show this help message"),
    ]

    for cmd, desc in commands_info:
        embed.add_field(name=cmd, value=desc, inline=False)

    is_premium = has_premium_role(interaction.user)
    tier_info = f"**Your Tier:** {'Premium' if is_premium else 'Standard'}\n"
    tier_info += f"**Daily Limit:** {PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT}/day\n"
    tier_info += f"**Cooldown:** {PREMIUM_COOLDOWN if is_premium else NORMAL_COOLDOWN}s"
    embed.add_field(name="Your Status", value=tier_info, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


if __name__ == '__main__':
    bot.run(BOT_TOKEN)
