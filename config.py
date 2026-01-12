# Bot Configuration File
# Edit these values to customize your bot

# Bot Token - Get this from Discord Developer Portal
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Role Configuration
# Change this to match your server's premium role name (case-sensitive!)
PREMIUM_ROLE_NAME = "Premium"

# Role required to use /restock command (case-sensitive!)
RESTOCK_ROLE_NAME = "Restock"

# Cooldown Settings (in seconds)
PREMIUM_COOLDOWN = 30      # Premium users wait 30 seconds
NORMAL_COOLDOWN = 3600     # Normal users wait 60 minutes (3600 seconds)

# Daily Generation Limits
PREMIUM_DAILY_LIMIT = 50   # Premium users: 50 accounts per day
NORMAL_DAILY_LIMIT = 10    # Normal users: 10 accounts per day

# Bot Command Prefix (for text commands like !format)
COMMAND_PREFIX = "!"

# Feature Toggles
AUTO_DELETE_FORMATTED = False  # Set to True to delete original unformatted messages
