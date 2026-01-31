"""
Bybit RSA 交易客戶端 v1.3
公開數據用 CoinGecko + 快取，私有 API 用 Bybit
"""

import os
import time
import base64
import logging
import aiohttp

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "")
BYBIT_PRIVATE_KEY = os.getenv("BYBIT_PRIVATE_KEY", "")
BASE_URL = "https://api.bybit.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# CoinGecko 幣種對應
COINGECKO_IDS = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum", 
    "SOLUSDT": "solana"
}

# 價格快取（避免 429 限流）
_price_cache = {}
_cache_time = {}
CACHE_DURATION = 60  # 快取 60 秒

def load_private_key(private_key_str: str):
    if not HAS_CRYPTO:
        raise ImportError("cryptography not installed")
    private_key_str = private_key_str.replace("\\n", "\n")
    return serialization.load_pem_private_key(private_key_str.encode(), password=None, backend=default_backend())

def generate_signature(private_key, param_str: str) -> str:
    signature = private_key.sign(param_str.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode('utf-8')

class BybitTrader:
    def __init__(self):
        self.api_key = BYBIT_API_KEY
        self.private_key_str = BYBIT_PRIVATE_KEY
        self.private_key = None
        self.recv_window = "5000"
        if self.private_key_str and HAS_CRYPTO:
            try:
                self.private_key = load_private_key(self.private_key_str)
                logger.info("✅ RSA 私鑰載入成功")
            except Exception as e:
                logger.error(f"❌ RSA 私鑰載入失敗: {e}")
    
    def _get_timestamp(self) -> str:
        return str(int(time.time() * 1000))
    
    def _sign_request(self, timestamp: str, params: dict = None) -> str:
        param_str = f"{timestamp}{self.api_key}{self.recv_window}"
        if params:
            sorted_params = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            param_str += sorted_params
        if self.private_key:
            return generate_signature(self.private_key, param_str)
        raise ValueError("私鑰未設置")
    
    def _get_headers(self, timestamp: str, signature: str) -> dict:
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-SIGN": signature,
            "X-BAPI-RECV-WINDOW": self.recv_window,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT
        }
    
    async def _request(self, method: str, endpoint: str, params: dict = None) -> dict:
        url = f"{BASE_URL}{endpoint}"
        timestamp = self._get_timestamp()
        try:
            signature = self._sign_request(timestamp, params)
            headers = self._get_headers(timestamp, signature)
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    if params:
                        query = "&".join([f"{k}={v}" for k, v in params.items()])
                        url = f"{url}?{query}"
                    async with session.get(url, headers=headers, timeout=15) as resp:
                        return await resp.json()
                else:
                    async with session.post(url, headers=headers, json=params, timeout=15) as resp:
                        return await resp.json()
        except Exception as e:
            logger.error(f"API 錯誤: {e}")
            return {"retCode": -1, "retMsg": str(e)}
    
    async def get_ticker(self, category: str = "linear", symbol: str = "BTCUSDT") -> dict:
        """用 CoinGecko 獲取價格（有快取避免 429）"""
        global _price_cache, _cache_time
        
        # 檢查快取
        now = time.time()
        if symbol in _price_cache and (now - _cache_time.get(symbol, 0)) < CACHE_DURATION:
            logger.info(f"📦 使用快取: {symbol}")
            return _price_cache[symbol]
        
        coin_id = COINGECKO_IDS.get(symbol, "bitcoin")
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        headers = {"User-Agent": USER_AGENT}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        market = data.get("market_data", {})
                        
                        result = {
                            "retCode": 0,
                            "result": {
                                "list": [{
                                    "symbol": symbol,
                                    "lastPrice": str(market.get("current_price", {}).get("usd", 0)),
                                    "price24hPcnt": str(market.get("price_change_percentage_24h", 0) / 100),
                                    "highPrice24h": str(market.get("high_24h", {}).get("usd", 0)),
                                    "lowPrice24h": str(market.get("low_24h", {}).get("usd", 0)),
                                    "volume24h": str(market.get("total_volume", {}).get("usd", 0))
                                }]
                            }
                        }
                        
                        # 存入快取
                        _price_cache[symbol] = result
                        _cache_time[symbol] = now
                        
                        return result
                    
                    elif resp.status == 429:
                        # 限流時使用舊快取
                        if symbol in _price_cache:
                            logger.warning(f"⚠️ 429 限流，使用舊快取: {symbol}")
                            return _price_cache[symbol]
                        return {"retCode": -1, "retMsg": "API 限流，請稍後再試"}
                    
                    return {"retCode": -1, "retMsg": f"CoinGecko 錯誤: {resp.status}"}
        except Exception as e:
            # 錯誤時使用舊快取
            if symbol in _price_cache:
                logger.warning(f"⚠️ 錯誤，使用舊快取: {symbol}")
                return _price_cache[symbol]
            logger.error(f"CoinGecko 錯誤: {e}")
            return {"retCode": -1, "retMsg": str(e)}
    
    async def get_funding_rate(self, category: str = "linear", symbol: str = "BTCUSDT") -> dict:
        """資金費率暫時返回 N/A"""
        return {"retCode": 0, "result": {"list": []}}
    
    async def get_wallet_balance(self, account_type: str = "UNIFIED") -> dict:
        return await self._request("GET", "/v5/account/wallet-balance", {"accountType": account_type})
    
    async def get_positions(self, category: str = "linear", symbol: str = None) -> dict:
        params = {"category": category}
        if symbol:
            params["symbol"] = symbol
        return await self._request("GET", "/v5/position/list", params)
    
    async def place_order(self, symbol: str, side: str, qty: str, order_type: str = "Market", category: str = "linear") -> dict:
        params = {"category": category, "symbol": symbol, "side": side, "orderType": order_type, "qty": qty}
        return await self._request("POST", "/v5/order/create", params)
    
    async def get_open_orders(self, category: str = "linear") -> dict:
        return await self._request("GET", "/v5/order/realtime", {"category": category})
    
    async def set_leverage(self, symbol: str, leverage: str, category: str = "linear") -> dict:
        return await self._request("POST", "/v5/position/set-leverage", {"category": category, "symbol": symbol, "buyLeverage": leverage, "sellLeverage": leverage})
