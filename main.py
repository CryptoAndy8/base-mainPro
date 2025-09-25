from modules.utils import sleeping, logger, sleep, choose_mode, make_modules_list
from modules import *  # Browser, Wallet, DataBase, TgReport, etc.
import settings
import random
import traceback

# --- дрібні утиліти ---

def _safe_get_callable(name: str):
    """Безпечно дістати функцію/клас модуля з globals()."""
    obj = globals().get(name)
    if callable(obj):
        return obj
    raise RuntimeError(f'Module "{name}" is not callable or not found')

def _run_with_retries(func, *, tries: int, on_label: str):
    """Універсальний ретрай-виконавець для модулів."""
    last_err = None
    for attempt in range(1, tries + 1):
        try:
            return func()
        except KeyboardInterrupt:
            raise
        except Exception as err:
            last_err = err
            logger.error(f'[-] Web3 | {on_label} | attempt {attempt}/{tries} failed: {err}')
            # короткий джітер перед повтором
            sleeping([3, 6])
    # якщо всі спроби впали — пробросимо останню
    if last_err:
        raise last_err

def _warn_proxy_once():
    if settings.PROXY in ['http://log:pass@ip:port', '']:
        logger.error('You will not use proxy')

# --- режими ---

def circle_mode(db: "DataBase"):
    """
    Mode 1: по акаунтах, формуємо список модулів на акаунт і виконуємо по черзі.
    """
    while True:
        wallet = None
        browser = None
        module_data = None

        try:
            module_data = db.get_random_account()

            if module_data == 'No more accounts left':
                logger.success('All accounts done.')
                return 'Ended'
            elif module_data == "Wrong mode":
                logger.error('[-] Database | Current database created only for "Warmup" mode')
                return False

            # ініт
            browser = Browser(db=db, privatekey=module_data["privatekey"])
            wallet = Wallet(
                privatekey=module_data["privatekey"],
                recipient=module_data["recipient"],
                db=db,
                browser=browser,
            )

            print('')
            logger.info(f'[•] Web3 | {wallet.address} | Starting')

            # список модулів
            modules_list = make_modules_list(format_list=True)

            # опційно вивід з OKX в Base на старті кола
            try:
                wallet.okx_withdraw(chain='base')
                sleeping(settings.SLEEP_AFTER_TX)
            except Exception as err:
                logger.error(f'[-] Web3 | okx_withdraw error: {err}')

            # виконання модулів
            for module_name in modules_list:
                def _one():
                    mod_callable = _safe_get_callable(module_name)
                    mod_callable(wallet=wallet)  # сумісність із існуючими модулями

                try:
                    _run_with_retries(_one, tries=max(1, int(settings.RETRY)), on_label=module_name)
                except Exception as err:
                    logger.error(f'[-] Web3 | Module {module_name} error: {err}')
                    db.append_report(privatekey=wallet.privatekey, text=f'{module_name}: {err}', success=False)
                finally:
                    sleeping(settings.SLEEP_AFTER_TX)
                    print('')

        except KeyboardInterrupt:
            logger.warning('Interrupted by user (Ctrl+C). Finishing current account gracefully...')
            break
        except Exception as err:
            # wallet може бути None, тому акуратно
            addr = getattr(wallet, 'address', 'unknown')
            logger.error(f'{addr} | Account error: {err}')
            if wallet is not None:
                db.append_report(privatekey=wallet.privatekey, text=str(err), success=False)
            # діагностика у лог
            traceback.print_exc()
        finally:
            # коректний пост-аккаунтний флоу
            if isinstance(module_data, dict) and wallet is not None:
                if module_data.get('last'):
                    # “вичіслюємо” ака, якщо потрібно
                    try:
                        wallet.send_all_native_balance()
                    except Exception as err:
                        logger.error(f'{wallet.address} | Send native error: {err}')
                        db.append_report(privatekey=wallet.privatekey, text=str(err), success=False)

                    # відправити TG-лог
                    try:
                        reports = db.get_account_reports(privatekey=wallet.privatekey)
                        TgReport().send_log(logs=reports)
                    except Exception as err:
                        logger.error(f'{wallet.address} | TG report error: {err}')

                    sleeping(settings.SLEEP_AFTER_ACC)

            # закрити браузер, якщо є метод
            try:
                if browser and hasattr(browser, "close") and callable(browser.close):
                    browser.close()
            except Exception as _:
                pass


def warmup_mode(db: "DataBase"):
    """
    Mode 2: по (гаманець, модуль) парам у базі — для набивки активності.
    """
    while True:
        wallet = None
        browser = None
        module_data = None

        try:
            module_data = db.get_random_module()

            if module_data == 'No more accounts left':
                logger.success('All accounts done.')
                return 'Ended'
            elif module_data == "Wrong mode":
                logger.error('[-] Database | Current database created only for "Circle" mode')
                return False

            # ініт
            browser = Browser(db=db, privatekey=module_data["privatekey"])
            wallet = Wallet(
                privatekey=module_data["privatekey"],
                recipient=module_data["recipient"],
                db=db,
                browser=browser,
            )

            # запуск конкретного модуля
            print('')
            mod_name = module_data["module_name"]
            logger.info(f'[•] Web3 | {wallet.address} | Starting "{mod_name.lower()}"')

            def _one():
                mod_callable = _safe_get_callable(mod_name)
                mod_callable(wallet=wallet)

            _run_with_retries(_one, tries=max(1, int(settings.RETRY)), on_label=mod_name)

        except KeyboardInterrupt:
            logger.warning('Interrupted by user (Ctrl+C). Finishing gracefully...')
            break
        except Exception as err:
            addr = getattr(wallet, 'address', 'unknown')
            logger.error(f'{addr} | Account error: {err}')
            if wallet is not None:
                db.append_report(privatekey=wallet.privatekey, text=str(err), success=False)
            traceback.print_exc()
        finally:
            if isinstance(module_data, dict) and wallet is not None:
                if module_data.get('last'):
                    try:
                        reports = db.get_account_reports(privatekey=wallet.privatekey)
                        TgReport().send_log(logs=reports)
                    except Exception as err:
                        logger.error(f'{wallet.address} | TG report error: {err}')

            sleeping(settings.SLEEP_AFTER_TX)  # затримка між модулями

            try:
                if browser and hasattr(browser, "close") and callable(browser.close):
                    browser.close()
            except Exception as _:
                pass


# --- entrypoint ---

if __name__ == '__main__':
    # стабільніший seed для випадковостей, якщо треба відтворюваність — закинь свій
    random.seed()

    _warn_proxy_once()

    db = DataBase()

    try:
        while True:
            mode = choose_mode()
            match mode:
                case 'Circle database' | 'Warmup database':
                    db.create_modules(mode=mode)

                case 1:
                    if circle_mode(db) == 'Ended':
                        break
                    print('')

                case 2:
                    if warmup_mode(db) == 'Ended':
                        break
                    print('')

                case _:
                    logger.error(f'Unknown mode: {mode}')
                    sleep(0.3)

    except KeyboardInterrupt:
        logger.warning('Stopped by user.')

    # невеличка пауза перед виходом
    sleep(0.1)
    input('\n > Exit')
