"""
交易客戶端 v2.0
- 公開數據：Binance API（穩定）
- 私有交易：Bybit API + 代理支援
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

# ═══════════════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════════════

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "")
BYBIT_PRIVATE_KEY = os.getenv("BYBIT_PRIVATE_KEY", "")
PROXY_URL = os.getenv("PROXY_URL", "")  # 可選代理，格式：http://user:pass@host:port

BYBIT_URL = "https://api.bybit.com"
BINANCE_URL = "https://api.binance.com"
BINANCE_FAPI_URL = "https://fapi.binance.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ═══════════════════════════════════════════════════════════════════════
# RSA 簽名
# ═══════════════════════════════════════════════════════════════════════

def load_private_key(private_key_str: str):
    if not HAS_CRYPTO:
        raise ImportError("cryptography not installed")
    private_key_str = private_key_str.replace("\\n", "\n")
    return serialization.load_pem_private_key(
        private_key_str.encode(), 
        password=None, 
        backend=default_backend()
    )

def generate_signature(private_key, param_str: str) -> str:
    signature = private_key.sign(
        param_str.encode('utf-8'), 
        padding.PKCS1v15(), 
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

# ═══════════════════════════════════════════════════════════════════════
# 交易客戶端
# ═══════════════════════════════════════════════════════════════════════

class BybitTrader:
    def __init__(self):
        self.api_key = BYBIT_API_KEY
        self.private_key_str = BYBIT_PRIVATE_KEY
        self.private_key = None
        self.recv_window = "5000"
        self.proxy = PROXY_URL if PROXY_URL else None
        
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
    
    # ═══════════════════════════════════════════════════════════════════
    # Bybit 私有 API（需要簽名 + 可選代理）
    # ═══════════════════════════════════════════════════════════════════
    
    async def _bybit_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Bybit 私有 API 請求"""
        url = f"{BYBIT_URL}{endpoint}"
        timestamp = self._get_timestamp()
        
        try:
            signature = self._sign_request(timestamp, params)
            headers = self._get_headers(timestamp, signature)
            
            connector = None
            if self.proxy:
                # 使用代理
                connector = aiohttp.TCPConnector()
            
            async with aiohttp.ClientSession(connector=connector) as session:
                if method == "GET":
                    if params:
                        query = "&".join([f"{k}={v}" for k, v in params.items()])
                        url = f"{url}?{query}"
                    async with session.get(url, headers=headers, proxy=self.proxy, timeout=15) as resp:
                        if resp.content_type == 'application/json':
                            return await resp.json()
                        else:
                            text = await resp.text()
                            return {"retCode": -1, "retMsg": f"非 JSON 回應: {text[:100]}"}
                else:
                    async with session.post(url, headers=headers, json=params, proxy=self.proxy, timeout=15) as resp:
                        if resp.content_type == 'application/json':
                            return await resp.json()
                        else:
                            text = await resp.text()
                            return {"retCode": -1, "retMsg": f"非 JSON 回應: {text[:100]}"}
        
        except Exception as e:
            logger.error(f"Bybit API 錯誤: {e}")
            return {"retCode": -1, "retMsg": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════
    # Binance 公開 API（價格、資金費率）
    # ═══════════════════════════════════════════════════════════════════
    
    async def get_ticker(self, category: str = "linear", symbol: str = "BTCUSDT") -> dict:
        """用 Binance 獲取即時價格"""
        url = f"{BINANCE_URL}/api/v3/ticker/24hr?symbol={symbol}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "retCode": 0,
                            "result": {
                                "list": [{
                                    "symbol": symbol,
                                    "lastPrice": data.get("lastPrice", "0"),
                                    "price24hPcnt": str(float(data.get("priceChangePercent", 0)) / 100),
                                    "highPrice24h": data.get("highPrice", "0"),
                                    "lowPrice24h": data.get("lowPrice", "0"),
                                    "volume24h": data.get("volume", "0")
                                }]
                            }
                        }
                    return {"retCode": -1, "retMsg": f"Binance 錯誤: {resp.status}"}
        except Exception as e:
            logger.error(f"Binance 錯誤: {e}")
            return {"retCode": -1, "retMsg": str(e)}
    
    async def get_funding_rate(self, category: str = "linear", symbol: str = "BTCUSDT") -> dict:
        """用 Binance 獲取資金費率"""
        url = f"{BINANCE_FAPI_URL}/fapi/v1/fundingRate?symbol={symbol}&limit=1"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data:
                            return {
                                "retCode": 0,
                                "result": {
                                    "list": [{
                                        "fundingRate": data[0].get("fundingRate", "0")
                                    }]
                                }
                            }
                    return {"retCode": 0, "result": {"list": []}}
        except Exception as e:
            logger.error(f"Binance Funding 錯誤: {e}")
            return {"retCode": 0, "result": {"list": []}}
    
    # ═══════════════════════════════════════════════════════════════════
    # Bybit 帳戶操作（需要簽名）
    # ═══════════════════════════════════════════════════════════════════
    
    async def get_wallet_balance(self, account_type: str = "UNIFIED") -> dict:
        """獲取錢包餘額"""
        return await self._bybit_request("GET", "/v5/account/wallet-balance", {"accountType": account_type})
    
    async def get_positions(self, category: str = "linear", symbol: str = None) -> dict:
        """獲取持倉"""
        params = {"category": category}
        if symbol:
            params["symbol"] = symbol
        return await self._bybit_request("GET", "/v5/position/list", params)
    
    async def place_order(self, symbol: str, side: str, qty: str, order_type: str = "Market", category: str = "linear") -> dict:
        """下單"""
        params = {
            "category": category, 
            "symbol": symbol, 
            "side": side, 
            "orderType": order_type, 
            "qty": qty
        }
        return await self._bybit_request("POST", "/v5/order/create", params)
    
    async def cancel_order(self, symbol: str, order_id: str, category: str = "linear") -> dict:
        """取消訂單"""
        params = {"category": category, "symbol": symbol, "orderId": order_id}
        return await self._bybit_request("POST", "/v5/order/cancel", params)
    
    async def get_open_orders(self, category: str = "linear") -> dict:
        """獲取未成交訂單"""
        return await self._bybit_request("GET", "/v5/order/realtime", {"category": category})
    
    async def set_leverage(self, symbol: str, leverage: str, category: str = "linear") -> dict:
        """設置槓桿"""
        params = {
            "category": category, 
            "symbol": symbol, 
            "buyLeverage": leverage, 
            "sellLeverage": leverage
        }
        return await self._bybit_request("POST", "/v5/position/set-leverage", params)
    
    async def close_position(self, symbol: str, side: str, qty: str, category: str = "linear") -> dict:
        """平倉"""
        close_side = "Sell" if side == "Buy" else "Buy"
        return await self.place_order(symbol, close_side, qty, "Market", category)
