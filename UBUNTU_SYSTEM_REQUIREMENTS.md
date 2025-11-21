# SCNMS - Ubuntu System Requirements & Installation Guide

## Complete Installation Guide for Ubuntu 20.04/22.04 LTS

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [System Package Dependencies](#system-package-dependencies)
3. [Docker Installation](#docker-installation)
4. [Docker Compose Installation](#docker-compose-installation)
5. [Python Development Environment](#python-development-environment)
6. [Network Protocol Tools](#network-protocol-tools)
7. [SNMP Configuration](#snmp-configuration)
8. [Firewall Configuration](#firewall-configuration)
9. [System User Permissions](#system-user-permissions)
10. [Optional Tools](#optional-tools)
11. [Verification Steps](#verification-steps)

---

## Prerequisites

### Minimum System Requirements
- **OS**: Ubuntu 20.04 LTS or 22.04 LTS
- **CPU**: 4 cores (minimum 2 cores)
- **RAM**: 8GB (minimum 4GB)
- **Disk**: 50GB free space
- **Network**: Static IP recommended for production
- **User**: sudo/root access required for installation

---

## System Package Dependencies

### Step 1: Update Package Index
```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Essential Build Tools
```bash
sudo apt install -y \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    git \
    curl \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    apt-transport-https \
    software-properties-common
```

### Step 3: Install SNMP Development Libraries
```bash
# SNMP libraries (required for pysnmp)
sudo apt install -y \
    snmp \
    snmpd \
    snmp-mibs-downloader \
    libsnmp-dev \
    libsnmp40
    
# Download MIBs
sudo download-mibs

# Configure SNMP to not complain about missing MIBs
sudo sed -i 's/^mibs :/#mibs :/g' /etc/snmp/snmp.conf
```

### Step 4: Install SSL/TLS Libraries
```bash
# OpenSSL libraries (required for secure connections)
sudo apt install -y \
    libssl-dev \
    openssl \
    libffi-dev
```

### Step 5: Install Network Libraries
```bash
# Network development libraries
sudo apt install -y \
    libxml2-dev \
    libxslt1-dev \
    libssh2-1-dev \
    libnetconf-dev \
    python3-ncclient
```

### Step 6: Install PostgreSQL Client Libraries
```bash
# PostgreSQL development libraries
sudo apt install -y \
    libpq-dev \
    postgresql-client
```

### Step 7: Install Python 3.11+ (if not available)
```bash
# Check Python version
python3 --version

# If Python < 3.11, add deadsnakes PPA (Ubuntu 20.04)
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip

# Set Python 3.11 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

---

## Docker Installation

### Step 1: Remove Old Docker Versions (if any)
```bash
sudo apt remove -y docker docker-engine docker.io containerd runc
```

### Step 2: Add Docker Official GPG Key
```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

### Step 3: Set Up Docker Repository
```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### Step 4: Install Docker Engine
```bash
sudo apt update
sudo apt install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin
```

### Step 5: Start and Enable Docker
```bash
sudo systemctl start docker
sudo systemctl enable docker
sudo systemctl status docker
```

### Step 6: Add User to Docker Group
```bash
# Add current user to docker group (no sudo required for docker commands)
sudo usermod -aG docker $USER

# Apply group changes (logout/login or run):
newgrp docker

# Verify
docker run hello-world
```

---

## Docker Compose Installation

Docker Compose v2 is included with docker-compose-plugin. Verify:

```bash
docker compose version
# Should output: Docker Compose version v2.x.x
```

### Alternative: Standalone Docker Compose (if needed)
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## Python Development Environment

### Install Python Package Manager and Virtual Environment
```bash
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-wheel \
    python3-setuptools
    
# Upgrade pip
python3 -m pip install --upgrade pip
```

### Create Project Virtual Environment (Optional for Local Development)
```bash
cd "/home/sujan-rathod/Desktop/NMS/NMS project"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Network Protocol Tools

### SNMP Tools
```bash
# Install SNMP utilities
sudo apt install -y \
    snmpwalk \
    snmpget \
    snmpset \
    snmptrapd

# Test SNMP (example)
snmpwalk -v2c -c public localhost system
```

### NETCONF/SSH Tools
```bash
# Install SSH and NETCONF libraries
sudo apt install -y \
    openssh-client \
    libssh-dev \
    libnetconf2-2
```

### Network Debugging Tools
```bash
sudo apt install -y \
    net-tools \
    iputils-ping \
    traceroute \
    tcpdump \
    nmap \
    netcat
```

---

## SNMP Configuration

### Configure SNMP Daemon (for Local Testing)
```bash
# Backup original config
sudo cp /etc/snmp/snmpd.conf /etc/snmp/snmpd.conf.bak

# Create basic SNMP configuration
sudo tee /etc/snmp/snmpd.conf > /dev/null <<'EOF'
# SCNMS Test SNMP Configuration
agentAddress  udp:161
rocommunity   public  default
rwcommunity   private default

# System information
sysLocation    Campus Network Lab
sysContact     admin@campus.edu
sysName        scnms-server

# Disable authentication traps
authtrapenable  1

# SNMP trap destination (if needed)
# trap2sink localhost public
EOF

# Restart SNMP daemon
sudo systemctl restart snmpd
sudo systemctl enable snmpd

# Test local SNMP
snmpwalk -v2c -c public localhost system
```

### Configure SNMP Trap Listener (Optional)
```bash
# Configure snmptrapd
sudo tee /etc/snmp/snmptrapd.conf > /dev/null <<'EOF'
authCommunity log,execute,net public
disableAuthorization yes
EOF

# Start snmptrapd
sudo systemctl start snmptrapd
sudo systemctl enable snmptrapd
```

---

## Firewall Configuration

### Configure UFW Firewall
```bash
# Enable UFW
sudo ufw enable

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow SCNMS services
sudo ufw allow 8000:8004/tcp comment 'SCNMS Microservices'

# Allow Grafana
sudo ufw allow 3000/tcp comment 'Grafana'

# Allow Prometheus
sudo ufw allow 9090/tcp comment 'Prometheus'

# Allow PostgreSQL (only if external access needed)
# sudo ufw allow 5432/tcp comment 'PostgreSQL'

# Allow Redis (only if external access needed)
# sudo ufw allow 6379/tcp comment 'Redis'

# Allow SNMP (for receiving traps and polling)
sudo ufw allow 161/udp comment 'SNMP'
sudo ufw allow 162/udp comment 'SNMP Traps'

# Reload firewall
sudo ufw reload

# Check status
sudo ufw status numbered
```

### Configure Firewalld (Alternative to UFW)
```bash
# If using firewalld instead of UFW
sudo apt install -y firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Open ports
sudo firewall-cmd --permanent --add-port=8000-8004/tcp
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=9090/tcp
sudo firewall-cmd --permanent --add-port=161/udp
sudo firewall-cmd --permanent --add-port=162/udp

# Reload
sudo firewall-cmd --reload
```

---

## System User Permissions

### Create SCNMS System User (Production)
```bash
# Create dedicated user for SCNMS
sudo useradd -r -m -s /bin/bash -d /opt/scnms scnms

# Add to docker group
sudo usermod -aG docker scnms

# Set ownership
sudo chown -R scnms:scnms /opt/scnms
```

### Set Directory Permissions
```bash
cd "/home/sujan-rathod/Desktop/NMS/NMS project"

# Make scripts executable
chmod +x setup.sh start.sh stop.sh test_api.sh

# Set proper permissions for config directories
chmod -R 755 config/
chmod -R 755 services/
chmod 644 requirements.txt
chmod 644 docker-compose.yml
```

---

## Optional Tools

### Prometheus (Standalone - Not Required if Using Docker)
```bash
# Download Prometheus
cd /tmp
PROM_VERSION="2.47.0"
wget https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz
tar xvfz prometheus-${PROM_VERSION}.linux-amd64.tar.gz
sudo mv prometheus-${PROM_VERSION}.linux-amd64 /opt/prometheus

# Create systemd service (if needed)
sudo tee /etc/systemd/system/prometheus.service > /dev/null <<'EOF'
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/opt/prometheus/prometheus \
    --config.file=/opt/prometheus/prometheus.yml \
    --storage.tsdb.path=/var/lib/prometheus/

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
```

### Grafana (Standalone - Not Required if Using Docker)
```bash
# Add Grafana GPG key
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -

# Add Grafana repository
echo "deb https://packages.grafana.com/oss/deb stable main" | \
    sudo tee /etc/apt/sources.list.d/grafana.list

# Install Grafana
sudo apt update
sudo apt install -y grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### PostgreSQL (Standalone - Not Required if Using Docker)
```bash
# Install PostgreSQL 15
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

## Verification Steps

### 1. Verify Docker Installation
```bash
docker --version
docker compose version
docker ps
docker run hello-world
```

### 2. Verify Python Installation
```bash
python3 --version
pip3 --version
```

### 3. Verify SNMP Installation
```bash
snmpwalk -v2c -c public localhost system
```

### 4. Verify Network Connectivity
```bash
ping -c 4 8.8.8.8
curl -I https://google.com
```

### 5. Check Firewall Status
```bash
sudo ufw status
```

### 6. Check Required Ports
```bash
# Check if ports are available
sudo ss -tulpn | grep -E ':(8000|8001|8002|8003|8004|3000|9090|5432|6379|161|162)'
```

### 7. Verify Docker Network
```bash
docker network ls
docker network inspect bridge
```

---

## Complete Installation Script

Save this as `install_ubuntu_dependencies.sh`:

```bash
#!/bin/bash
# SCNMS Ubuntu Dependencies Installation Script

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
```

### Make it executable and run:
```bash
chmod +x install_ubuntu_dependencies.sh
sudo ./install_ubuntu_dependencies.sh
```

---

## Post-Installation Checklist

- [ ] Docker installed and running
- [ ] Docker Compose v2 installed
- [ ] Python 3.11+ installed
- [ ] SNMP libraries installed
- [ ] User added to docker group
- [ ] Firewall configured
- [ ] All required ports open
- [ ] SNMP daemon configured (if testing locally)
- [ ] Network connectivity verified

---

## Troubleshooting

### Docker Permission Denied
```bash
# If you get "permission denied" errors with Docker
sudo usermod -aG docker $USER
newgrp docker
# or logout/login
```

### SNMP MIBs Not Loading
```bash
# Download MIBs
sudo download-mibs
# Edit SNMP config
sudo nano /etc/snmp/snmp.conf
# Comment out: mibs :
```

### Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :8000
# Kill the process or change the port in docker-compose.yml
```

### Python Module Not Found
```bash
# Activate virtual environment
source .venv/bin/activate
# Reinstall requirements
pip install -r requirements.txt
```

---

## Production Hardening (Additional Steps)

### 1. System Security
```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure automatic updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 2. Docker Security
```bash
# Enable Docker content trust
export DOCKER_CONTENT_TRUST=1

# Scan images for vulnerabilities
docker scan nmsproject-api:latest
```

### 3. Network Security
```bash
# Limit SSH to specific IPs (production)
sudo ufw delete allow 22/tcp
sudo ufw allow from YOUR_IP_ADDRESS to any port 22

# Enable SYN flood protection
sudo sysctl -w net.ipv4.tcp_syncookies=1
```

---

## Support

For issues during installation:
1. Check logs: `sudo journalctl -xe`
2. Verify services: `sudo systemctl status docker`
3. Test connectivity: `ping`, `curl`, `telnet`
4. Review firewall: `sudo ufw status`

---

**Document Version**: 1.0  
**Last Updated**: October 22, 2025  
**Target OS**: Ubuntu 20.04/22.04 LTS
