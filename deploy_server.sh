#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, pip, venv
sudo apt install python3 python3-pip python3-venv nginx -y

# Create app directory
mkdir -p ~/voting_app
cd ~/voting_app

# (Manually upload your project files into ~/voting_app or use Git)

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install project dependencies
pip install wheel
pip install Flask pandas openpyxl gunicorn

# Initialize the database if needed
# python3 manage.py init_db  # Uncomment if running first time
# python3 manage.py load_voters --file path_to_voters_file.xls # Uncomment if uploading voters

# Setup Gunicorn systemd service
sudo tee /etc/systemd/system/voting_app.service > /dev/null <<EOF
[Unit]
Description=Gunicorn instance to serve Voting App
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/home/$USER/voting_app
Environment=\"PATH=/home/$USER/voting_app/venv/bin\"
ExecStart=/home/$USER/voting_app/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start the app
sudo systemctl daemon-reload
sudo systemctl start voting_app
sudo systemctl enable voting_app

# Setup Nginx
sudo tee /etc/nginx/sites-available/voting_app > /dev/null <<EOF
server {
    listen 80;
    server_name YOUR_SERVER_IP_OR_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Activate Nginx config
sudo ln -s /etc/nginx/sites-available/voting_app /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
