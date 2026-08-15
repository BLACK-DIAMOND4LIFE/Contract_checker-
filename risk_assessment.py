import logging
from datetime import datetime
from typing import Dict, Any, List

try:
    from financial_analyzer import FinancialHealthAnalyzer
except Exception:
    FinancialHealthAnalyzer = None

try:
    from transaction_analyzer import TransactionPatternAnalyzer
except Exception:
    TransactionPatternAnalyzer = None

logger = logging.getLogger(__name__)


class RiskAssessment:
    """Simple RiskAssessment implementation that integrates available analyzers.

    This implementation is intentionally lightweight so the scanner can run out-of-the-box
    even if external API clients (like an Etherscan client) are missing. It will:
    - call FinancialHealthAnalyzer.analyze_financial_health() if available
    - call TransactionPatternAnalyzer.analyze_transaction_patterns() if available
    - compute a heuristic risk_score and risk_level
    - return a dictionary with the keys expected by batch_processor/scanner
    """

    def __init__(self):
        self.logger = logger
        self.financial = FinancialHealthAnalyzer() if FinancialHealthAnalyzer else None
        self.tx_analyzer = TransactionPatternAnalyzer() if TransactionPatternAnalyzer else None

    def assess_contract(self, address: str) -> Dict[str, Any]:
        """Assess a single contract address and return a structured result."""
        ts = datetime.utcnow().isoformat()
        result: Dict[str, Any] = {
            'contract_address': address,
            'assessment_timestamp': ts,
            'risk_score': 0,
            'risk_level': 'unknown',
            'recommendation': 'invest',
            'verification': {'is_verified': False, 'note': 'verification module not present'},
            'financial_health': {'financial_health': 'unknown'},
            'transaction_patterns': {'pattern_status': 'unknown'},
            'all_red_flags': [],
            'summary': ''
        }

        # Financial analysis
        try:
            if self.financial:
                health = self.financial.analyze_financial_health(address)
                result['financial_health'] = health
                # propagate red flags
                rflags = health.get('red_flags', []) or []
                result['all_red_flags'].extend(rflags)
            else:
                self.logger.debug('FinancialHealthAnalyzer not available; skipping financial analysis')
        except Exception as e:
            self.logger.exception('Error running financial analysis: %s', e)
            result['all_red_flags'].append(f'ERROR: financial analysis failed: {e}')

        # Transaction pattern analysis
        try:
            if self.tx_analyzer:
                patterns = self.tx_analyzer.analyze_transaction_patterns(address)
                result['transaction_patterns'] = patterns
                rflags = patterns.get('red_flags', []) or []
                result['all_red_flags'].extend(rflags)
                # include any detected rug-pull indicators
                try:
                    indicators = self.tx_analyzer.detect_rug_pull_indicators(patterns)
                    result['all_red_flags'].extend(indicators)
                except Exception:
                    # not critical if detect method is missing or fails
                    pass
            else:
                self.logger.debug('TransactionPatternAnalyzer not available; skipping transaction analysis')
        except Exception as e:
            self.logger.exception('Error running transaction analysis: %s', e)
            result['all_red_flags'].append(f'ERROR: transaction analysis failed: {e}')

        # Basic heuristic scoring
        score = 0

        # Score from financial health
        fh = result.get('financial_health', {})
        fh_state = fh.get('financial_health') if isinstance(fh, dict) else None
        if fh_state == 'suspicious':
            score += 60
        elif fh_state == 'underfunded':
            score += 30
        elif fh_state == 'healthy':
            score += 5
        else:
            # unknown or missing -> small penalty
            score += 10

        # Score from transaction patterns
        tp = result.get('transaction_patterns', {})
        pattern_status = tp.get('pattern_status') if isinstance(tp, dict) else None
        if pattern_status == 'suspicious':
            score += 30
        elif pattern_status == 'irregular':
            score += 15
        elif pattern_status == 'regular':
            score += 0
        else:
            score += 5

        # Add points per red flag / indicator
        red_flags = result.get('all_red_flags', []) or []
        score += min(len(red_flags) * 8, 40)  # each flag adds up to 8 points, cap 40

        # Normalize and clamp to 0-100
        score = max(0, min(int(score), 100))
        result['risk_score'] = score

        # Map score -> level
        if score >= 75:
            level = 'critical'
            rec = 'avoid'
        elif score >= 50:
            level = 'high'
            rec = 'invest_with_extreme_caution'
        elif score >= 25:
            level = 'medium'
            rec = 'invest_with_caution'
        else:
            level = 'low'
            rec = 'invest'

        result['risk_level'] = level
        result['recommendation'] = rec

        # Build a human-readable summary
        summary_lines: List[str] = []
        summary_lines.append(f'Assessment for {address} at {ts}')
        summary_lines.append(f'Risk score: {score} ({level})')
        if result['all_red_flags']:
            summary_lines.append('Red flags:')
            for flag in result['all_red_flags'][:10]:
                summary_lines.append(f' - {flag}')
        else:
            summary_lines.append('No red flags detected')

        result['summary'] = '\n'.join(summary_lines)

        return result
