"""
This code tries to solve problems with telegram messages caused by Tor network.
Some robots complain that are not receiving TG messages when its orders are taken.
This code search for orders that are taken and the maker is offline for a while.
When a message is sent successfully, the order_id and taker_hash are written in a file
to avoid sent the message every time it runs.

Create a cronjob to execute this code every 10min:
3-57/10 * * * * torsocks python3 /home/user/scripts/telegram_resend.py
Edit the constants in the beginning.
"""

import subprocess
import requests
import re
from datetime import datetime

# Docker and database details
container_name = 'sql-lndmn'
db_user = 'postgres'
db_name = 'postgres'

# Create a telegram bot to send you information when this code send a message to a robot
telegram_token_coordinator = 'coordinator bot'
chat_id_coordinator = 'coordinator chat id'

telegram_token_robosats_env = 'the same token in robosats.env'
my_onion_site = '4t4.....onion'
log_tg_file = '/home/user/scripts/log_tg_coord.txt'

# Run a sql command to search for robots
def exec_cmd(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    lines = result.stdout.split('\n')
    robots = lines[2:-3]
    
    return robots

# Send TG messages. It will try 5 times and return True if it works
def send_telegram_msg(msg, chat_id, bot_token):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            payload = {
                'chat_id': chat_id,
                'text': msg
            }
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return True
            else:
                print('response.status_code = ', response.status_code)
        except Exception:
            print('Error sending Telegram bot message:', attempt)
    return False

# Write a new_line in file_name if a message was sent
def append_2_file(file_name, new_line):
    # Open the file in append mode
    with open(file_name, 'a') as file:
        # Append the new string to the end of the file on a new line
        file.write(f'{new_line}\n')

# Search if it has already sent a message
def find_line_in_file(line, file_name):
    with open(file_name, 'r') as f:
        for file_line in f:
            if line in file_line:
                return True
    return False

"""
Search for orders that:
  - telegram is enabled
  - the status are 'Waiting for trade collateral and buyer invoice (6)',
    'Waiting only for seller trade collateral (7)' or 'Waiting only for buyer invoice (8)'
  - taker bond was created 30min ago or more
  - last login of the maker was 30min ago or more
"""

telegram_enabled = True
time_interval_created = 30
time_interval_login = 30

cmd = f"""
docker exec -t {container_name} psql -U {db_user} -d {db_name} -c \"
SELECT user_m.username, r_m.telegram_chat_id, o.id, user_t.username, o.taker_bond_id
FROM api_order as o
JOIN api_robot as r_m ON o.maker_id = r_m.user_id
JOIN api_lnpayment as ln ON o.taker_bond_id = ln.payment_hash
JOIN auth_user as user_t ON user_t.id = o.taker_id
JOIN auth_user as user_m ON user_m.id = o.maker_id
WHERE r_m.telegram_enabled = {telegram_enabled} AND (o.status = 6 OR o.status = 7 OR o.status = 8)
AND ln.created_at < NOW() - INTERVAL '{time_interval_created} minutes' AND user_m.last_login < NOW() - INTERVAL '{time_interval_login} minutes'\"
"""

output = exec_cmd(cmd)

if len(output) > 0:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    send_coord_alert = False

    # Header of the message to the coordinator
    msg = '⚠️Message resent⚠️\n'
    msg += 'Robot | chat_id | order_id | Taker\n'

    pattern = r'[|]'
    for line in output:
        line_array = re.split(pattern, line.replace(' ',''))
        robot = line_array[0]
        chat_id_robot = line_array[1]
        order_id = line_array[2]
        robot_taker = line_array[3]
        taker_hash = line_array[4]

        # Search if it has already sent a message
        is_msg_sent = find_line_in_file(line=f'*{order_id}_{taker_hash}*', file_name=log_tg_file)

        if not is_msg_sent:
            robot_msg = f'✅ Hey {robot}, your order was taken by {robot_taker}!🥳 Visit http://{my_onion_site}/order/{order_id} to proceed with the trade.'
            print(robot_msg)
            is_msg_sent = send_telegram_msg(msg=robot_msg, chat_id=chat_id_robot, bot_token=telegram_token_robosats_env)
            
            # Organize message to coordinator if one message was sent to a robot
            if is_msg_sent:
                # write in file if a message was sent to a robot
                append_2_file(file_name=log_tg_file, new_line=f'{now} - *{order_id}_{taker_hash}*')
                msg += f'{robot} | {chat_id_robot} | {order_id} | {robot_taker}\n'
                send_coord_alert = True

    # Send the coordinator message
    if send_coord_alert:
        print(msg)
        send_telegram_msg(msg=msg, chat_id=chat_id_coordinator, bot_token=telegram_token_coordinator)
else:
    print('No Robots')
