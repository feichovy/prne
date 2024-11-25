from netmiko import ConnectHandler
import json
def read_config(file_path):
    try:
        # Read the configuration file
        with open(file_path, 'r') as file:
            config = json.load(file)  # 读取 JSON 文件并解析为字典
        return config
    except FileNotFoundError:
        print(f"Error: The configuration file '{file_path}' was not found.")

        # 创建默认的 JSON 配置文件
        default_config = {
            'devices': [
                {
                    'name': 'default_device',
                    'ip': '192.168.56.1',
                    'username': 'admin',
                    'password': 'password',
                    'connection_type': 'ssh',
                    'secret': 'enable_password'
                }
            ]
        }

        # 创建并写入默认配置到 JSON 文件
        with open(file_path, 'w') as file:
            json.dump(default_config, file, indent=4)

        print(f"A default configuration file '{file_path}' has been created. Please update it with the correct device information.")
        return default_config

# Create SSH connection and enter configure terminal
def connect_to_device(username, ip, password, secret):
    try:
        network_device = {
            'username': username,
            'ip': ip,
            'password': password,
            'secret': secret
        }
        connection = ConnectHandler(**network_device)
        connection.enable()
        connection.send_command("terminal length 0")
        return connection
    except Exception as e:
        print(f"Fail to connect via SSH: {e}")
        return None

# Configure Loopback0 & GigabitEthernet1
def config_interface(connection, interface, ip, mask):
    pass

if __name__ == "__main__":
    config = read_config('config.json')

    for device in config['devices']:
        ip = device['ip']
        username = device['username']
        password = device['password']
        secret = device['secret']
    connection = connect_to_device(ip, username, password, secret)
    if connection:
        print("[SUCCESS] Device is reachable!")
        connection.disconnect()


