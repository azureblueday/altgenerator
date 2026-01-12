# Discord Credentials Formatter & Generator Bot

A Discord bot that automatically formats credential messages and generates accounts with role-based rate limiting.

## Features

- **Auto-formatting**: Automatically detects and reformats messages with credentials
- **Manual formatting**: Use `!format` command to manually format text
- **/generate command**: Generate random account credentials with smart rate limiting
- **/restock command**: Staff can add accounts to the stock (requires Restock role)
- **/stock command**: Check how many accounts are available
- **Role-based limits**: Premium users get better rates and higher limits
- **Daily limits**: Prevents abuse with daily generation caps
- **Account management**: Automatically distributes accounts from stock
- **Clean output**: Removes unnecessary text and formats consistently

## /generate Command Features

### Standard Users (No Premium Role)
- **Cooldown**: 60 minutes between generations
- **Daily Limit**: 10 accounts per day
- Perfect for casual users

### Premium Users (With Premium Role)
- **Cooldown**: 30 seconds between generations
- **Daily Limit**: 50 accounts per day
- **Special badge**: Premium indicator on generated accounts
- Ideal for power users

### Rate Limiting
- Automatic cooldown tracking per user
- Daily limits reset every 24 hours
- Helpful error messages with time remaining
- Ephemeral messages (only visible to the user) for errors

## Example

**Before:**
```
Name 
maewayke226 
Password 
96pSf@ATn1!Je 
Combo 
maewayke226:96pSf@ATn1!Je 
Tap the combo above to copy on mobile. Do not share this account!
```

**After:**
```
Username: maewayke226 
Password: 96pSf@ATn1!Je 
Combo: maewayke226:96pSf@ATn1!Je
```

## Setup Instructions

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot"
5. Under "Privileged Gateway Intents", enable:
   - **MESSAGE CONTENT INTENT** (Required!)
   - **SERVER MEMBERS INTENT** (Required for role checking!)
   - Presence Intent (optional)
6. Click "Reset Token" and copy your bot token (keep it secret!)

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install discord.py directly:
```bash
pip install discord.py
```

### 3. Configure the Bot

Open `discord_formatter_bot.py` and configure these settings:

**Bot Token** - Replace with your actual bot token:
```python
TOKEN = 'your_actual_bot_token_here'
```

**Premium Role Name** - Change to match your server's role name:
```python
PREMIUM_ROLE_NAME = "Premium"  # Change this to your role name (e.g., "VIP", "Donor", "Pro")
```

**Restock Role Name** - Role that can use /restock command:
```python
RESTOCK_ROLE_NAME = "Restock"  # Change this to your staff/admin role (e.g., "Staff", "Admin", "Mod")
```

**Rate Limits** (optional) - Adjust if needed:
```python
PREMIUM_COOLDOWN = 30  # Premium users: 30 seconds
NORMAL_COOLDOWN = 3600  # Normal users: 60 minutes
PREMIUM_DAILY_LIMIT = 50  # Premium users: 50 per day
NORMAL_DAILY_LIMIT = 10  # Normal users: 10 per day
```

**IMPORTANT:** Never share your bot token publicly!

### 4. Invite Bot to Your Server

1. In the Discord Developer Portal, go to "OAuth2" > "URL Generator"
2. Select scopes:
   - `bot`
3. Select bot permissions:
   - `Send Messages`
   - `Read Messages/View Channels`
   - `Read Message History`
   - `Manage Messages` (optional, if you want the bot to delete original messages)
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

### 5. Run the Bot

```bash
python discord_formatter_bot.py
```

You should see:
```
YourBotName#1234 has connected to Discord!
Bot is ready to format messages!
```

## Usage

### /restock Command (Staff Only)

Add accounts to the stock for distribution. Requires the "Restock" role.

**Simple Format:**
```
/restock accounts:
username1:password1
username2:password2
username3:password3
```

**Formatted Input (the format from your example):**
```
/restock accounts:
Name
maewayke226
Password
96pSf@ATn1!Je
Combo
maewayke226:96pSf@ATn1!Je
Tap the combo above to copy on mobile. Do not share this account!
Name
user2
Password
pass2
```

The bot will automatically parse both formats and extract the username:password combos!

**Output:**
```
✅ Accounts Restocked
Successfully added 2 accounts to the stock!
📦 Total Stock: 25 accounts available
```

### /stock Command

Check how many accounts are currently available:

```
/stock
```

**Output:**
```
📦 Account Stock
50 accounts available
```

### /generate Command

Generate account credentials from the stock with automatic rate limiting:

```
/generate
```

The bot will pull a random account from the stock and give it to you!

