
# ======== CHAINS / EXPLORERS / LZ IDs ========
CHAINS_DATA = {
    'ethereum': {'explorer': 'https://etherscan.io/tx/',  'lz_chain_id': 101},
    'base'    : {'explorer': 'https://basescan.org/tx/',   'lz_chain_id': 184},
    'arbitrum': {'explorer': 'https://arbiscan.io/tx/',    'lz_chain_id': 110},
    'nova'    : {'lz_chain_id': 175},
    'zora'    : {'lz_chain_id': 195},
}

# ======== TOKENS (Base mainnet) ========
# Примітка: на Base “ETH” у транзах — це WETH за адресою системного контракту 0x4200...,
# тому додаємо і alias 'WETH', і 'ETH' для зручності.
TOKEN_ADDRESSES = {
    'ETH'      : '0x4200000000000000000000000000000000000006',  # canonical WETH on Base
    'WETH'     : '0x4200000000000000000000000000000000000006',  # alias

    "USDC"     : "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "DAI"      : "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
    "USDBC"    : '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA',
    "MAV"      : '0x64b88c73A5DfA78D1713fE1b4c69a22d7E0faAa7',
    "aBasWETH" : '0xd4a0e0b9149bcee3c920d2e00b5de09138fd8bb7',
    "sWETH"    : '0x48bf8fcd44e2977c8a9a744658431a8e6c0d866c',

    "BSWAP"    : "0x78a087d713Be963Bf307b18F2Ff8122EF9A63ae9",
    "BSX"      : "0xd5046B976188EB40f6DE40fB527F89c05b323385",
    "GMD"      : "0xCd239E01C36d3079c0dAeF355C61cFF591C40DB1",
    "UNIDX"    : "0x6B4712AE9797C199edd44F897cA09BC57628a1CF",
    "EDE"      : "0x0A074378461FB7ed3300eA638c6Cc38246db4434",
    "BASED"    : "0xBa5E6fa2f33f3955f0cef50c63dCC84861eAb663",
    "AERO"     : "0x940181a94A35A4569E4529A3CDfB74e38FD98631",
    "YFX"      : "0x8901cB2e82CC95c01e42206F8d1F417FE53e7Af0",
    "TAROT"    : "0xF544251D25f3d243A36B07e7E7962a678f952691",
    "BALD"     : "0x27D2DECb4bFC9C76F0309b8E88dec3a601Fe25a8",
    "HZN"      : "0x081AD949deFe648774C3B8deBe0E4F28a80716dc",
    "AXL"      : "0x23ee2343B892b1BB63503a4FAbc840E0e2C6810f",
    "SEAM"     : "0x1C7a460413dD4e964f96D8dFC56E7223cE88CD85",
    "DEGEN"    : "0x4ed4E862860beD51a9570b96d89aF5E1B0Efefed",
    "BMX"      : "0x548f93779fbc992010c07467cbaf329dd5f059b7",
}

# ======== DEX ROUTERS / CONTRACTS (Base) ========
# ⚠️ Підстав свіжі адреси з офіційних джерел перед запуском!
# Aerodrome (Solidly v2) Router:
AERODROME_ROUTER = '<PUT_ROUTER_ADDRESS_HERE>'   # напр., 0x... (Base mainnet)

# KyberSwap Classic/Elastic Router (якщо твій модуль ходить саме в router, а не в API)
KYBER_ROUTER     = '<OPTIONAL_KYBER_ROUTER>'     # якщо не потрібно — залиш порожнім рядком ''

# Інші DEX, якщо потрібні router-адреси (за бажанням):
# BASESWAP_ROUTER   = '<router>'
# ALIENSWAP_ROUTER  = '<router>'
# WOOFI_ROUTER      = '<router>'
# OPENOCEAN_AGG     = '<api_or_router>'  # зазвичай через API

# ======== Maverick (пули) ========
MAVERICK_POOLS = {
    'USDBC': '0x06e6736ca9e922766279a22b75a600fe8b8473b6',
    'DAI'  : '0x5bdb08ae195c8f085704582a27d566028a719265',
    'USDC' : '0x3d70b2f31f75dc84acdd5e1588695221959b2d37',
    'MAV'  : '0xe6917fbf0f44053fd42b55657555afa89806cc24',
}

# ======== DEPLOY CONFIG (для modules/deploy.py) ========
# Які шаблони контрактів деплоїти (імена мають збігатись із ключами нижче
# або з класами/функціями, що ти викликаєш у deploy-модулі)
DEPLOY_CONTRACTS = [
    # 'Counter',
    # 'SimpleStorage',
    # 'Ping',
]

# За замовчуванням газ/велью для всіх деплоїв (можеш перевизначати в модулі)
DEPLOY_DEFAULT_GAS_LIMIT = 1_200_000     # під Solidty 0.8.x прості контракти зазвичай < 300k
DEPLOY_DEFAULT_VALUE_WEI = 0             # без ETH при деплої

# Якщо використовуєш py-solc-x для компіляції — версія компілятора за замовчуванням
SOLC_VERSION = "0.8.20"

# (опційно) Якщо триматимеш заготовки байткодів (без компіляції на льоту):
# DEPLOY_BYTECODES = {
#     'Counter': '0x6080...00',  # приклад
# }

