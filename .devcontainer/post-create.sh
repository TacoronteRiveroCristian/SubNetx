#!/bin/bash

# Ensure the script fails if there are any errors
set -e

echo "⚙️ Setting up development environment..."

# Install Python development tools
echo "🐍 Installing Python development tools..."
pip3 install --no-cache-dir --upgrade pip

# Install specific versions of development tools
pip3 install --no-cache-dir \
    black==25.1.0 \
    isort==6.0.1 \
    mypy==1.15.0 \
    pylint==3.3.6 \
    pytest==8.3.5 \
    pytest-cov==6.0.0 \
    flake8==7.1.2 \
    flake8-docstrings==1.7.0 \
    Flake8-pyproject==1.2.3 \
    debugpy==1.8.13 \
    ipython==8.34.0 \
    pre-commit==4.2.0 \
    ipykernel==6.29.0 \

# Install project dependencies from specific directories
echo "📦 Installing project dependencies..."

# Install dependencies for metrics module
if [ -f "vpn/metrics/requirements.txt" ]; then
    echo "📊 Installing metrics dependencies..."
    pip3 install --no-cache-dir -r vpn/metrics/requirements.txt
fi

# Install the project in development mode if setup.py exists
# We're not using -e flag to avoid issues with multiple packages
if [ -f "setup.py" ]; then
    echo "🔧 Installing project in development mode..."
    pip3 install --no-cache-dir -e . || echo "⚠️ Could not install package in development mode"
fi

# Configure pre-commit if it exists
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🔧 Setting up pre-commit hooks..."
    pre-commit install
else
    echo "ℹ️ No pre-commit configuration found"
fi

# Verify installed tools
echo "🔍 Verifying development tools..."
python3 --version
echo "Black: $(black --version)"
echo "isort: $(isort --version)"
echo "mypy: $(mypy --version)"
echo "pylint: $(pylint --version)"
echo "pytest: $(pytest --version)"
echo "flake8: $(flake8 --version)"

# Create useful development aliases
echo "🔧 Setting up useful aliases..."
if ! grep -q "formatcode" ~/.bashrc; then
    echo 'alias formatcode="black . && isort ."' >> ~/.bashrc
    echo 'alias lint="pylint --recursive=y ."' >> ~/.bashrc
    echo 'alias typecheck="mypy ."' >> ~/.bashrc
    echo 'alias testall="pytest"' >> ~/.bashrc
fi

echo "✅ Development environment setup completed!"
echo "   To format code: formatcode"
echo "   To check code: lint"
echo "   To check types: typecheck"
echo "   To run tests: testall"

