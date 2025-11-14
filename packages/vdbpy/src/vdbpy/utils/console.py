from getpass import getpass

from vdbpy.utils.logger import get_logger

logger = get_logger()

TRUTHY_VALUES = ["true", "1", "t", "y", "yes"]
FALSY_VALUES = ["false", "0", "f", "n", "no"]


def get_credentials_from_console() -> tuple[str, str]:
    """Prompt the user for credentials."""
    logger.info("Please enter your credentials:")
    account_name = input("Account name: ").strip()
    password = getpass("Password: ").strip()

    if not account_name or not password:
        logger.warning("Credentials cannot be empty.")
        return get_credentials_from_console()

    return account_name, password


def prompt_choice(choices: list[str]) -> str:
    while True:
        logger.info("\nAvailable choices:")
        for i, choice in enumerate(choices, 1):
            logger.info(f"{i}. {choice}")

        try:
            choice = int(input("\nSelect a number: "))
            if choice < 1 or choice > len(choices):
                logger.warning("Invalid selection.")
                continue
            return choices[choice - 1]

        except ValueError:
            logger.warning("Invalid input. Please enter a number.")
            continue


def get_boolean(prompt: str) -> bool:
    while True:
        user_input = input(f"{prompt} [y/n]: ").strip().lower()

        if user_input in TRUTHY_VALUES:
            return True
        if user_input in FALSY_VALUES:
            return False

        logger.warning(f"Invalid input '{user_input}'.")
        logger.warning(f"Please enter value from {TRUTHY_VALUES} / {FALSY_VALUES}.")


def get_boolean_or_none(prompt: str) -> bool | None:
    while True:
        user_input = input(f"{prompt} [y/n] (press enter to skip): ").strip().lower()

        if user_input in TRUTHY_VALUES:
            return True
        if user_input in FALSY_VALUES:
            return False
        if user_input == "":
            return None

        logger.warning(f"Invalid input '{user_input}'.")
        logger.warning(f"Please enter value from {TRUTHY_VALUES} / {FALSY_VALUES}.")
