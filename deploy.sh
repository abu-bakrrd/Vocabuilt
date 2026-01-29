#!/bin/bash

# Vocabuilt Automated VPS Setup Script
# Works on Ubuntu 22.04+

# Exit on error
set -e

echo "🚀 Starting Vocabuilt automated installation..."

# 1. Update system and install dependencies
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv git postgresql postgresql-contrib libpq-dev

# 2. Setup PostgreSQL
echo "🐘 Setting up PostgreSQL database..."
DB_NAME="vocabuilt"
DB_USER="vocabuilt_user"

# Ensure PostgreSQL is running
echo "⚙️ Starting PostgreSQL service..."
sudo systemctl restart postgresql
sudo systemctl enable postgresql

# Wait for PostgreSQL to actually start (wait for socket)
echo "⏳ Waiting for PostgreSQL socket to become available..."
for i in {1..10}; do
    if [ -S /var/run/postgresql/.s.PGSQL.5432 ]; then
        echo "✅ PostgreSQL socket found!"
        break
    fi
    echo "...waiting ($i/10)"
    sleep 2
done

if [ ! -S /var/run/postgresql/.s.PGSQL.5432 ]; then
    echo "❌ PostgreSQL failed to start properly. Checking logs..."
    sudo journalctl -u postgresql -n 20
    exit 1
fi

# Ask for DB password
read -sp "Enter a password for the database user ($DB_USER): " DB_PASSWORD
echo

# Run SQL commands as postgres user to create DB and User locally on VPS
# We move to /tmp first because the postgres user cannot access /root directory
echo "🛠️ Creating local database and user in PostgreSQL..."
cd /tmp
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || echo "⚠️ Database already exists"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || echo "⚠️ User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER DATABASE $DB_NAME OWNER TO $DB_USER;"
cd - > /dev/null
echo "✅ Local PostgreSQL setup finished."

# 3. Setup Project
echo "📂 Setting up project environment..."
PROJECT_DIR=$(pwd)
PYTHON_VENV="$PROJECT_DIR/venv"

if [ ! -d "$PYTHON_VENV" ]; then
    python3 -m venv "$PYTHON_VENV"
fi

source "$PYTHON_VENV/bin/activate"
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create .env file
echo "🔑 Configuring environment variables..."
read -p "Enter your Telegram Bot Token: " BOT_TOKEN

cat > .env << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
SESSION_SECRET=$(openssl rand -hex 24)
EOF

echo "✅ .env file created."

# 5. Create Systemd Service
echo "⚙️ Creating systemd service..."
SERVICE_FILE="/etc/systemd/system/vocabuilt.service"
CURRENT_USER=$(whoami)

sudo bash -c "cat > $SERVICE_FILE << EOF
[Unit]
Description=Vocabuilt Telegram Bot
After=network.target postgresql.service

[Service]
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PYTHON_VENV/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

# 6. Start and Enable Service
echo "📡 Starting the bot service..."
sudo systemctl daemon-reload
sudo systemctl enable vocabuilt
sudo systemctl restart vocabuilt

echo "✨ Installation complete!"
echo "📊 Run 'sudo systemctl status vocabuilt' to check if it's running."
echo "📝 Use 'journalctl -u vocabuilt -f' to see the logs."
