import discord
from discord.ext import commands
from discord import app_commands
import re
import time
from datetime import datetime, timedelta
from collections import defaultdict
import os
import random

# Try to import config, fallback to defaults if not found
try:
    from config import (
        BOT_TOKEN as TOKEN,
        PREMIUM_ROLE_NAME,
        PREMIUM_COOLDOWN,
        NORMAL_COOLDOWN,
        PREMIUM_DAILY_LIMIT,
        NORMAL_DAILY_LIMIT,
        COMMAND_PREFIX,
        AUTO_DELETE_FORMATTED,
        RESTOCK_ROLE_NAME
    )
except ImportError:
    # Fallback defaults if config.py doesn't exist
    TOKEN = "YOUR_BOT_TOKEN_HERE"
    PREMIUM_ROLE_NAME = "Premium"
    PREMIUM_COOLDOWN = 30
    NORMAL_COOLDOWN = 3600
    PREMIUM_DAILY_LIMIT = 50
    NORMAL_DAILY_LIMIT = 10
    COMMAND_PREFIX = "!"
    AUTO_DELETE_FORMATTED = False
    RESTOCK_ROLE_NAME = "Restock"

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Tracking dictionaries
user_cooldowns = {}  # {user_id: timestamp}
user_daily_counts = {}  # {user_id: {'count': int, 'reset_time': datetime}}

# Account storage configuration
ACCOUNTS_FILE = "accounts.txt"

# Account management functions
def load_accounts():
    """Load accounts from file"""
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    
    with open(ACCOUNTS_FILE, 'r') as f:
        accounts = [line.strip() for line in f if line.strip() and ':' in line]
    return accounts

def save_accounts(accounts):
    """Save accounts to file"""
    with open(ACCOUNTS_FILE, 'w') as f:
        f.write('\n'.join(accounts))

def get_random_account():
    """Get and remove a random account from the file"""
    accounts = load_accounts()
    
    if not accounts:
        return None, None, None
    
    # Get random account
    account = random.choice(accounts)
    username, password = account.split(':', 1)
    combo = account
    
    # Remove used account
    accounts.remove(account)
    save_accounts(accounts)
    
    return username, password, combo

def add_accounts(accounts_list):
    """Add multiple accounts to the file"""
    existing = load_accounts()
    existing.extend(accounts_list)
    save_accounts(existing)
    return len(accounts_list)

def get_account_count():
    """Get total number of available accounts"""
    return len(load_accounts())

def has_restock_role(member):
    """Check if user has the restock role"""
    return discord.utils.get(member.roles, name=RESTOCK_ROLE_NAME) is not None


def has_premium_role(member):
    """Check if user has the premium role"""
    return discord.utils.get(member.roles, name=PREMIUM_ROLE_NAME) is not None