**Example Output:**
```
✅ Account Generated
Username: `maewayke226`
Password: `96pSf@ATn1!Je`
Combo: `maewayke226:96pSf@ATn1!Je`

Remaining today: 9/10 | Stock: 24 | Cooldown: 60 minutes
```

**For Premium Users:**
```
💎 Premium Generation
✅ Account Generated
Username: `premium789`
Password: `X7@nL4&wQ1z#`
Combo: `premium789:X7@nL4&wQ1z#`

Remaining today: 49/50 | Stock: 24 | Cooldown: 30 seconds
```

**If Stock is Empty:**
```
❌ No Accounts Available
The account stock is empty! Please wait for a restock.
ℹ️ Info: Staff members can add accounts using /restock
```

**Rate Limit Messages:**
- If on cooldown: Shows time remaining before next use
- If daily limit reached: Shows when limit resets
- All error messages are ephemeral (only visible to you)

### Automatic Formatting

Simply post a message in any channel the bot has access to with the format:
```
Name 
username123 
Password 
pass123 
Combo 
username123:pass123
```

The bot will automatically detect it and post the formatted version.

### Manual Formatting

Use the `!format` command:
```
!format Name
username123
Password
pass123
Combo
username123:pass123
```

## Optional Configuration

### Customize Generation Output

The `/generate` command currently generates random credentials. You can customize the generation logic in the bot code:

```python
# In the generate() function, replace this section:
username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
```

You can:
- Connect to a database of actual accounts
- Use an API to generate accounts
- Read from a text file
- Implement any custom logic

### Change Rate Limits

Edit these values in the configuration section:
```python
PREMIUM_COOLDOWN = 30  # seconds
NORMAL_COOLDOWN = 3600  # seconds (60 minutes)
PREMIUM_DAILY_LIMIT = 50  # accounts per day
NORMAL_DAILY_LIMIT = 10  # accounts per day
```

### Change Premium Role Name

If your server uses a different role name:
```python
PREMIUM_ROLE_NAME = "VIP"  # or "Donor", "Pro", etc.
```

Make sure the role name matches exactly (case-sensitive)!

### Auto-delete Original Messages

If you want the bot to automatically delete the original unformatted message, uncomment this line in the code:

```python
# await message.delete()
```

**Note:** The bot needs "Manage Messages" permission for this to work.

### Change Command Prefix

To use a different prefix instead of `!`, change this line:

```python
bot = commands.Bot(command_prefix='!', intents=intents)
```

For example, use `?` instead:
```python
bot = commands.Bot(command_prefix='?', intents=intents)
```

## Security Note

⚠️ **Keep your bot token secure!** Never commit it to public repositories. Consider using environment variables:

```python
import os
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
```

Then set it in your environment:
```bash
export DISCORD_BOT_TOKEN='your_token_here'
```

## Troubleshooting

### /generate command doesn't appear
- Make sure the bot is online and connected
- Wait a few minutes for Discord to sync slash commands
- Try kicking and re-inviting the bot
- Check that the bot has `applications.commands` scope

### /restock command permission denied
- Verify the restock role name matches exactly in the code (case-sensitive)
- Check that users actually have the role assigned
- Ensure SERVER MEMBERS INTENT is enabled for role checking

### Accounts not being parsed in /restock
- Make sure accounts are in `username:password` format
- Each account should be on a new line
- The bot supports both simple format and the formatted style from your example
- Check that there are no extra spaces or special characters

### Stock not updating
- The `accounts.txt` file is created in the same directory as the bot
- Make sure the bot has write permissions to the directory
- Use `/stock` to verify the current count
- Verify the role name matches exactly in the code (case-sensitive)
- Ensure SERVER MEMBERS INTENT is enabled in Developer Portal
- Check that users actually have the role assigned
- Try restarting the bot after role changes

### Rate limits not resetting
- Daily limits reset 24 hours after first use (not at midnight)
- Restart the bot to clear all cooldowns (for testing)
- Cooldowns are per-user and stored in memory

### Bot doesn't respond
- Make sure MESSAGE CONTENT INTENT is enabled in Discord Developer Portal
- Ensure SERVER MEMBERS INTENT is enabled for role checking
- Check that the bot has permission to read and send messages in the channel
- Verify your bot token is correct

### Bot crashes on startup
- Ensure discord.py is installed: `pip install discord.py`
- Check that your Python version is 3.8 or higher
- Make sure all intents are properly enabled

### Formatting doesn't work
- Make sure the message follows the expected format with line breaks
- The pattern is case-insensitive, so "Name", "name", or "NAME" all work

### Slash commands not syncing
- It can take up to an hour for Discord to sync commands globally
- Try using `guild_id` parameter for instant syncing during development
- Restart Discord client if commands don't appear

## License

Free to use and modify!
