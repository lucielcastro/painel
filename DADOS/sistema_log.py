import logging
from datetime import datetime

logging.basicConfig(
    filename='log_pendlist.txt',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    encoding='utf-8'
)

def log_print(msg):
    msg_str = str(msg)  # Garante que qualquer tipo seja convertido para string
    hora = datetime.now().strftime('%H:%M:%S')
    print(f"[{hora}] {msg_str}")
    logging.info(msg_str)