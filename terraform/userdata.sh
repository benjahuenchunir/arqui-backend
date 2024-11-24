#!/bin/bash

# Update and install Nginx and Docker
sudo apt-get update -y
sudo apt-get install -y nginx docker.io

# Download docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start and enable services
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl enable docker
sudo systemctl start docker

# Install the CodeDeploy agent
sudo apt-get install ruby wget -y && \
cd /home/ubuntu && \
wget https://aws-codedeploy-us-east-1.s3.us-east-1.amazonaws.com/latest/install && \
chmod +x ./install && \
sudo ./install auto && \
rm install && \
sudo systemctl enable codedeploy-agent && \
sudo systemctl start codedeploy-agent

# Custom Nginx configuration
cat <<EOF | sudo tee /etc/nginx/sites-available/pre-certbot-api.conf
upstream apiLoadBalancer {
    server 0.0.0.0:8001;
    server 0.0.0.0:8002;
    server 0.0.0.0:8003;
}

server {

    server_name entregasarquicrisinguc.xyz www.entregasarquicrisinguc.xyz;

    location / {
        proxy_pass http://apiLoadBalancer;

        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    listen 80;
    listen [::]:80;
}

server {
    server_name entregasarquicrisinguc.xyz www.entregasarquicrisinguc.xyz;

    location / {
        proxy_pass http://apiLoadBalancer;

        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    listen 80;
    listen [::]:80;
}
EOF

# Enable the custom Nginx configuration
sudo ln -s /etc/nginx/sites-available/pre-certbot-api.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Restart Nginx to apply the new configuration
sudo systemctl restart nginx