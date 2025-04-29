import subprocess
import requests
from datetime import datetime
import json

# Docker and database details
container_name = 'sql-lndmn'
db_user = 'postgres'
db_name = 'postgres'
telegram_token = 'your-token'
chat_id = 'your-chat-id'
telegram_api_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

status_list = {
    "Sucessful trade": "14",
    "Public": "1",
    "Paused": "2",
    "Sending fiat - In chatroom": "9",
    "Fiat sent - In chatroom": "10",
    "In dispute": "11",
    "Collaboratively cancelled": "12",
    "Sending satoshis to buyer": "13",
    "Waiting for maker bond": "0",
    "Waiting for taker bond": "3",
    "Cancelled": "4",
    "Expired": "5",
    "Waiting for trade collateral and buyer invoice": "6",
    "Waiting only for seller trade collateral": "7",
    "Waiting only for buyer invoice": "8",
    "Failed lightning network routing": "15",
    "Wait for dispute resolution": "16",
    "Maker lost dispute": "17",
    "Taker lost dispute": "18"
}

def status_cmd(status):
    return f"docker exec -t {container_name} psql -U {db_user} -d {db_name} -c \"SELECT COUNT(*) FROM api_order WHERE status = {status} AND created_at > NOW() - INTERVAL '24 hours'\""

def exec_cmd(cmd):
    # Execute the command
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    count = 0
    
    # Check for execution errors
    if result.returncode != 0:
        print("Error executing command.")
        return
    
    # Assuming the output format, extract the number of disputes found
    try:
        count_line = next(line for line in result.stdout.split('\n') if line.strip().isdigit())
        count = int(count_line.strip())
    except StopIteration:
        print("Error parsing command output.")
        return
    
    return count

def get_last_n_orders(n):
    cmd = f"docker exec -t {container_name} psql -U {db_user} -d {db_name} -c \"SELECT created_at,status FROM api_order ORDER BY created_at DESC LIMIT {n}\""

    # Execute the command
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Check for execution errors
    if result.returncode != 0:
        print("Error executing command.")
        return
    
    return result.stdout

def get_ids_status():
    msg = "0 - Waiting for maker bond\n"
    msg += "1 - Public\n"
    msg += "2 - Paused\n"
    msg += "3 - Waiting for taker bond\n"
    msg += "4 - Cancelled\n"
    msg += "5 - Expired\n"
    msg += "6 - Waiting for trade collateral and buyer invoice\n"
    msg += "7 - Waiting only for seller trade collateral\n"
    msg += "8 - Waiting only for buyer invoice\n"
    msg += "9 - Sending fiat - In chatroom\n"
    msg += "10 - Fiat sent - In chatroom\n"
    msg += "11 - In dispute\n"
    msg += "12 - Collaboratively cancelled\n"
    msg += "13 - Sending satoshis to buyer\n"
    msg += "14 - Sucessful trade\n"
    msg += "15 - Failed lightning network routing\n"
    msg += "16 - Wait for dispute resolution\n"
    msg += "17 - Maker lost dispute\n"
    msg += "18 - Taker lost dispute\n"

    return msg

def check_orders_status_and_notify():
    msg = f"🤖 Coordinator information at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 🤖\n\n"

    for status_name, status_value in status_list.items():
        cmd = status_cmd(status_value)
        value = exec_cmd(cmd)
        msg += f"{value} - {status_name}\n"

    last_orders = get_last_n_orders(10)
    msg += "\n"
    msg += last_orders

    msg += "\n"
    msg += get_ids_status()
    
    # Notify orders status
    requests.post(telegram_api_url, data={'chat_id': chat_id, 'text': msg})

check_orders_status_and_notify()
