import subprocess
import sys
import os
import platform
import logging
from dotenv import load_dotenv
from bip_utils import (
    Bip39MnemonicGenerator,
    Bip39SeedGenerator,
    Bip44,
    Bip44Coins,
    Bip44Changes,
    Bip39WordsNum,
)

# Các hằng số
LOG_FILE_NAME = "enigmacracker.log"
ENV_FILE_NAME = "EnigmaCracker.env"
MATCHED_WALLETS_FILE = "wallet.txt"    # File để ghi địa chỉ ví khớp
KNOWN_WALLETS_FILE = "walletgoc.txt"    # File chứa địa chỉ ví đã biết

# Biến toàn cục cho số lượng ví đã quét
wallets_scanned = 0

# Lấy đường dẫn tuyệt đối của thư mục chứa script
directory = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(directory, LOG_FILE_NAME)
env_file_path = os.path.join(directory, ENV_FILE_NAME)

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),  # Ghi log vào file
        logging.StreamHandler(sys.stdout),     # Ghi log ra stdout
    ],
)

# Tải biến môi trường từ file .env
load_dotenv(env_file_path)

# Kiểm tra xem các biến môi trường có bị thiếu không
required_env_vars = ["ETHERSCAN_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

# Hàm để load các ví đã biết từ file
def load_known_wallets(filename):
    """Đọc các địa chỉ ví từ file đã cho và trả về một tập hợp các địa chỉ."""
    known_wallets = set()
    try:
        with open(filename, "r") as f:
            for line in f:
                known_wallets.add(line.strip())
    except FileNotFoundError:
        logging.error(f"Không tìm thấy file: {filename}")
    return known_wallets

# Load các ví đã biết
known_wallets = load_known_wallets(KNOWN_WALLETS_FILE)

def update_cmd_title():
    """Cập nhật tiêu đề CMD với số lượng ví đã quét."""
    if platform.system() == "Windows":
        os.system(f"title EnigmaCracker.py - Wallets Scanned: {wallets_scanned}")

def bip():
    """Sinh 12 từ khóa BIP39 mnemonics."""
    return Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)

def bip44_ETH_wallet_from_seed(seed):
    """Tạo ví Ethereum từ hạt giống BIP39."""
    seed_bytes = Bip39SeedGenerator(seed).Generate()
    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    bip44_acc_ctx = (
        bip44_mst_ctx.Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT)
        .AddressIndex(0)
    )
    eth_address = bip44_acc_ctx.PublicKey().ToAddress()
    return eth_address

def write_matched_wallets_to_file(seed, ETH_address):
    """Ghi các ví khớp vào file wallet.txt."""
    with open(MATCHED_WALLETS_FILE, "a") as f:
        log_message = f"Seed: {seed}\nETH Address: {ETH_address}\n\n"
        f.write(log_message)
        logging.info(f"Đã ghi vào file matched wallets: {log_message}")

def main():
    global wallets_scanned
    try:
        while True:
            seed = bip()
            ETH_address = bip44_ETH_wallet_from_seed(seed)

            if ETH_address in known_wallets:
                logging.info(f"Tìm thấy khớp! Seed: {seed}, ETH: {ETH_address}")
                write_matched_wallets_to_file(seed, ETH_address)
            else:
                logging.info(f"Seed: {seed}, ETH: {ETH_address}")

            wallets_scanned += 1
            update_cmd_title()

    except KeyboardInterrupt:
        logging.info("Script stopped by user.")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
