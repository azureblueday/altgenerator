# Quick Start Guide - Account Stock System

## Overview
Your Discord bot now has an account stock system! Staff can add accounts using `/restock`, and users can claim them with `/generate`.

## Setup (5 minutes)

### 1. Create the Roles
In your Discord server, create two roles:
- **Premium** - For users who get 50 accounts/day and 30s cooldown
- **Restock** - For staff who can add accounts to stock

### 2. Configure the Bot
Edit `config.py`:
```python
BOT_TOKEN = "your_actual_token_here"
PREMIUM_ROLE_NAME = "Premium"    # Must match your Discord role exactly
RESTOCK_ROLE_NAME = "Restock"    # Must match your Discord role exactly
```

### 3. Assign Roles
- Give the "Restock" role to staff members who will manage accounts
- Give the "Premium" role to users who paid/subscribed

### 4. Start the Bot
```bash
python discord_formatter_bot.py
```

## How It Works

### For Staff (with Restock role):

1. **Add Accounts** - Use `/restock` with your accounts:
   ```
   /restock accounts:
   username1:password1
   username2:password2
   username3:password3
   ```

2. **Check Stock** - Use `/stock` to see how many accounts are available:
   ```
   /stock
   → 📦 Account Stock: 50 accounts available
   ```

### For Users:

1. **Generate Account** - Use `/generate`:
   ```
   /generate
   → ✅ Account Generated
   Username: maewayke226
   Password: 96pSf@ATn1!Je
   Combo: maewayke226:96pSf@ATn1!Je
   ```

2. **Rate Limits**:
   - **Standard Users**: 10 accounts/day, 60 minute cooldown
   - **Premium Users**: 50 accounts/day, 30 second cooldown

## Supported Input Formats

The `/restock` command accepts multiple formats:

### Simple Format (Recommended)
```
/restock accounts:
username1:password1
username2:password2
```

### Formatted Style (Your Example)
```
/restock accounts:
Name
maewayke226
Password
96pSf@ATn1!Je
Combo
maewayke226:96pSf@ATn1!Je
Tap the combo above to copy on mobile. Do not share this account!
```

The bot automatically extracts the username:password from either format!

### Mixed Format
You can even mix formats:
```
/restock accounts:
user1:pass1
Name
user2
Password
pass2
user3:pass3
```

## Account Storage

- Accounts are stored in `accounts.txt` in the bot's directory
- Each account is on its own line in `username:password` format
- When a user runs `/generate`, one account is randomly selected and removed
- The file persists between bot restarts

## Common Commands

| Command | Who Can Use | Description |
|---------|------------|-------------|
| `/generate` | Everyone | Get an account from stock |
| `/restock` | Staff only | Add accounts to stock |
| `/stock` | Everyone | Check available accounts |
| `/stats` | Everyone | Check your usage stats |

## Tips

1. **Regular Restocking**: Check `/stock` regularly and restock when low
2. **Bulk Add**: You can add hundreds of accounts at once with `/restock`
3. **Monitor Usage**: Use `/stock` to track how quickly accounts are being claimed
4. **Testing**: Test with a few accounts first before adding large quantities

## Example Workflow

1. Staff member gets new accounts (100 accounts)
2. Staff runs `/restock` and pastes all accounts
3. Bot confirms: "✅ Successfully added 100 accounts to the stock!"
4. Users can now run `/generate` to claim accounts
5. Bot automatically manages distribution and rate limiting
6. Stock depletes over time as users claim accounts
7. When stock is low, staff restocks again

## Error Messages

**"No Accounts Available"**
- Stock is empty, staff needs to use `/restock`

**"Permission Denied"**
- User doesn't have the Restock role
- Check role name matches exactly in config

**"No Valid Accounts Found"**
- Format wasn't recognized
- Make sure accounts are in `username:password` format

## Advanced: Viewing the Stock File

Want to see what's in stock? Just open `accounts.txt`:
```bash
cat accounts.txt
```

You'll see:
```
username1:password1
username2:password2
username3:password3
```

## Need Help?

- Make sure both "Message Content Intent" and "Server Members Intent" are enabled
- Check that role names match exactly (case-sensitive!)
- Verify the bot has write permissions in its directory
- Test with a small batch first before adding large quantities
