# ======== RUN / GENERAL ========
SHUFFLE_WALLETS   = False
RETRY             = 3

MAX_GWEI          = 15
BASE_MAX_GWEI     = 1.2
GWEI_MULTIPLIER   = 1.05
TO_WAIT_TX        = 3                      # хвилин чекати підтвердження
SLEEP_AFTER_TX    = [10, 20]
SLEEP_AFTER_ACC   = [40, 60]

# ======== RPC (кілька ендпойнтів; вибір можна робити per-wallet) ========
RPCS = {
    "ethereum": [
        "https://eth.drpc.org",
        "https://rpc.ankr.com/eth",                  # запасний приклад
    ],
    "base": [
        "https://base.llamarpc.com",
        "https://mainnet.base.org",                  # офіційний
        "https://rpc.ankr.com/base",                 # запасний приклад
    ],
}

# ======== COUNT CONFIG ========
TXS_COUNT = {
    'OdosSwap'      : [1, 2],
    'XyFinanceSwap' : [1, 2],
    'OpenOceanSwap' : [0, 1],
    'MaverickSwap'  : [0, 1],
    'KyberSwap'     : [0, 1],
    'Aerodrome'     : [1, 2],   # ← збігається з імпортом вище
    'AlienSwap'     : [0, 0],
    'InfusionSwap'  : [0, 0],

    'Aave'          : [0, 2],
    'Compound'      : [0, 2],

    'Deploy'        : [1, 1],   # автодеплой смарт-контрактів
}
WALLET_TX_COUNT   = [2, 6]

# ======== DEX TOKENS / SLIPPAGE ========
XY_TOKENS = ['USDC', 'WETH']
XY_FROM_SWAP, XY_TO_SWAP  = 0.001, 0.003
XY_FROM_BACK, XY_TO_BACK  = 100, 100
XY_SLIPPAGE               = 1

# AERODROME (Solidly v2) — https://aerodrome.finance/
AD_TOKENS                 = ['USDC', 'USDbC', 'DAI', 'WETH']  # вибери свої
AD_FROM_SWAP, AD_TO_SWAP  = 0.0001, 0.0002
AD_FROM_BACK, AD_TO_BACK  = 95, 100
AD_SLIPPAGE               = 0.5   # % (0.3–0.8 ок)

MV_TOKENS = ['USDC', 'MAV', 'WETH']
MV_FROM_SWAP, MV_TO_SWAP  = 0.001, 0.002
MV_FROM_BACK, MV_TO_BACK  = 95, 100
MV_SLIPPAGE               = 5

OD_TOKENS = ['DAI', 'USDC', 'MAV', 'WETH']
OD_FROM_SWAP, OD_TO_SWAP  = 0.001, 0.002
OD_FROM_BACK, OD_TO_BACK  = 95, 100
OD_SLIPPAGE               = 1

KS_TOKENS = ['DAI', 'USDC']
KS_FROM_SWAP, KS_TO_SWAP  = 0.0001, 0.0002
KS_FROM_BACK, KS_TO_BACK  = 95, 100
KS_SLIPPAGE               = 1

OOS_TOKENS = ['USDC', "DAI"]
OOS_FROM_SWAP, OOS_TO_SWAP = 0.0001, 0.0002
OOS_FROM_BACK, OOS_TO_BACK = 95, 100
OOS_SLIPPAGE                = 1

# ======== LENDING ========
AV_FROM_DEPOSIT, AV_TO_DEPOSIT = 50, 70        # % від балансу, консервативно
AV_FROM_BACK, AV_TO_BACK       = 100, 100

CP_FROM_DEPOSIT, CP_TO_DEPOSIT = 50, 70
CP_FROM_BACK, CP_TO_BACK       = 100, 100

SM_FROM_DEPOSIT, SM_TO_DEPOSIT = 80, 90
SM_FROM_BACK, SM_TO_BACK       = 95, 100

MW_FROM_DEPOSIT, MW_TO_DEPOSIT = 80, 90
MW_FROM_BACK, MW_TO_BACK       = 95, 100

# ======== MODE 1 (OKX) ========
OKX_API_KEY       = ''
OKX_API_SECRET    = ''
OKX_API_PASSWORD  = ''
OKX_WITHDRAW_FROM = 0.002
OKX_WITHDRAW_TO   = 0.01
BASE_MIN_KEEP     = 0.0005
BASE_MAX_KEEP     = 0.001

# ======== PROXY ========
# 'off' — не використовуємо; 'global' — один на всіх; 'per_wallet' — різний для кожного адреса
PROXY_MODE = 'per_wallet'   # 'per_wallet' | 'global' | 'off'

PROXIES = [
    "http://log:pass@IP:port",
    "http://log:pass@IP:port",
]

CHANGE_IP_LINK = "https://changeip.mobileproxy.space/?proxy_key=...&format=json"

# Ротація user-agent'ів (додав кілька популярних десктоп/мобільних)
USER_AGENTS = [
    # Desktop Chrome/Edge/Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/124.0.0.0 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",

    # Mobile Android/iOS
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Mi 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
]
# ======== DEPLOY (Base mainnet) ========
# скільки разів модуль "Deploy" може відпрацювати на одному гаманці
# (як і для інших модулів)
TXS_COUNT.update({
    'Deploy': [0, 2],       # напр., 0–2 деплої на гаманець
})

# які контракти модуль може деплоїти і як часто їх брати
DEPLOY_CONTRACTS_PLAN = {
    # "назва у модулі": [min, max] запусків на гаманець
    'SimpleStorage': [0, 1],
    'Greeter':       [0, 1],
    'MinimalERC20':  [0, 1],   # мінімальний ERC20, усі токени деплояться на адресу деплойера
}

# версія компілятора (ставиться автоматично при першому запуску)
SOLC_VERSION = "0.8.20"

# генерація аргументів конструктора (рандом)
DEPLOY_ARGS = {
    'Greeter': {
        'greetings': ["GM", "Hello Base", "WAGMI", "Stay based", "LFG"]
    },
    'MinimalERC20': {
        'names':   ["Test", "Alpha", "Omega", "Based", "Echo"],
        'symbols': ["TST", "ALP", "OMG", "BASED", "ECHO"],
        'decimals': 18,
        # початковий саплай у «цілих» токенах (мінтиться на адресу деплойера)
        'supply_range': [1_000, 100_000]
    }
}