def check_and_update_daily_limit(user_id, is_premium):
    """Check if user is within daily limit and update count"""
    now = datetime.now()
    
    # Initialize or reset daily count
    if user_id not in user_daily_counts:
        user_daily_counts[user_id] = {
            'count': 0,
            'reset_time': now + timedelta(days=1)
        }
    
    user_data = user_daily_counts[user_id]
    
    # Reset if past reset time
    if now >= user_data['reset_time']:
        user_data['count'] = 0
        user_data['reset_time'] = now + timedelta(days=1)
    
    # Check limit
    limit = PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT
    if user_data['count'] >= limit:
        time_until_reset = user_data['reset_time'] - now
        hours = int(time_until_reset.total_seconds() // 3600)
        minutes = int((time_until_reset.total_seconds() % 3600) // 60)
        return False, hours, minutes
    
    # Increment count
    user_data['count'] += 1
    return True, 0, 0

def check_and_update_cooldown(user_id, is_premium):
    """Check if user is on cooldown and update last used time"""
    now = time.time()
    cooldown = PREMIUM_COOLDOWN if is_premium else NORMAL_COOLDOWN
    
    if user_id in user_cooldowns:
        time_passed = now - user_cooldowns[user_id]
        if time_passed < cooldown:
            remaining = cooldown - time_passed
            return False, int(remaining)
    
    user_cooldowns[user_id] = now
    return True, 0

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('Bot is ready to format messages!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

@bot.tree.command(name="generate", description="Generate account credentials")
async def generate(interaction: discord.Interaction):
    """Generate command with role-based rate limiting"""
    user_id = interaction.user.id
    is_premium = has_premium_role(interaction.user)
    
    # Check daily limit
    within_limit, hours, minutes = check_and_update_daily_limit(user_id, is_premium)
    if not within_limit:
        limit = PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT
        embed = discord.Embed(
            title="❌ Daily Limit Reached",
            description=f"You've reached your daily limit of **{limit} generations**.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Reset Time",
            value=f"Resets in **{hours}h {minutes}m**",
            inline=False
        )
        if not is_premium:
            embed.add_field(
                name="💎 Want More?",
                value=f"Get the **{PREMIUM_ROLE_NAME}** role for:\n• 50 generations/day\n• 30s cooldown",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check cooldown
    can_use, remaining = check_and_update_cooldown(user_id, is_premium)
    if not can_use:
        minutes = remaining // 60
        seconds = remaining % 60
        embed = discord.Embed(
            title="⏳ Cooldown Active",
            description=f"Please wait before using this command again.",
            color=discord.Color.orange()
        )
        if minutes > 0:
            embed.add_field(
                name="Time Remaining",
                value=f"**{minutes}m {seconds}s**",
                inline=False
            )
        else:
            embed.add_field(
                name="Time Remaining",
                value=f"**{seconds}s**",
                inline=False
            )
        if not is_premium:
            embed.add_field(
                name="💎 Want Faster Access?",
                value=f"Get the **{PREMIUM_ROLE_NAME}** role for 30s cooldown!",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Get account from stock
    username, password, combo = get_random_account()
    
    # Check if accounts are available
    if not username:
        embed = discord.Embed(
            title="❌ No Accounts Available",
            description="The account stock is empty! Please wait for a restock.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="ℹ️ Info",
            value="Staff members can add accounts using `/restock`",
            inline=False
        )
        
        # Refund the user's daily count since no account was given
        user_daily_counts[user_id]['count'] -= 1
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Get user stats
    user_data = user_daily_counts[user_id]
    limit = PREMIUM_DAILY_LIMIT if is_premium else NORMAL_DAILY_LIMIT
    remaining_today = limit - user_data['count']
    
    # Create embed response
    embed = discord.Embed(
        title="✅ Account Generated",
        color=discord.Color.green()
    )
    embed.add_field(name="Username", value=f"`{username}`", inline=False)
    embed.add_field(name="Password", value=f"`{password}`", inline=False)
    embed.add_field(name="Combo", value=f"`{combo}`", inline=False)
    
    # Get remaining stock
    remaining_stock = get_account_count()
    
    # Add stats footer
    cooldown_time = "30 seconds" if is_premium else "60 minutes"
    embed.set_footer(text=f"Remaining today: {remaining_today}/{limit} | Stock: {remaining_stock} | Cooldown: {cooldown_time}")
    
    if is_premium:
        embed.set_author(name="💎 Premium Generation")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="restock", description="Add accounts to the stock (Staff only)")
async def restock(interaction: discord.Interaction, accounts: str):
    """Restock command - add accounts in username:password format"""
    
    # Check if user has restock role
    if not has_restock_role(interaction.user):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description=f"You need the **{RESTOCK_ROLE_NAME}** role to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Parse the accounts from the text
    # Support both formats:
    # 1. Simple: username:password (one per line)
    # 2. Formatted: Name\nusername\nPassword\npassword\nCombo\nusername:password
    
    lines = accounts.strip().split('\n')
    parsed_accounts = []
    
    # Try to extract accounts
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if it's a direct combo format (username:password)
        if ':' in line and not line.lower().startswith(('name', 'password', 'combo', 'username')):
            parsed_accounts.append(line)
            i += 1
        # Check if it's the formatted style
        elif line.lower() in ['name', 'username']:
            if i + 1 < len(lines):
                username = lines[i + 1].strip()
                # Look for password
                if i + 2 < len(lines) and lines[i + 2].strip().lower() == 'password':
                    if i + 3 < len(lines):
                        password = lines[i + 3].strip()
                        parsed_accounts.append(f"{username}:{password}")
                        i += 4  # Skip to next account
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
        else:
            i += 1
    
    if not parsed_accounts:
        embed = discord.Embed(
            title="❌ No Valid Accounts Found",
            description="Could not parse any accounts from your input.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Supported Formats",
            value="**Simple:**\n```username:password\nusername2:password2```\n**Formatted:**\n```Name\nusername\nPassword\npassword\nCombo\nusername:password```",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Add accounts to stock
    added_count = add_accounts(parsed_accounts)
    total_stock = get_account_count()
    
    # Create success embed
    embed = discord.Embed(
        title="✅ Accounts Restocked",
        description=f"Successfully added **{added_count}** accounts to the stock!",
        color=discord.Color.green()
    )
    embed.add_field(
        name="📦 Total Stock",
        value=f"**{total_stock}** accounts available",
        inline=False
    )
    embed.set_footer(text=f"Restocked by {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stock", description="Check how many accounts are in stock")
async def stock(interaction: discord.Interaction):
    """Check the current account stock"""
    count = get_account_count()
    
    if count == 0:
        embed = discord.Embed(
            title="📦 Account Stock",
            description="**No accounts in stock!**",
            color=discord.Color.red()
        )
        if has_restock_role(interaction.user):
            embed.add_field(
                name="ℹ️ Staff Action",
                value="Use `/restock` to add accounts to the stock.",
                inline=False
            )
    else:
        embed = discord.Embed(
            title="📦 Account Stock",
            description=f"**{count}** accounts available",
            color=discord.Color.green()
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Check if message contains the pattern to format
    content = message.content
    
    # Pattern to detect the credentials format
    # Looking for "Name" or "Username" followed by value, "Password" followed by value, etc.
    if ('Name' in content or 'Username' in content) and 'Password' in content and 'Combo' in content:
        try:
            # Extract username/name
            name_match = re.search(r'(?:Name|Username)\s*\n\s*(\S+)', content, re.IGNORECASE)
            
            # Extract password
            password_match = re.search(r'Password\s*\n\s*(\S+)', content, re.IGNORECASE)
            
            # Extract combo
            combo_match = re.search(r'Combo\s*\n\s*(\S+:\S+)', content, re.IGNORECASE)
            
            if name_match and password_match and combo_match:
                username = name_match.group(1)
                password = password_match.group(1)
                combo = combo_match.group(1)
                
                # Create formatted message
                formatted_message = f"""Username: {username}
Password: {password}
Combo: {combo}"""
                
                # Send formatted message
                await message.channel.send(formatted_message)
                
                # Optional: Delete original message (requires manage_messages permission)
                # await message.delete()
                
        except Exception as e:
            print(f"Error formatting message: {e}")

@bot.command(name='format')
async def manual_format(ctx, *, text):
    """Manually format credentials text"""
    try:
        name_match = re.search(r'(?:Name|Username)\s*\n\s*(\S+)', text, re.IGNORECASE)
        password_match = re.search(r'Password\s*\n\s*(\S+)', text, re.IGNORECASE)
        combo_match = re.search(r'Combo\s*\n\s*(\S+:\S+)', text, re.IGNORECASE)
        
        if name_match and password_match and combo_match:
            username = name_match.group(1)
            password = password_match.group(1)
            combo = combo_match.group(1)
            
            formatted_message = f"""Username: {username}
Password: {password}
Combo: {combo}"""
            
            await ctx.send(formatted_message)
        else:
            await ctx.send("Could not parse the credentials format. Please check the text.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

# Replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token
if __name__ == '__main__':
    TOKEN = 'YOUR_BOT_TOKEN_HERE'
    bot.run(TOKEN)
