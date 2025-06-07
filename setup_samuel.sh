# This script sets up the environment for Samuel the Raven, a project that uses Python and various system packages.
# It creates a virtual environment, installs Python dependencies, and optionally installs system-level packages.

# How to use me:
# git clone https://github.com/Anatw/samuel_the_raven.git
# cd samuel_the_raven
# ./setup_samuel.sh
# Then:
# source ~/.virtualenvs/samuel-env/bin/activate
# python samuel_main.py


#!/bin/bash

echo "🐦 Setting up Samuel the Raven's environment..."

# 1. Create virtual environment (if not exists)
ENV_DIR="$HOME/.virtualenvs/samuel-env"
if [ ! -d "$ENV_DIR" ]; then
  echo "📦 Creating virtualenv..."
  python3 -m venv "$ENV_DIR" --system-site-packages
fi

# 2. Activate environment
source "$ENV_DIR/bin/activate"

# 3. Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install system-level packages
echo "🛠️ Installing system packages (requires sudo)..."
sudo apt update
sudo apt install -y \
  libtiff6 libcap-dev libdrm-dev libfmt-dev libcamera-dev \
  portaudio19-dev alsa-utils

# 5. Enable I2C for MPR121 touch sensor
echo "⚙️ Enabling I2C..."
sudo raspi-config nonint do_i2c 0

echo "✅ Setup complete. To run Samuel:"
echo "source $ENV_DIR/bin/activate && python samuel_main.py"
