import os
import time
import requests
import itertools
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class EtherscanAPIClient:
    """Simple Etherscan API client with support for multiple API keys and basic retry/rotation.

    Usage:
      - Provide multiple keys via the ETHERSCAN_API_KEYS env var as a comma-separated list,
        or provide a single key via ETHERSCAN_API_KEY.
      - The client will round-robin keys on each request and attempt simple retries on failures
        and common rate-limit messages.
    """

    BASE_URL = "https://api.etherscan.io/api"

    def __init__(self, api_keys: Optional[List[str]] = None, timeout: int = 15, max_retries: int = 3):
        # Load keys from arguments or environment
        keys = api_keys or []
        env_keys = os.environ.get('ETHERSCAN_API_KEYS')
        single_key = os.environ.get('ETHERSCAN_API_KEY')

        if env_keys:
            # allow comma or whitespace separated
            parts = [p.strip() for p in env_keys.replace(';', ',').split(',') if p.strip()]
            keys.extend(parts)

        if single_key:
            keys.append(single_key.strip())

        # Deduplicate while preserving order
        seen = set()
        unique_keys = []
        for k in keys:
            if k and k not in seen:
                unique_keys.append(k)
                seen.add(k)

        if not unique_keys:
            logger.warning('No Etherscan API key found in environment (ETHERSCAN_API_KEYS or ETHERSCAN_API_KEY).')

        self.keys = unique_keys
        # iterator for round-robin keys; if no keys, iterator yields None repeatedly
        self._key_cycle = itertools.cycle(self.keys) if self.keys else itertools.cycle([None])
        self.timeout = timeout
        self.max_retries = max_retries

    def _next_key(self) -> Optional[str]:
        k = next(self._key_cycle)
        return k

    def _get(self, params: Dict[str, Any]) -> Any:
        """Internal GET helper that handles key rotation and basic retry/backoff.

        Returns the parsed JSON 'result' when possible, or raw JSON on unexpected shapes.
        On persistent failure, returns None or an empty list depending on expected result shape.
        """
        attempt = 0
        last_exception = None

        while attempt < self.max_retries:
            key = self._next_key()
            if key:
                params['apikey'] = key
            else:
                # ensure any existing apikey param is removed
                params.pop('apikey', None)

            try:
                resp = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            except Exception as e:
                last_exception = e
                wait = 2 ** attempt
                logger.debug('Etherscan request error (attempt %s): %s -- retrying in %ss', attempt+1, e, wait)
                time.sleep(wait)
                attempt += 1
                continue

            # Try to parse JSON
            try:
                data = resp.json()
            except ValueError:
                last_exception = ValueError('Invalid JSON response from Etherscan')
                logger.debug('Invalid JSON response from Etherscan, status=%s', resp.status_code)
                time.sleep(1)
                attempt += 1
                continue

            # Etherscan sometimes returns {"status":"0","message":"No transactions found","result":[]} which is OK
            # When rate-limited, you may get a 403/429 or a JSON message with result='Max rate limit reached' or message 'NOTOK'
            status = str(data.get('status', '')) if isinstance(data.get('status', None), (str, int)) else ''
            message = data.get('message', '')

            # If HTTP status indicates rate limit, rotate and retry
            if resp.status_code in (429, 403):
                logger.warning('Etherscan rate-limited (HTTP %s). Rotating key and retrying.', resp.status_code)
                attempt += 1
                time.sleep(1 + attempt)
                continue

            # Some Etherscan responses have status '0' but are valid (no data), return result
            if status == '1' or (status == '0' and isinstance(data.get('result'), (list, str, dict))):
                return data.get('result', data)

            # If message indicates rate limit, rotate and retry
            if isinstance(message, str) and ('rate limit' in message.lower() or 'max rate' in message.lower() or 'notok' in message.lower()):
                logger.warning('Etherscan returned rate-limit message: %s. Rotating key and retrying.', message)
                attempt += 1
                time.sleep(1 + attempt)
                continue

            # If response looks like an error but not rate limit, return result if present else full data
            return data.get('result', data)

        # Exhausted retries
        logger.error('Etherscan requests exhausted retries. Last error: %s', last_exception)
        return None

    def get_account_balance(self, address: str) -> Optional[float]:
        """Return ETH balance in ETH (float) or None on error."""
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': 'latest'
        }

        result = self._get(params)
        if result is None:
            return None

        # Etherscan returns balance as string of wei
        try:
            # if the client returned the whole response (dict) try to extract
            if isinstance(result, dict) and 'result' in result:
                val = result['result']
            else:
                val = result
            return float(val) / 1e18
        except Exception:
            return None

    def get_normal_transactions(self, address: str, page: int = 1, offset: int = 100, sort: str = 'desc') -> List[Dict[str, Any]]:
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'page': page,
            'offset': offset,
            'sort': sort
        }
        result = self._get(params)
        if isinstance(result, list):
            return result
        # If result is None or dict, return empty list to let callers add red flags
        return []

    def get_internal_transactions(self, address: str, page: int = 1, offset: int = 100, sort: str = 'desc') -> List[Dict[str, Any]]:
        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'page': page,
            'offset': offset,
            'sort': sort
        }
        result = self._get(params)
        if isinstance(result, list):
            return result
        return []

    def get_token_transfers(self, address: str, page: int = 1, offset: int = 100, sort: str = 'desc') -> List[Dict[str, Any]]:
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'page': page,
            'offset': offset,
            'sort': sort
        }
        result = self._get(params)
        if isinstance(result, list):
            return result
        return []
