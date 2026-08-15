# Setup Guide

## Prerequisites
- Python 3.8 or higher
- pip package manager
- Etherscan API key (free)

## Step-by-Step Setup

### 1. Clone Repository
```bash
git clone https://github.com/Kroid485/Contract_checker-.git
cd Contract_checker-
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Get Etherscan API Key
1. Visit https://etherscan.io/apis
2. Create a free account
3. Generate a new API key
4. Copy the API key

### 5. Configure Environment
```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your API key
# Linux/macOS:
nano .env

# Windows:
type .env.example > .env
edit .env
```

### 6. Prepare Contract List
Create `contracts.csv` with your contract addresses:
```csv
Protocol Name,Chain,Category,Contract Address
aave-v1,Ethereum,Withdrawal,0x3dfd23A6c5E8BbcFc9581d2E864a68feb6a076d3
aperocke,Ethereum,Withdrawal,0x101bCD396DDFb934072a171Bc4F625B85D505C78
```

### 7. Run Scanner
```bash
python scanner.py contracts.csv
```

### 8. View Results
Results are saved in `results/` directory:
- `assessment_results.json` - Full technical report
- `assessment_summary.csv` - Quick summary
- `assessment_report.txt` - Human-readable report

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'requests'"
**Solution:** Install requirements
```bash
pip install -r requirements.txt
```

### Issue: "ETHERSCAN_API_KEY not set"
**Solution:** Make sure .env file exists with API key
```bash
cat .env
# Should show: ETHERSCAN_API_KEY=your_key_here
```

### Issue: Rate limit errors
**Solution:** Increase delays in .env
```
REQUEST_DELAY=0.5
RETRY_DELAY=10
```

## Verification

To verify everything is working:
```bash
# Run with a single test contract
echo 'Protocol,Chain,Category,Address
test,Ethereum,Withdrawal,0x3dfd23A6c5E8BbcFc9581d2E864a68feb6a076d3' > test.csv
python scanner.py test.csv
```

If you see a `results/` directory with files, the setup is complete!
