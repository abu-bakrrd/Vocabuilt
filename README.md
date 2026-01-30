# Vocabuilt: Telegram Vocabulary Bot

A Telegram bot for learning English vocabulary with a local personal dictionary and interactive quizzes.

## 🚀 Quick Start (VPS Deployment)

The fastest way to install the bot on a fresh Ubuntu 22.04+ VPS:

1. **Transfer files** to your server (via Git or SCP).
2. **Run the automated installer**:

```bash
chmod +x deploy.sh
./deploy.sh
```

3. **Follow the prompts** to set your Database Password and Telegram Bot Token.

### Manage the Service

The bot runs as a systemd service called `vocabuilt`:

- **Check status**: `sudo systemctl status vocabuilt`
- **Restart**: `sudo systemctl restart vocabuilt`
- **View logs**: `journalctl -u vocabuilt -f`

---

## 💻 Local Development (Windows/Mac/Linux)

1. **Create a virtual environment**:

```bash
python -m venv venv
./venv/Scripts/activate  # Windows
source venv/bin/activate # Mac/Linux
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Set up environment**:
   Copy `.env.example` to `.env` and add your bot token.
4. **Run**:
   ```bash
   python main.py
   ```

---

## 🐙 How to Push to Git

To save your code to GitHub/GitLab/Bitbucket:

1. **Initialize Git** (if not already done):

```bash
git init
```

2. **Add your files**:

```bash
git add .
```

3. **Commit your changes**:

```bash
git commit -m "Initialize Vocabuilt bot with automated deployment"
```

4. **Connect to a remote repository**:
   _Go to GitHub, create a new empty repository, then copy the commands provided there:_

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
```

5. **Push**:

```bash
git push -u origin main
```

> [!IMPORTANT]
> Never share your `.env` file or hardcode your Bot Token. The `.gitignore` file included will keep your local database and secrets safe from being uploaded.

---

## 🛠 Project Structure

- `bot/`: Core Telegram bot logic, handlers, and quizzes.
- `app.py`: Flask application and database initialization.
- `models.py`: Database schema (Users, Words, Quizzes).
- `deploy.sh`: Automated Ubuntu VPS setup script.
- `utils/`: Translation logic and local fallback dictionary.
