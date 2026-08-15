import logging
import json
import csv
import os
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from risk_assessment import RiskAssessment

class BatchProcessor:
    """Process multiple contracts in batch"""
    
    def __init__(self, output_dir: str = './results'):
        self.output_dir = output_dir
        self.risk_assessor = RiskAssessment()
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def process_batch(self, contracts: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Process a batch of contracts"""
        self.logger.info(f"Processing batch of {len(contracts)} contracts")
        
        results = []
        high_risk_contracts = []
        
        for idx, contract in enumerate(contracts, 1):
            address = contract.get('Contract Address', '').strip()
            protocol = contract.get('Protocol Name', 'Unknown')
            
            if not address:
                self.logger.warning(f"Skipping contract {idx}: Invalid address")
                continue
            
            self.logger.info(f"Processing {idx}/{len(contracts)}: {protocol} - {address}")
            
            try:
                assessment = self.risk_assessor.assess_contract(address)
                assessment['protocol'] = protocol
                assessment['category'] = contract.get('Category', 'Unknown')
                assessment['chain'] = contract.get('Chain', 'Unknown')
                
                results.append(assessment)
                
                # Track high-risk contracts
                if assessment['risk_level'] in ['high', 'critical']:
                    high_risk_contracts.append({
                        'address': address,
                        'protocol': protocol,
                        'risk_level': assessment['risk_level'],
                        'recommendation': assessment['recommendation']
                    })
                
            except Exception as e:
                self.logger.error(f"Error processing {address}: {e}")
                results.append({
                    'contract_address': address,
                    'protocol': protocol,
                    'error': str(e),
                    'risk_level': 'unknown'
                })
        
        return results
    
    def save_results_json(self, results: List[Dict[str, Any]], filename: str = 'assessment_results.json') -> str:
        """Save results to JSON file"""
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Results saved to {filepath}")
        return filepath
    
    def save_results_csv(self, results: List[Dict[str, Any]], filename: str = 'assessment_summary.csv') -> str:
        """Save summary results to CSV file"""
        filepath = os.path.join(self.output_dir, filename)
        
        # Extract key fields for CSV
        csv_data = []
        for result in results:
            csv_data.append({
                'Contract Address': result.get('contract_address', ''),
                'Protocol': result.get('protocol', ''),
                'Chain': result.get('chain', ''),
                'Category': result.get('category', ''),
                'Risk Level': result.get('risk_level', 'unknown'),
                'Risk Score': result.get('risk_score', 0),
                'Recommendation': result.get('recommendation', ''),
                'Is Verified': result.get('verification', {}).get('is_verified', False),
                'Financial Health': result.get('financial_health', {}).get('financial_health', 'unknown'),
                'Transaction Status': result.get('transaction_patterns', {}).get('pattern_status', 'unknown'),
                'Red Flags Count': len(result.get('all_red_flags', [])),
                'Assessment Timestamp': result.get('assessment_timestamp', '')
            })
        
        if csv_data:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)
        
        self.logger.info(f"Summary saved to {filepath}")
        return filepath
    
    def generate_report(self, results: List[Dict[str, Any]], filename: str = 'assessment_report.txt') -> str:
        """Generate human-readable report"""
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("CONTRACT VERIFICATION AND RISK ASSESSMENT REPORT\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary statistics
            total = len(results)
            critical = len([r for r in results if r.get('risk_level') == 'critical'])
            high = len([r for r in results if r.get('risk_level') == 'high'])
            medium = len([r for r in results if r.get('risk_level') == 'medium'])
            low = len([r for r in results if r.get('risk_level') == 'low'])
            
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Contracts Assessed: {total}\n")
            f.write(f"  - Critical Risk: {critical}\n")
            f.write(f"  - High Risk: {high}\n")
            f.write(f"  - Medium Risk: {medium}\n")
            f.write(f"  - Low Risk: {low}\n\n")
            
            # High-risk contracts
            high_risk = [r for r in results if r.get('risk_level') in ['critical', 'high']]
            if high_risk:
                f.write("HIGH-RISK CONTRACTS (AVOID)\n")
                f.write("-" * 80 + "\n")
                for contract in high_risk:
                    f.write(f"\nAddress: {contract.get('contract_address')}\n")
                    f.write(f"Protocol: {contract.get('protocol')}\n")
                    f.write(f"Risk Level: {contract.get('risk_level').upper()}\n")
                    f.write(f"Recommendation: {contract.get('recommendation').upper()}\n")
                    f.write(f"Red Flags: {len(contract.get('all_red_flags', []))}\n")
                    if contract.get('all_red_flags'):
                        for flag in contract.get('all_red_flags', [])[:5]:
                            f.write(f"  - {flag}\n")
                    f.write("\n")
            
            # Medium-risk contracts
            medium_risk = [r for r in results if r.get('risk_level') == 'medium']
            if medium_risk:
                f.write("\nMEDIUM-RISK CONTRACTS (CAUTION)\n")
                f.write("-" * 80 + "\n")
                for contract in medium_risk[:10]:  # Show first 10
                    f.write(f"\nAddress: {contract.get('contract_address')}\n")
                    f.write(f"Protocol: {contract.get('protocol')}\n")
                    f.write(f"Recommendation: {contract.get('recommendation')}\n")
            
            # Detailed findings
            f.write("\n" + "=" * 80 + "\n")
            f.write("DETAILED FINDINGS\n")
            f.write("=" * 80 + "\n")
            for result in results:
                if 'error' not in result:
                    f.write(f"\n{result.get('protocol')} - {result.get('contract_address')}\n")
                    f.write(result.get('summary', 'No summary available'))
                    f.write("\n" + "-" * 80 + "\n")
        
        self.logger.info(f"Report saved to {filepath}")
        return filepath
