#!/bin/bash

# Vocabuilt Automated VPS Setup Script
# Works on Ubuntu 22.04+

# Exit on error
set -e

echo "=========================================="
echo "   🚀 VOCABUILT AUTOMATED SETUP   "
echo "=========================================="

# Cleanup old logs and temp files
echo "🧹 Cleaning up old temporary files..."
rm -f *.log
sudo find /tmp -name ".s.PGSQL.*" -mtime +1 -delete 2>/dev/null || true

# Check if already running as root
if [ "$EUID" -ne 0 ]; then
  echo "💡 You are not running as root. This script will use sudo for system tasks."
fi

# 1. Update system and install dependencies
echo "📦 Updating system packages..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv git postgresql postgresql-contrib libpq-dev openssl

# 2. Setup PostgreSQL
echo "🐘 Setting up PostgreSQL database..."
DB_NAME="vocabuilt"
DB_USER="vocabuilt_user"

# Ensure PostgreSQL core service is enabled
sudo systemctl enable postgresql

# Diagnostic: check for clusters and start them
echo "⚙️ Checking for PostgreSQL clusters..."
pg_lsclusters

# If cluster exists but is down, try to start it
if pg_lsclusters | grep -q "14.*main.*down"; then
    echo "⚠️ Cluster '14 main' is down. Attempting to start..."
    sudo pg_ctlcluster 14 main start || true
fi

# If it's STILL not online, we use the "Nuclear Option"
if ! pg_lsclusters | grep -q "14.*main.*online"; then
    echo "🚀 Using the 'Nuclear Option': Dropping and recreating cluster..."
    sudo pg_dropcluster 14 main --stop || true
    echo "🔨 Recreating cluster with C.UTF-8 locale..."
    sudo pg_createcluster 14 main --start --locale C.UTF-8 || true
fi

# Ensure the specific service is active
sudo systemctl start postgresql@14-main || true

# Wait for PostgreSQL to actually start (wait for socket)
echo "⏳ Waiting for PostgreSQL socket to become available..."
SOCKET_FOUND=false
for i in {1..15}; do
    # Check common socket location
    if [ -S /var/run/postgresql/.s.PGSQL.5432 ]; then
        echo "✅ PostgreSQL socket found!"
        SOCKET_FOUND=true
        break
    fi
    echo "...waiting ($i/15)"
    sleep 2
done

if [ "$SOCKET_FOUND" = false ]; then
    echo "❌ PostgreSQL failed to start properly."
    echo "🛠️ Diagnostic info:"
    pg_lsclusters
    echo "📝 Last 20 lines of Postgres log:"
    sudo tail -n 20 /var/log/postgresql/postgresql-14-main.log || true
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
if [ -f .env ]; then
    echo "⚠️ .env file already exists. Skipping creation to preserve settings."
    echo "💡 If you need to reconfigure, delete the .env file and run this script again."
else
    echo "🔑 Configuring environment variables..."
    read -p "Enter your Telegram Bot Token: " BOT_TOKEN

    cat > .env << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
SESSION_SECRET=$(openssl rand -hex 24)
EOF
    echo "✅ .env file created."
fi

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
