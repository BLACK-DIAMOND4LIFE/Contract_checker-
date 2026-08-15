import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from etherscan_client import EtherscanAPIClient

class TransactionPatternAnalyzer:
    """Analyze transaction patterns for suspicious activity"""
    
    def __init__(self):
        self.api_client = EtherscanAPIClient()
        self.logger = logging.getLogger(__name__)
    
    def analyze_transaction_patterns(self, address: str) -> Dict[str, Any]:
        """Analyze contract transaction patterns"""
        self.logger.info(f"Analyzing transaction patterns for {address}")
        
        pattern_analysis = {
            'contract_address': address,
            'analysis_timestamp': datetime.now().isoformat(),
            'normal_transactions': [],
            'internal_transactions': [],
            'token_transfers': [],
            'transaction_frequency': 'unknown',
            'pattern_status': 'unknown',
            'red_flags': [],
            'warnings': [],
            'statistics': {
                'total_transactions': 0,
                'transactions_7d': 0,
                'transactions_30d': 0,
                'avg_transaction_value': 0.0,
                'large_outflows': []
            }
        }
        
        # Get normal transactions
        normal_txs = self.api_client.get_normal_transactions(address, page=1, offset=100)
        
        if normal_txs and isinstance(normal_txs, list):
            pattern_analysis['normal_transactions'] = normal_txs[:50]
            pattern_analysis['statistics']['total_transactions'] = len(normal_txs)
            
            # Analyze transaction frequency and patterns
            now = datetime.now()
            transactions_7d = 0
            transactions_30d = 0
            total_value = 0
            large_outflows = []
            
            for tx in normal_txs[:100]:
                try:
                    tx_timestamp = int(tx.get('timeStamp', 0))
                    tx_datetime = datetime.fromtimestamp(tx_timestamp)
                    days_old = (now - tx_datetime).days
                    
                    if days_old <= 7:
                        transactions_7d += 1
                    if days_old <= 30:
                        transactions_30d += 1
                    
                    # Track large outflows
                    value = float(tx.get('value', 0)) / 1e18
                    total_value += value
                    
                    if value > 1.0 and tx.get('from', '').lower() == address.lower():
                        large_outflows.append({
                            'hash': tx.get('hash'),
                            'value': value,
                            'timestamp': tx_datetime.isoformat()
                        })
                
                except (ValueError, KeyError):
                    continue
            
            pattern_analysis['statistics']['transactions_7d'] = transactions_7d
            pattern_analysis['statistics']['transactions_30d'] = transactions_30d
            
            if len(normal_txs) > 0:
                pattern_analysis['statistics']['avg_transaction_value'] = total_value / len(normal_txs)
            
            # Check for sudden large withdrawals (rug-pull indicator)
            if large_outflows:
                pattern_analysis['statistics']['large_outflows'] = large_outflows
                if len(large_outflows) > 5:
                    pattern_analysis['red_flags'].append('WARNING: Multiple large outflows detected')
            
            # Determine transaction frequency
            if transactions_7d == 0 and pattern_analysis['statistics']['total_transactions'] > 0:
                pattern_analysis['warnings'].append('WARNING: No transactions in last 7 days')
                pattern_analysis['transaction_frequency'] = 'inactive'
            elif transactions_7d > 10:
                pattern_analysis['transaction_frequency'] = 'high'
            elif transactions_7d > 1:
                pattern_analysis['transaction_frequency'] = 'regular'
            elif pattern_analysis['statistics']['total_transactions'] > 0:
                pattern_analysis['transaction_frequency'] = 'low'
            else:
                pattern_analysis['red_flags'].append('CRITICAL: No transactions found')
                pattern_analysis['transaction_frequency'] = 'none'
        else:
            pattern_analysis['red_flags'].append('CRITICAL: Could not retrieve transaction history')
        
        # Get internal transactions
        internal_txs = self.api_client.get_internal_transactions(address)
        if internal_txs and isinstance(internal_txs, list):
            pattern_analysis['internal_transactions'] = internal_txs[:20]
            if len(internal_txs) > 10:
                pattern_analysis['warnings'].append('WARNING: Multiple hidden internal transactions detected')
        
        # Get token transfers
        token_transfers = self.api_client.get_token_transfers(address, page=1, offset=100)
        if token_transfers and isinstance(token_transfers, list):
            pattern_analysis['token_transfers'] = token_transfers[:50]
        
        # Determine pattern status
        if pattern_analysis['transaction_frequency'] == 'none':
            pattern_analysis['pattern_status'] = 'suspicious'
        elif pattern_analysis['transaction_frequency'] == 'inactive':
            pattern_analysis['pattern_status'] = 'irregular'
        else:
            pattern_analysis['pattern_status'] = 'regular'
        
        return pattern_analysis
    
    def detect_rug_pull_indicators(self, pattern_analysis: Dict[str, Any]) -> List[str]:
        """Detect specific rug-pull indicators"""
        indicators = []
        
        stats = pattern_analysis.get('statistics', {})
        
        # Sudden large withdrawal
        if stats.get('large_outflows'):
            indicators.append('CRITICAL: Recent large outflows detected')
        
        # No recent activity with history
        if pattern_analysis.get('transaction_frequency') == 'inactive' and stats.get('total_transactions', 0) > 10:
            indicators.append('WARNING: Recent inactivity after high activity period')
        
        # Hidden internal transactions
        if len(pattern_analysis.get('internal_transactions', [])) > 20:
            indicators.append('WARNING: Suspicious internal transaction volume')
        
        return indicators
