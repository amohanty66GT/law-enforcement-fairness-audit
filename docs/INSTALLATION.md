# Installation Guide

## Prerequisites

- Python 3.11 or higher
- Git
- 4GB+ RAM recommended
- Internet connection for API access

## Quick Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/law-enforcement-fairness-audit.git
cd law-enforcement-fairness-audit
```

### 2. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using conda
conda env create -f environment.yml
conda activate fairness-audit
```

### 3. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env
```

### 4. Test Installation

```bash
# Run component tests
python test_analysis.py

# Should output: "🎉 All tests passed!"
```

## Platform-Specific Instructions

### Windows

```powershell
# Install Python from python.org or Microsoft Store
# Install Git from git-scm.com

# Clone and setup
git clone https://github.com/yourusername/law-enforcement-fairness-audit.git
cd law-enforcement-fairness-audit
py -m pip install -r requirements.txt
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python git

# Clone and setup
git clone https://github.com/yourusername/law-enforcement-fairness-audit.git
cd law-enforcement-fairness-audit
pip3 install -r requirements.txt
```

### Linux (Ubuntu/Debian)

```bash
# Install Python and Git
sudo apt update
sudo apt install python3 python3-pip git

# Clone and setup
git clone https://github.com/yourusername/law-enforcement-fairness-audit.git
cd law-enforcement-fairness-audit
pip3 install -r requirements.txt
```

## Using Make (Optional)

If you have `make` installed:

```bash
# Complete setup
make setup

# Run analysis
make run-analysis

# Start dashboard
make dashboard
```

## Docker Installation (Alternative)

```bash
# Build Docker image
docker build -t fairness-audit .

# Run analysis
docker run -v $(pwd)/output:/app/output fairness-audit python scripts/run_simple_analysis.py

# Run dashboard
docker run -p 8501:8501 fairness-audit python scripts/start_simple_dashboard.py
```

## Troubleshooting

### Common Issues

**1. ModuleNotFoundError**
```bash
# Ensure you're in the project directory
cd law-enforcement-fairness-audit

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**2. Permission Errors (Windows)**
```powershell
# Run as administrator or use:
py -m pip install --user -r requirements.txt
```

**3. SSL Certificate Errors**
```bash
# For corporate networks
pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org
```

**4. Memory Issues**
```bash
# Reduce sample size in scripts/run_simple_analysis.py
# Change n_records = 1000 to n_records = 500
```

### Getting Help

1. Check [GitHub Issues](https://github.com/yourusername/law-enforcement-fairness-audit/issues)
2. Run diagnostic: `python test_analysis.py`
3. Check logs in `logs/` directory
4. Verify Python version: `python --version` (should be 3.11+)

## Next Steps

After installation:

1. **Run Analysis**: `python scripts/run_simple_analysis.py --data-source sample`
2. **Start Dashboard**: `python scripts/start_simple_dashboard.py`
3. **View Results**: Check `output/` directory
4. **Read Documentation**: See `docs/` folder for detailed guides