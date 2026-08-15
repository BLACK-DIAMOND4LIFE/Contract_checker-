import csv
import logging
import sys
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

def main():
    """Main scanner application"""
    
    print("=" * 80)
    print("CONTRACT VERIFICATION AND RISK ASSESSMENT SCANNER")
    print("=" * 80)
    print()
    
    # Check if CSV file is provided
    csv_file = 'contracts.csv'
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    # Verify CSV file exists
    if not Path(csv_file).exists():
        print(f"Error: CSV file '{csv_file}' not found")
        print(f"\nUsage: python main.py [contracts.csv]")
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
