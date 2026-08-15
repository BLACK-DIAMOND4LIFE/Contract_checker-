#!/usr/bin/env python3
import csv
import logging
import sys
import os
import argparse
from pathlib import Path
from batch_processor import BatchProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def load_contracts_from_csv(filepath: str) -> list:
    """Load contract addresses from CSV file"""
    contracts = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                contracts.append(row)
        
        logger.info(f"Loaded {len(contracts)} contracts from {filepath}")
        return contracts
    
    except FileNotFoundError:
        logger.error(f"CSV file not found: {filepath}")
        return []
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return []

def _parse_api_keys_arg(arg: str) -> list:
    """Parse --api-keys argument which can be a comma-separated string or a path to a file."""
    if not arg:
        return []
    # path to file?
    if os.path.isfile(arg):
        keys = []
        with open(arg, 'r', encoding='utf-8') as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                # allow comma-separated keys on a single line too
                for k in ln.replace(';', ',').split(','):
                    k = k.strip()
                    if k:
                        keys.append(k)
        return keys
    # otherwise treat as comma-separated
    parts = [p.strip() for p in arg.replace(';', ',').split(',') if p.strip()]
    return parts

def main():
    """Main scanner application"""
    parser = argparse.ArgumentParser(description='Contract verification and risk assessment scanner')
    parser.add_argument('csv', nargs='?', default='contracts.csv', help='Path to contracts CSV file')
    parser.add_argument('--api-keys', help='Comma-separated Etherscan API keys or path to a file containing keys (one per line).', default=None)
    args = parser.parse_args()

    # If user provided --api-keys, set ETHERSCAN_API_KEYS so downstream modules see it
    if args.api_keys:
        keys = _parse_api_keys_arg(args.api_keys)
        if keys:
            os.environ['ETHERSCAN_API_KEYS'] = ','.join(keys)
            logger.info(f"Using {len(keys)} Etherscan API key(s) from --api-keys")
        else:
            logger.warning("No API keys parsed from --api-keys argument")

    # Also allow ETHERSCAN_API_KEYS or ETHERSCAN_API_KEY from environment
    env_keys_raw = os.environ.get('ETHERSCAN_API_KEYS') or os.environ.get('ETHERSCAN_API_KEY')
    if env_keys_raw:
        # Normalize to list to count
        if os.environ.get('ETHERSCAN_API_KEYS'):
            parsed = [p.strip() for p in os.environ['ETHERSCAN_API_KEYS'].replace(';', ',').split(',') if p.strip()]
        else:
            parsed = [os.environ.get('ETHERSCAN_API_KEY').strip()] if os.environ.get('ETHERSCAN_API_KEY') else []
        logger.info(f"Detected {len(parsed)} Etherscan API key(s) from environment")
    else:
        logger.warning("No Etherscan API keys found in environment. Set ETHERSCAN_API_KEYS (comma-separated) or ETHERSCAN_API_KEY, or pass --api-keys on the command line.")

    print("=" * 80)
    print("CONTRACT VERIFICATION AND RISK ASSESSMENT SCANNER")
    print("=" * 80)
    print()

    csv_file = args.csv

    # Verify CSV file exists
    if not Path(csv_file).exists():
        print(f"Error: CSV file '{csv_file}' not found")
        print(f"\nUsage: python scanner.py [contracts.csv] [--api-keys \"key1,key2,...\"]")
        print(f"\nExpected CSV format:")
        print("Protocol Name,Chain,Category,Contract Address")
        print("aave-v1,Ethereum,Withdrawal,0x3dfd23A6c5E8BbcFc9581d2E864a68feb6a076d3")
        sys.exit(1)

    # Load contracts from CSV
    contracts = load_contracts_from_csv(csv_file)
    
    if not contracts:
        print("No contracts to process")
        sys.exit(1)
    
    print(f"Found {len(contracts)} contracts to verify\n")
    
    # Initialize batch processor
    processor = BatchProcessor(output_dir='./results')
    
    # Process all contracts
    print("Starting verification process...")
    print("This may take several minutes depending on the number of contracts.\n")
    
    results = processor.process_batch(contracts)
    
    # Save results
    print("\nSaving results...")
    json_file = processor.save_results_json(results)
    csv_file_out = processor.save_results_csv(results)
    report_file = processor.generate_report(results)
    
    print(f"✓ JSON results: {json_file}")
    print(f"✓ CSV summary: {csv_file_out}")
    print(f"✓ Text report: {report_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    
    total = len(results)
    critical = len([r for r in results if r.get('risk_level') == 'critical'])
    high = len([r for r in results if r.get('risk_level') == 'high'])
    medium = len([r for r in results if r.get('risk_level') == 'medium'])
    low = len([r for r in results if r.get('risk_level') == 'low'])
    
    print(f"\nTotal Contracts Assessed: {total}")
    print(f"  🔴 Critical Risk: {critical}")
    print(f"  🟠 High Risk: {high}")
    print(f"  🟡 Medium Risk: {medium}")
    print(f"  🟢 Low Risk: {low}")
    
    # Recommendations summary
    avoid = len([r for r in results if r.get('recommendation') == 'avoid'])
    extreme_caution = len([r for r in results if r.get('recommendation') == 'invest_with_extreme_caution'])
    caution = len([r for r in results if r.get('recommendation') == 'invest_with_caution'])
    invest = len([r for r in results if r.get('recommendation') == 'invest'])
    
    print(f"\nInvestment Recommendations:")
    print(f"  ❌ AVOID: {avoid}")
    print(f"  ⚠️  INVEST WITH EXTREME CAUTION: {extreme_caution}")
    print(f"  ⚡ INVEST WITH CAUTION: {caution}")
    print(f"  ✅ INVEST: {invest}")
    
    print("\nAll results have been saved to the './results' directory")
    print("=" * 80)

if __name__ == '__main__':
    main()
