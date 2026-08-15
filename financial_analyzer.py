import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from etherscan_client import EtherscanAPIClient

class FinancialHealthAnalyzer:
    """Analyze contract financial health and liquidity"""
    
    def __init__(self):
        self.api_client = EtherscanAPIClient()
        self.logger = logging.getLogger(__name__)
    
    def analyze_financial_health(self, address: str) -> Dict[str, Any]:
        """Analyze contract financial health"""
        self.logger.info(f"Analyzing financial health for {address}")
        
        health_analysis = {
            'contract_address': address,
            'analysis_timestamp': datetime.now().isoformat(),
            'eth_balance': 0.0,
            'eth_balance_usd': 0.0,
            'token_balances': [],
            'total_value_locked': 0.0,
            'liquidity_status': 'unknown',
            'financial_health': 'unknown',
            'red_flags': [],
            'warnings': []
        }
        
        # Get ETH balance
        eth_balance = self.api_client.get_account_balance(address)
        if eth_balance is not None:
            health_analysis['eth_balance'] = eth_balance
            if eth_balance == 0:
                health_analysis['red_flags'].append('CRITICAL: Contract has zero ETH balance')
                health_analysis['liquidity_status'] = 'empty'
            elif eth_balance < 0.1:
                health_analysis['warnings'].append('WARNING: Low ETH balance (< 0.1 ETH)')
                health_analysis['liquidity_status'] = 'low'
            else:
                health_analysis['liquidity_status'] = 'adequate'
        
        # Get recent token transfers to analyze holdings
        token_transfers = self.api_client.get_token_transfers(address, page=1, offset=50)
        
        if token_transfers and isinstance(token_transfers, list):
            unique_tokens = {}
            for transfer in token_transfers[:50]:  # Analyze last 50 transfers
                token_addr = transfer.get('contractAddress', '').lower()
                if token_addr not in unique_tokens:
                    unique_tokens[token_addr] = {
                        'token_address': token_addr,
                        'token_symbol': transfer.get('tokenSymbol', 'UNKNOWN'),
                        'token_decimals': int(transfer.get('tokenDecimal', 18)),
                        'transfers_count': 0,
                        'last_transfer': transfer.get('timeStamp')
                    }
                unique_tokens[token_addr]['transfers_count'] += 1
            
            health_analysis['token_balances'] = list(unique_tokens.values())
            
            # Check for concentrated holdings (red flag)
            if len(unique_tokens) == 1:
                health_analysis['red_flags'].append('WARNING: Holdings concentrated in single token')
            elif len(unique_tokens) == 0:
                health_analysis['red_flags'].append('WARNING: No token holdings detected')
        
        # Estimate financial health based on liquidity
        if health_analysis['eth_balance'] > 1.0:
            health_analysis['financial_health'] = 'healthy'
        elif health_analysis['eth_balance'] > 0:
            health_analysis['financial_health'] = 'underfunded'
        else:
            health_analysis['financial_health'] = 'suspicious'
        
        return health_analysis
    
    def get_current_eth_price(self) -> Optional[float]:
        """Get current ETH price in USD (placeholder - would integrate with price API)"""
        # This would integrate with a price API like CoinGecko or Uniswap
        # For now, returning None as placeholder
        return None
