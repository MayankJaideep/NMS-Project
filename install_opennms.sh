#!/bin/bash

# Install OpenNMS on macOS using Homebrew

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Update Homebrew
brew update

# Install OpenNMS dependencies
brew install postgresql@14 openjdk@17

# Add OpenNMS repository
brew tap opennms/opennms

# Install OpenNMS
brew install opennms

# Initialize PostgreSQL
brew services start postgresql@14
createdb opennms
createuser -d opennms

# Configure OpenNMS
echo "opennms   ALL=(ALL) NOPASSWD: /opt/opennms/bin/opennms" | sudo tee /etc/sudoers.d/opennms
sudo chmod 440 /etc/sudoers.d/opennms

# Start OpenNMS
sudo /opt/opennms/bin/opennms start

echo "OpenNMS installation complete!"
echo "Access the web interface at: http://localhost:8980/opennms"
echo "Default credentials: admin/admin"
