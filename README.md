# 🔮 AS CLOUD SYSTEM — Telegram Storage Bot

Store any Telegram file and retrieve it anytime with a unique 10-character code.

---

## Features

- 📁 Store photos, videos, documents, audio, voice notes, stickers, GIFs
- 🔑 Auto-generates a unique 10-char alphanumeric code per file (`A3BX7KQ2LP`)
- 📥 `/give CODE` retrieves the file instantly
- 🚫 No "Forwarded from" header (uses `copy_message`)
- 💾 Heroku Postgres database
- 🎛 Button-based UI throughout

---

## Setup

### 1. Create a Telegram Bot
1. Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. Save the **BOT_TOKEN**

### 2. Create a Storage Channel
1. Create a **private channel** in Telegram
2. Add your bot as an **Admin** with "Post Messages" permission
3. Get the **numerical Chat ID** of the channel:
   - Forward any message from the channel to [@userinfobot](https://t.me/userinfobot)
   - Or use `https://api.telegram.org/bot<TOKEN>/getUpdates` after adding the bot
   - The ID looks like `-1001234567890` (starts with `-100`)

### 3. Deploy to Heroku

#### Option A — One-Click Deploy
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Fill in `BOT_TOKEN` and `CHANNEL_ID` (numerical) when prompted.

#### Option B — Manual CLI Deploy
```bash
# Clone repo
git clone https://github.com/your-username/as-cloud-bot
cd as-cloud-bot

# Login & create app
heroku login
heroku create your-app-name

# Add Postgres addon
heroku addons:create heroku-postgresql:essential-0

# Set env vars
heroku config:set BOT_TOKEN="123456:ABC-DEF..."
heroku config:set CHANNEL_ID="-1001234567890"

# Deploy
git push heroku main

# Scale worker
heroku ps:scale worker=1
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome screen with menu buttons |
| `/help` | Same as start |
| `/give CODE` | Retrieve a stored file by its 10-char code |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Bot token from @BotFather | ✅ |
| `CHANNEL_ID` | Numerical channel ID (e.g. `-1001234567890`) | ✅ |
| `DATABASE_URL` | Auto-set by Heroku Postgres addon | ✅ |

---

## Database Schema

```sql
CREATE TABLE files (
    id          SERIAL PRIMARY KEY,
    file_code   VARCHAR(10) UNIQUE NOT NULL,
    message_id  BIGINT NOT NULL,
    user_id     BIGINT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Notes

- The bot uses `copy_message` (not `forward_message`), so files appear **without** any "Forwarded from" header.
- Files are physically stored in Telegram's servers; the bot only stores the `message_id` reference in Postgres.
- Keep the storage channel intact — deleting messages there will break retrieval.
