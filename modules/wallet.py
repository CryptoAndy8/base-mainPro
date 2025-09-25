from web3.middleware import geth_poa_middleware
from random import uniform, randint, shuffle
import datetime, hmac, base64, requests
from typing import Union
from time import sleep
from web3 import Web3

from modules.utils import logger, sleeping
from modules.database import DataBase
from modules import config
import settings

# --- NEW: проксі/RPC хелпери з utils ---
from modules.utils import get_proxy_for_address, get_rpc_for_chain
# ---------------------------------------


class Wallet:
    def __init__(self, privatekey: str, recipient: Union[str, bool], db: DataBase, browser):
        self.privatekey = privatekey
        self.account = Web3().eth.account.from_key(privatekey)
        self.address = self.account.address
        if recipient:
            self.recipient = Web3().to_checksum_address(recipient)
        else:
            self.recipient = recipient

        self.db = db
        self.browser = browser

        self.max_retries = 5
        self.error = None

    # --- UPDATED: web3 з урахуванням проксі та “per-wallet RPC” ---
    def get_web3(self, chain_name: str):
        """
        Створює Web3 для потрібного чейну з урахуванням:
          - персистентного вибору RPC per-wallet (utils.get_rpc_for_chain)
          - проксі per-wallet / global / off (utils.get_proxy_for_address)
        """
        rpc_url = get_rpc_for_chain(self.address, chain_name)
        proxy = get_proxy_for_address(self.address)

        request_kwargs = {'timeout': 60}
        if proxy:
            request_kwargs['proxies'] = {'http': proxy, 'https': proxy}

        web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs=request_kwargs))
        # Base — це L2 з PoA-подібним ланцюгом → geth_poa_middleware доречний
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3
    # ----------------------------------------------------------------

    def make_modules_path(self, modules: list):
        modules_path = []

        for module in modules:
            try:
                counts = settings.TXS_COUNT[module.__name__]
            except:
                counts = [1, 1]
            for _ in range(randint(counts[0], counts[1])):
                modules_path.append(module)
        shuffle(modules_path)
        return modules_path

    def wait_for_gwei(self):
        for chain_data in [
            {'chain_name': 'ethereum', 'max_gwei': settings.MAX_GWEI},
            {'chain_name': 'base', 'max_gwei': settings.BASE_MAX_GWEI},
        ]:
            first_check = True
            while True:
                try:
                    new_gwei = round(self.get_web3(chain_name=chain_data['chain_name']).eth.gas_price / 10 ** 9, 2)
                    if new_gwei < chain_data["max_gwei"]:
                        if not first_check:
                            logger.debug(f'[•] Web3 | New {chain_data["chain_name"].title()} GWEI is {new_gwei}')
                        break
                    sleep(5)
                    if first_check:
                        first_check = False
                        logger.debug(
                            f'[•] Web3 | Waiting for GWEI in {chain_data["chain_name"].title()} at least {chain_data["max_gwei"]}. Now it is {new_gwei}'
                        )
                except Exception as err:
                    logger.warning(f'[•] Web3 | {chain_data["chain_name"].title()} gwei waiting error: {err}')
                    sleeping(10)

    def get_gas(self, chain_name, increasing_gwei=0):
        web3 = self.get_web3(chain_name=chain_name)
        # іноді .max_priority_fee може падати — якщо так, беремо 1 gwei як запасний варіант
        try:
            max_priority_raw = web3.eth.max_priority_fee
        except Exception:
            max_priority_raw = int(1e9)
        max_priority = int(max_priority_raw * (settings.GWEI_MULTIPLIER + increasing_gwei))

        last_block = web3.eth.get_block('latest')
        base_fee = last_block.get('baseFeePerGas', web3.eth.gas_price)
        block_filled = last_block['gasUsed'] / last_block['gasLimit'] * 100 if last_block['gasLimit'] else 0
        if block_filled > 50:
            base_fee = int(base_fee * 1.127)

        max_fee = int(base_fee + max_priority)
        return {'maxPriorityFeePerGas': max_priority, 'maxFeePerGas': max_fee}

    def approve(self, chain_name: str, token_name: str, spender: str, amount=None, value=None, retry=0):
        try:
            token_address = token_name if token_name.startswith('0x') else config.TOKEN_ADDRESSES[token_name]
            web3 = self.get_web3(chain_name=chain_name)
            spender = web3.to_checksum_address(spender)
            token_contract = web3.eth.contract(
                address=web3.to_checksum_address(token_address),
                abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]'
            )

            decimals = token_contract.functions.decimals().call()
            if amount:
                new_amount = round(amount * randint(10, 40), 5)
                new_value = int(new_amount * 10 ** decimals)
            else:
                new_value = int(value * randint(10, 40))
                new_amount = round(new_value / 10 ** decimals, 5)
            module_str = f'approve {new_amount} {token_name} to {spender}'

            allowance = token_contract.functions.allowance(self.address, spender).call()
            if allowance < new_value:
                tx = token_contract.functions.approve(spender, new_value)
                tx_hash = self.sent_tx(chain_name=chain_name, tx=tx, tx_label=module_str)
                sleeping(settings.SLEEP_AFTER_TX)
                return tx_hash

        except Exception as error:
            logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
            if retry + 1 < settings.RETRY:
                sleeping(10)
                return self.approve(
                    chain_name=chain_name, token_name=token_name, spender=spender, amount=amount, value=value, retry=retry + 1
                )
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')

    def sent_tx(self, chain_name: str, tx, tx_label, tx_raw=False, value=0, increasing_gwei=0):
        try:
            web3 = self.get_web3(chain_name=chain_name)
            if not tx_raw:
                tx_completed = tx.build_transaction({
                    'from': self.address,
                    'chainId': web3.eth.chain_id,
                    'nonce': web3.eth.get_transaction_count(self.address),
                    'value': value,
                    **self.get_gas(chain_name=chain_name, increasing_gwei=increasing_gwei),
                })
                # --- NEW: якщо gas не заповнився провайдером — порахуємо
                if 'gas' not in tx_completed or not tx_completed['gas']:
                    try:
                        tx_completed['gas'] = web3.eth.estimate_gas({**tx_completed, 'to': tx_completed.get('to')})
                    except Exception:
                        # запасний дефолт
                        tx_completed['gas'] = 21000
                # невеликий запас по ліміту
                tx_completed['gas'] = int(int(tx_completed['gas']) * 1.25)
            else:
                tx_completed = tx

            signed_tx = web3.eth.account.sign_transaction(tx_completed, self.privatekey)
            raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash = web3.to_hex(raw_tx_hash)
            tx_link = f'{config.CHAINS_DATA[chain_name]["explorer"]}{tx_hash}'
            logger.debug(f'[•] Web3 | {tx_label} tx sent: {tx_link}')

            status = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=int(settings.TO_WAIT_TX * 60)).status

            if status == 1:
                logger.info(f'[+] Web3 | {tx_label} tx confirmed')
                self.db.append_report(privatekey=self.privatekey, text=tx_label, success=True)
                return tx_hash
            else:
                self.db.append_report(
                    privatekey=self.privatekey,
                    text=f'{tx_label} | tx is failed | <a href="{tx_link}">link 👈</a>',
                    success=False
                )
                raise ValueError(f'{tx_label} tx failed: {tx_link}')

        except Exception as err:
            if "replacement transaction underpriced" in str(err) or "not in the chain after" in str(err):
                logger.warning(f'[-] Web3 | {tx_label} | couldnt send tx, increasing gwei')
                return self.sent_tx(
                    chain_name=chain_name, tx=tx, tx_label=tx_label, tx_raw=tx_raw, value=value, increasing_gwei=increasing_gwei + 0.05
                )

            try:
                encoded_tx = f'\n{tx_completed._encode_transaction_data()}'
            except Exception:
                encoded_tx = ''

            raise ValueError(f'tx failed: {err}{encoded_tx}')

    def get_balance(self, chain_name: str, token_name=False, human=False):
        web3 = self.get_web3(chain_name=chain_name)
        if token_name:
            contract = web3.eth.contract(
                address=web3.to_checksum_address(config.TOKEN_ADDRESSES[token_name]),
                abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]'
            )
        while True:
            try:
                if token_name:
                    balance = contract.functions.balanceOf(self.address).call()
                else:
                    balance = web3.eth.get_balance(self.address)

                decimals = contract.functions.decimals().call() if token_name else 18
                if not human:
                    return balance
                return balance / 10 ** decimals
            except Exception as err:
                logger.warning(f'[•] Web3 | Get balance error: {err}')
                sleep(10)

    def wait_balance(self, chain_name: str, needed_balance: Union[int, float], only_more: bool = False):
        " needed_balance: human digit "
        if only_more:
            logger.debug(f'[•] Web3 | Waiting for balance more than {round(needed_balance, 6)} ETH in {chain_name.upper()}')
        else:
            logger.debug(f'[•] Web3 | Waiting for {round(needed_balance, 6)} ETH balance in {chain_name.upper()}')
        while True:
            try:
                new_balance = self.get_balance(chain_name=chain_name, human=True)
                if only_more:
                    status = new_balance > needed_balance
                else:
                    status = new_balance >= needed_balance
                if status:
                    logger.debug(f'[•] Web3 | New balance: {round(new_balance, 6)} ETH')
                    break
                sleep(5)
            except Exception as err:
                logger.warning(f'[•] Web3 | Wait balance error: {err}')
                sleep(10)

    def okx_withdraw(self, chain: str, retry=0):
        def okx_data(api_key, secret_key, passphras, request_path="/api/v5/account/balance?ccy=USDT", body='', meth="GET"):
            try:
                def signature(timestamp: str, method: str, request_path: str, secret_key: str, body: str = "") -> str:
                    if not body:
                        body = ""
                    message = timestamp + method.upper() + request_path + body
                    mac = hmac.new(bytes(secret_key, encoding="utf-8"), bytes(message, encoding="utf-8"), digestmod="sha256")
                    d = mac.digest()
                    return base64.b64encode(d).decode("utf-8")

                dt_now = datetime.datetime.utcnow()
                ms = str(dt_now.microsecond).zfill(6)[:3]
                timestamp = f"{dt_now:%Y-%m-%dT%H:%M:%S}.{ms}Z"

                base_url = "https://www.okex.com"
                headers = {
                    "Content-Type": "application/json",
                    "OK-ACCESS-KEY": api_key,
                    "OK-ACCESS-SIGN": signature(timestamp, meth, request_path, secret_key, body),
                    "OK-ACCESS-TIMESTAMP": timestamp,
                    "OK-ACCESS-PASSPHRASE": passphras,
                    'x-simulated-trading': '0'
                }
            except Exception as ex:
                logger.error(ex)
            return base_url, request_path, headers

        match chain:
            case 'ethereum':
                CHAIN = 'ERC20'
            case 'base':
                CHAIN = 'Base'

        SYMBOL = 'ETH'

        old_balance = self.get_balance(chain_name=chain, human=True)

        api_key = settings.OKX_API_KEY
        secret_key = settings.OKX_API_SECRET
        passphras = settings.OKX_API_PASSWORD

        wallet = self.address
        amount_from = settings.OKX_WITHDRAW_FROM
        amount_to = settings.OKX_WITHDRAW_TO

        # take FEE for withdraw
        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/currencies?ccy={SYMBOL}", meth="GET")
        response = requests.get(f"https://www.okx.cab/api/v5/asset/currencies?ccy={SYMBOL}", timeout=10, headers=headers)

        try:
            if not response.json().get("data"):
                raise Exception(f"couldnt access Api: {response.text}")
            for lst in response.json()['data']:
                if lst['chain'] == f'{SYMBOL}-{CHAIN}':
                    FEE = lst['minFee']

            while True:
                _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/users/subaccount/list", meth="GET")
                list_sub = requests.get("https://www.okx.cab/api/v5/users/subaccount/list", timeout=10, headers=headers)
                list_sub = list_sub.json()

                for sub_data in list_sub['data']:
                    while True:
                        name_sub = sub_data['subAcct']

                        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}", meth="GET")
                        sub_balance = requests.get(
                            f"https://www.okx.cab/api/v5/asset/subaccount/balances?subAcct={name_sub}&ccy={SYMBOL}",
                            timeout=10, headers=headers
                        )
                        sub_balance = sub_balance.json()
                        if sub_balance.get('msg') == f'Sub-account {name_sub} doesn\'t exist':
                            logger.warning(f'ERROR | {sub_balance["msg"]}')
                            continue
                        sub_balance = sub_balance['data'][0]['bal']

                        logger.info(f'{name_sub} | {sub_balance} {SYMBOL}')

                        if float(sub_balance) > 0:
                            body = {"ccy": f"{SYMBOL}", "amt": str(sub_balance), "from": 6, "to": 6, "type": "2", "subAcct": name_sub}
                            _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer", body=str(body), meth="POST")
                            _ = requests.post("https://www.okx.cab/api/v5/asset/transfer", data=str(body), timeout=10, headers=headers)
                        break

                try:
                    _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/account/balance?ccy={SYMBOL}")
                    balance = requests.get(f'https://www.okx.cab/api/v5/account/balance?ccy={SYMBOL}', timeout=10, headers=headers)
                    balance = balance.json()
                    balance = balance["data"][0]["details"][0]["cashBal"]

                    if balance != 0:
                        body = {"ccy": f"{SYMBOL}", "amt": float(balance), "from": 18, "to": 6, "type": "0", "subAcct": "", "clientId": "", "loanTrans": "", "omitPosRisk": ""}
                        _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/transfer", body=str(body), meth="POST")
                        _ = requests.post("https://www.okx.cab/api/v5/asset/transfer", data=str(body), timeout=10, headers=headers)
                except Exception:
                    pass

                # CHECK MAIN BALANCE
                _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/balances?ccy={SYMBOL}", meth="GET")
                main_balance = requests.get(f'https://www.okx.cab/api/v5/asset/balances?ccy={SYMBOL}', timeout=10, headers=headers)
                main_balance = main_balance.json()
                main_balance = float(main_balance["data"][0]['availBal'])
                logger.info(f'total balance | {main_balance} {SYMBOL}')

                if amount_from > main_balance:
                    logger.warning(f'not enough balance ({main_balance} < {amount_from}), waiting 10 secs...')
                    sleep(10)
                    continue

                if amount_to > main_balance:
                    logger.warning(f'you want to withdraw MAX {amount_to} but have only {round(main_balance, 7)}')
                    amount_to = round(main_balance, 7)

                AMOUNT = round(uniform(amount_from, amount_to), 7)
                break

            body = {"ccy": SYMBOL, "amt": AMOUNT, "fee": FEE, "dest": "4", "chain": f"{SYMBOL}-{CHAIN}", "toAddr": wallet}
            _, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/withdrawal", meth="POST", body=str(body))
            a = requests.post("https://www.okx.cab/api/v5/asset/withdrawal", data=str(body), timeout=10, headers=headers)
            result = a.json()

            if result['code'] == '0':
                logger.info(f'[+] OKX | Withdraw success {AMOUNT} {SYMBOL} to {wallet}')
                self.db.append_report(privatekey=self.privatekey, text=f"OKX withdraw {AMOUNT} {SYMBOL} to {wallet}")
                self.wait_balance(chain_name=chain, needed_balance=old_balance, only_more=True)
                return True
            else:
                error = result['msg']
                if retry < settings.RETRY:
                    logger.error(f"OKX withdraw error: {error}")
                    sleep(10)
                    return self.okx_withdraw(chain=chain, retry=retry + 1)
                else:
                    raise ValueError(f'OKX withdraw error: {error}')

        except Exception as error:
            if retry < settings.RETRY:
                logger.error(f"OKX withdraw error: {error}")
                sleep(10)
                if 'Insufficient balance' in str(error):
                    return self.okx_withdraw(chain=chain, retry=retry)
                return self.okx_withdraw(chain=chain, retry=retry + 1)
            else:
                raise ValueError(f'OKX withdraw error : {error}')

    def send_all_native_balance(self, retry=0):
        "sending all native balance excluding `keep` var"

        if not self.recipient:
            return False

        token_name = 'ETH'
        chain_name = 'base'
        module_str = f'send ETH to {self.recipient}'

        try:
            web3 = self.get_web3(chain_name=chain_name)
            all_balance = self.get_balance(chain_name=chain_name)
            keep = round(uniform(settings.BASE_MIN_KEEP, settings.BASE_MAX_KEEP), 5)
            balance_to_send = int(
                (all_balance - web3.eth.gas_price * 21000 * 1.02 - keep * 10 ** 18)
                // 10 ** 10 * 10 ** 10
            )  # round number
            if balance_to_send <= 0:
                logger.error(
                    f'[-] Web3 | {self.address} have {round(all_balance / 10 ** 18, 5)} '
                    f'{token_name} which less then `keep`: {keep} {token_name}'
                )
                return False

            tx = {
                'from': self.address,
                'chainId': web3.eth.chain_id,
                'nonce': web3.eth.get_transaction_count(self.address),
                'value': balance_to_send,
                'to': self.recipient,
                **self.get_gas(chain_name=chain_name),
            }
            try:
                tx['gas'] = web3.eth.estimate_gas(tx)
            except Exception:
                tx['gas'] = 21000

            tx_hash = self.sent_tx(
                chain_name, tx, f'Sent {round(balance_to_send / 10 ** 18, 4)} {token_name} to {self.recipient}', tx_raw=True
            )
            return tx_hash

        except Exception as error:
            logger.error(f'[-] Web3 | {module_str} | {error} [{retry + 1}/{settings.RETRY}]')
            if retry + 1 < settings.RETRY:
                sleeping(10)
                return self.send_all_native_balance(retry=retry + 1)
            else:
                if 'tx failed' not in str(error):
                    self.db.append_report(privatekey=self.privatekey, text=f'{module_str}: {error}', success=False)
                raise ValueError(f'{module_str}: {error}')

    def get_human_token_amount(self, chain_name: str, token_name: str, value: Union[int, float], human=True):
        if token_name != 'ETH':
            web3 = self.get_web3(chain_name=chain_name)
            token_contract = web3.eth.contract(
                address=web3.to_checksum_address(config.TOKEN_ADDRESSES[token_name]),
                abi='[{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]'
            )

            decimals = token_contract.functions.decimals().call()
        else:
            decimals = 18

        if human:
            return round(value / 10 ** decimals, 7)
        else:
            return int(value * 10 ** decimals)
