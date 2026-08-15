# Contract Verification Scanner for Investment Safety

A comprehensive DeFi contract verification and risk assessment tool that analyzes smart contracts for authenticity, financial health, and suspicious activity patterns to prevent investment in fraudulent or unsafe protocols.

## Features

### 🔍 **Contract Authenticity Verification**
- Verify contract source code availability on Etherscan
- Check contract verification status
- Analyze contract ABI to identify intended functionality
- Cross-reference with protocol documentation
- Detect red flags like hidden backdoor functions

### 💰 **Financial Health Analysis**
- Check ETH balance and liquidity
- Analyze token holdings and diversification
- Calculate total value locked (TVL)
- Identify concentrated holdings (rug-pull indicator)
- Verify adequate fund reserves

### 📊 **Transaction Pattern Analysis**
- Analyze recent transaction history
- Identify transaction frequency and regularity
- Detect sudden large withdrawals (rug-pull signals)
- Monitor internal transaction patterns
- Track token transfer events

### ⚠️ **Risk Assessment**
- Comprehensive risk scoring (0-100)
- Multi-factor risk evaluation
- Clear investment recommendations
- Detailed red flag identification
- Actionable security insights

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kroid485/Contract_checker-.git
   cd Contract_checker-
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Etherscan API**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Etherscan API key:
   ```
   ETHERSCAN_API_KEY=your_api_key_here
   ```

   Get a free API key at https://etherscan.io/apis

## Usage

### Basic Usage

1. **Prepare CSV file** with contract addresses (`contracts.csv`):
   ```csv
   Protocol Name,Chain,Category,Contract Address
   aave-v1,Ethereum,Withdrawal,0x3dfd23A6c5E8BbcFc9581d2E864a68feb6a076d3
   aperocket,Ethereum,Withdrawal,0x101bCD396DDFb934072a171Bc4F625B85D505C78
   ```

2. **Run the scanner**
   ```bash
   python scanner.py contracts.csv
   ```

3. **Review results** in the `results/` directory:
   - `assessment_results.json` - Full detailed assessment
   - `assessment_summary.csv` - Quick reference summary
   - `assessment_report.txt` - Human-readable report

### Output Format

#### Risk Levels
- **🔴 Critical**: Extreme risk, likely fraudulent (Risk Score: 75-100)
- **🟠 High**: Significant risk factors present (Risk Score: 50-74)
- **🟡 Medium**: Some concerning indicators (Risk Score: 25-49)
- **🟢 Low**: Appears legitimate and safe (Risk Score: 0-24)

#### Recommendations
- **❌ AVOID**: Do not invest
- **⚠️ INVEST WITH EXTREME CAUTION**: High risk, only if you understand the risks
- **⚡ INVEST WITH CAUTION**: Some concerns, thorough due diligence recommended
- **✅ INVEST**: Appears safe to invest

## Architecture

### Core Modules

- **`etherscan_client.py`** - Etherscan API client with rate limiting
- **`contract_verifier.py`** - Contract authenticity verification
- **`financial_analyzer.py`** - Financial health analysis
- **`transaction_analyzer.py`** - Transaction pattern analysis
- **`risk_assessment.py`** - Comprehensive risk scoring
- **`batch_processor.py`** - Batch processing and report generation
- **`scanner.py`** - Main entry point

## Security Disclaimer

⚠️ **This tool is for educational and research purposes only.** It does not guarantee the safety or legitimacy of any contract. Always conduct thorough due diligence before investing in any DeFi protocol.

## License

MIT License - See LICENSE file for details