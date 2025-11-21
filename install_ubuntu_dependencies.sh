#!/bin/bash
# SCNMS Ubuntu Dependencies Installation Script
# For Ubuntu 20.04/22.04 LTS

set -e

echo "================================"
echo "SCNMS Ubuntu System Setup"
echo "================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install build essentials
echo "Installing build essentials..."
apt install -y build-essential gcc g++ make cmake git curl wget \
    ca-certificates gnupg lsb-release apt-transport-https \
    software-properties-common

# Install SNMP packages
echo "Installing SNMP packages..."
apt install -y snmp snmpd snmp-mibs-downloader libsnmp-dev libsnmp40
download-mibs
sed -i 's/^mibs :/#mibs :/g' /etc/snmp/snmp.conf

# Install SSL libraries
echo "Installing SSL/TLS libraries..."
apt install -y libssl-dev openssl libffi-dev

# Install network libraries
echo "Installing network libraries..."
apt install -y libxml2-dev libxslt1-dev libssh2-1-dev

# Install PostgreSQL client
echo "Installing PostgreSQL client libraries..."
apt install -y libpq-dev postgresql-client

# Install Python 3.11
echo "Installing Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.11 python3.11-dev python3.11-venv python3-pip

# Install Docker
echo "Installing Docker..."
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    apt remove -y $pkg || true
done

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
systemctl start docker
systemctl enable docker

# Add current user to docker group
if [ -n "$SUDO_USER" ]; then
    usermod -aG docker $SUDO_USER
    echo "User $SUDO_USER added to docker group. Please logout and login again."
fi

# Install network tools
echo "Installing network tools..."
apt install -y net-tools iputils-ping traceroute tcpdump nmap netcat

# Configure firewall
echo "Configuring firewall..."
ufw --force enable
ufw allow 22/tcp
ufw allow 8000:8004/tcp
ufw allow 3000/tcp
ufw allow 9090/tcp
ufw allow 161/udp
ufw allow 162/udp
ufw reload

echo ""
echo "================================"
echo "Installation Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Logout and login again (for Docker group to take effect)"
echo "2. Navigate to SCNMS project directory"
echo "3. Run: ./setup.sh"
echo "4. Run: ./start.sh"
echo ""
