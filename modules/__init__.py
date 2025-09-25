from .browser import Browser
from .wallet import Wallet
from .database import DataBase

# Swaps / DEX
from .odos import OdosSwap
from .xy_finance import XyFinanceSwap
from .openocean import OpenOceanSwap
from .maverick import MaverickSwap
from .kyber import KyberSwap
from .aerodrome import Aerodrome      # клас саме так і має називатись
from .baseswap import BaseSwap
from .alienswap import AlienSwap
from .infusionswap import InfusionSwap
from .woofi import WoofiSwap

# Lending
from .aave import Aave
from .compound import Compound
from .seamless import Seamless         # якщо використовуєш
from .moonwell import Moonwell         # якщо використовуєш

# Інше
from .deploy import Deploy
