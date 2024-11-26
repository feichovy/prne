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

        # Create default json file
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

        # Write configuration into the json file
        with open(file_path, 'w') as file:
            json.dump(default_config, file, indent=4)

        print(f"A default configuration file '{file_path}' has been created. Please update it with the correct device information.")
        return default_config

# Write updated configuration back to the file
def write_config(file_path, config):
    try:
        with open(file_path, 'w') as file:
            json.dump(config, file, indent=4)
        print(f"[INFO] Configuration file '{file_path}' updated successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to update configuration file '{file_path}': {str(e)}")

# Create SSH connection and enter configure terminal
def connect_to_device(username, ip, password, secret):
    try:
        network_device = {
            'device_type': 'cisco_ios',
            'host': ip,
            'username': username,
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
def config_interface(connection, interface, ip, mask, config, file_path):
    commands =  [
        f"interface {interface}",
        f"ip address {ip} {mask}",
        "no shutdown",
    ]
    try:
        print(f"[INFO]: Configuring IP address for {interface}")
        connection.send_config_set(commands)
        # Update the configuration file with the new IP address
        for device in config['devices']:
            if interface.lower() == 'loopback0':
                device['loopback_ip'] = ip
            elif interface.lower() == 'gigabitethernet1':
                device['g1_ip'] = ip
        write_config(file_path, config)
        return f"[SUCCESS] {interface} configured with {ip}/{mask} successfully"
    except Exception as e:
        return f"[ERROR] Fail to configure {interface}: {str(e)}"

# Enable OSPF
def config_OSPF(connection):
    commands = [
        "router ospf 1", # Start OSPF session
        "network 192.168.56.0 0.0.0.255 area 0", # Set Backbone area, use Wildcard Mask to match the devices
        "network 10.1.1.1 0.0.0.0 area 0" # Advertise Loopback0 interface to OSPF
    ]
    try:
        print("[INFO] Configuring OSPF...")
        connection.send_config_set(commands)
        return "[SUCCESS] OSPF configured successfully"
    except Exception as e:
        return f"[ERROR] Failed to configure OSPF: {str(e)}"

# Create ACL and apply to the interface
def configure_acl(connection, interface):
    acl_commands = []
    print(f"[INFO] Starting ACL configuration on {interface}...")
    print("By default, no access restrictions are in place. You can add rules to allow or deny specific traffic.")
    while True:
        action = input("Enter action (permit/deny) or 'done' to finish ACL configuration: ").strip().lower()
        if action == 'done':
            break
        elif action not in ['permit', 'deny']:
            print("Invalid action. Please enter 'permit', 'deny', or 'done'.")
            continue
        source_ip = input("Enter the source IP address to {}: ".format(action)).strip()
        wildcard_mask = input("Enter the wildcard mask for the source IP (e.g., 0.0.0.0): ").strip()
        acl_commands.append(f"access-list 101 {action} ip {source_ip} {wildcard_mask} any")
    # Notice if there is no ACL rule
    if not acl_commands:
        print("[INFO] No ACL rules configured.")
        return "[INFO] No ACL rules applied."
    # Apply ACL to the specified interface
    acl_commands.extend([
        f"interface {interface}",
        "ip access-group 101 in"
    ])
    try:
        print(f"[INFO] Configuring ACL on {interface}...")
        connection.send_config_set(acl_commands)
        return f"[SUCCESS] ACL configured and applied to {interface} successfully"
    except Exception as e:
        return f"[ERROR] Failed to configure ACL: {str(e)}"

# Configure IPSec
def configure_ipsec(connection):
    ipsec_commands = [
        "crypto isakmp policy 10",
        "encr aes",
        "hash sha",
        "authentication pre-share",
        "group 2",
        "crypto isakmp key MY_KEY address 0.0.0.0",
        "crypto ipsec transform-set MY_TRANSFORM_SET esp-aes esp-sha-hmac",
        "crypto map MY_CRYPTO_MAP 10 ipsec-isakmp",
        "set peer 192.168.56.2",
        "set transform-set MY_TRANSFORM_SET",
        "match address 101",
        "interface GigabitEthernet1",
        "crypto map MY_CRYPTO_MAP"
    ]
    try:
        print("[INFO] Configuring IPSec...")
        connection.send_config_set(ipsec_commands)
        return "[SUCCESS] IPSec configured successfully"
    except Exception as e:
        return f"[ERROR] Failed to configure IPSec: {str(e)}"

if __name__ == "__main__":
    config_file_path = 'config.json'
    config = read_config(config_file_path)

    for device in config['devices']:
        ip = device['ip']
        username = device['username']
        password = device['password']
        secret = device['secret']

    connection = connect_to_device(ip, username, password, secret)
    if connection:
        print("[SUCCESS] Device is reachable!")

        # Example usage: Configuring an interface
        interface_result = config_interface(connection, "Loopback0", "10.1.1.1", "255.255.255.255", config, config_file_path)
        print(interface_result)

        # Example usage: Configuring OSPF
        ospf_result = config_OSPF(connection)
        print(ospf_result)

        # Example usage: Configuring ACL for GigabitEthernet1
        acl_result_g1 = configure_acl(connection, "GigabitEthernet1")
        print(acl_result_g1)

        # Example usage: Configuring ACL for Loopback0
        acl_result_lb0 = configure_acl(connection, "Loopback0")
        print(acl_result_lb0)

        # Example usage: Configuring IPSec
        ipsec_result = configure_ipsec(connection)
        print(ipsec_result)

        connection.disconnect()
        print("[INFO] Disconnected from the device.")
# from netmiko import ConnectHandler
# import json
# import concurrent.futures
#
# def read_config(file_path):
#     try:
#         # Read the configuration file
#         with open(file_path, 'r') as file:
#             config = json.load(file)  # 读取 JSON 文件并解析为字典
#         return config
#     except FileNotFoundError:
#         print(f"Error: The configuration file '{file_path}' was not found.")
#
#         # Create default json file
#         default_config = {
#             'devices': [
#                 {
#                     'name': 'default_device',
#                     'ip': '192.168.56.1',
#                     'username': 'admin',
#                     'password': 'password',
#                     'connection_type': 'ssh',
#                     'secret': 'enable_password'
#                 }
#             ]
#         }
#
#         # Write configuration into the json file
#         with open(file_path, 'w') as file:
#             json.dump(default_config, file, indent=4)
#
#         print(f"A default configuration file '{file_path}' has been created. Please update it with the correct device information.")
#         return default_config
#
# # Write updated configuration back to the file
# def write_config(file_path, config):
#     try:
#         with open(file_path, 'w') as file:
#             json.dump(config, file, indent=4)
#         print(f"[INFO] Configuration file '{file_path}' updated successfully.")
#     except Exception as e:
#         print(f"[ERROR] Failed to update configuration file '{file_path}': {str(e)}")
#
# # Create SSH connection and enter configure terminal
# def connect_to_device(username, ip, password, secret):
#     try:
#         network_device = {
#             'device_type': 'cisco_ios',
#             'host': ip,
#             'username': username,
#             'password': password,
#             'secret': secret
#         }
#         connection = ConnectHandler(**network_device)
#         connection.enable()
#         connection.send_command("terminal length 0")
#         return connection
#     except Exception as e:
#         print(f"Fail to connect via SSH: {e}")
#         return None
#
# # Configure Loopback0 & GigabitEthernet1
# def config_interface(connection, interface, ip, mask, config, file_path):
#     commands =  [
#         f"interface {interface}",
#         f"ip address {ip} {mask}",
#         "no shutdown",
#     ]
#     try:
#         print(f"[INFO]: Configuring IP address for {interface}")
#         connection.send_config_set(commands)
#         # Update the configuration file with the new IP address
#         for device in config['devices']:
#             if interface.lower() == 'loopback0':
#                 device['loopback_ip'] = ip
#             elif interface.lower() == 'gigabitethernet1':
#                 device['g1_ip'] = ip
#         write_config(file_path, config)
#         return f"[SUCCESS] {interface} configured with {ip}/{mask} successfully"
#     except Exception as e:
#         return f"[ERROR] Fail to configure {interface}: {str(e)}"
#
# # Enable OSPF
# def config_OSPF(connection):
#     commands = [
#         "router ospf 1", # Start OSPF session
#         "network 192.168.56.0 0.0.0.255 area 0", # Set Backbone area, use Wildcard Mask to match the devices
#         "network 10.1.1.1 0.0.0.0 area 0" # Advertise Loopback0 interface to OSPF
#     ]
#     try:
#         print("[INFO] Configuring OSPF...")
#         connection.send_config_set(commands)
#         # Verify OSPF status
#         ospf_status = connection.send_command("show ip ospf neighbor")
#         print(f"[INFO] OSPF Neighbor Status:\n{ospf_status}")
#         return "[SUCCESS] OSPF configured successfully"
#     except Exception as e:
#         return f"[ERROR] Failed to configure OSPF: {str(e)}"
#
# # Create ACL and apply to the interface
# def configure_acl(connection, interface):
#     acl_commands = []
#     print(f"[INFO] Starting ACL configuration on {interface}...")
#     print("By default, no access restrictions are in place. You can add rules to allow or deny specific traffic.")
#     while True:
#         action = input("Enter action (permit/deny) or 'done' to finish ACL configuration: ").strip().lower()
#         if action == 'done':
#             break
#         elif action not in ['permit', 'deny']:
#             print("Invalid action. Please enter 'permit', 'deny', or 'done'.")
#             continue
#         source_ip = input("Enter the source IP address to {}: ".format(action)).strip()
#         wildcard_mask = input("Enter the wildcard mask for the source IP (e.g., 0.0.0.0): ").strip()
#         acl_commands.append(f"access-list 101 {action} ip {source_ip} {wildcard_mask} any")
#     # Notice if there is no ACL rule
#     if not acl_commands:
#         print("[INFO] No ACL rules configured.")
#         return "[INFO] No ACL rules applied."
#     # Apply ACL to the specified interface
#     acl_commands.extend([
#         f"interface {interface}",
#         "ip access-group 101 in"
#     ])
#     try:
#         print(f"[INFO] Configuring ACL on {interface}...")
#         connection.send_config_set(acl_commands)
#         return f"[SUCCESS] ACL configured and applied to {interface} successfully"
#     except Exception as e:
#         return f"[ERROR] Failed to configure ACL: {str(e)}"
#
# # Configure IPSec
# def configure_ipsec(connection):
#     ipsec_commands = [
#         "crypto isakmp policy 10",
#         "encr aes",
#         "hash sha",
#         "authentication pre-share",
#         "group 2",
#         "crypto isakmp key MY_KEY address 0.0.0.0",
#         "crypto ipsec transform-set MY_TRANSFORM_SET esp-aes esp-sha-hmac",
#         "crypto map MY_CRYPTO_MAP 10 ipsec-isakmp",
#         "set peer 192.168.56.2",
#         "set transform-set MY_TRANSFORM_SET",
#         "match address 101",
#         "interface GigabitEthernet1",
#         "crypto map MY_CRYPTO_MAP"
#     ]
#     try:
#         print("[INFO] Configuring IPSec...")
#         connection.send_config_set(ipsec_commands)
#         # Verify IPSec status
#         ipsec_status = connection.send_command("show crypto ipsec sa")
#         print(f"[INFO] IPSec Security Associations:\n{ipsec_status}")
#         return "[SUCCESS] IPSec configured successfully"
#     except Exception as e:
#         return f"[ERROR] Failed to configure IPSec: {str(e)}"
#
# # Function to configure multiple devices concurrently
# def configure_multiple_devices(config):
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         futures = []
#         for device in config['devices']:
#             futures.append(executor.submit(configure_device, device, config))
#         for future in concurrent.futures.as_completed(futures):
#             print(future.result())
#
# # Configure a single device
# def configure_device(device, config):
#     connection = connect_to_device(device['username'], device['ip'], device['password'], device['secret'])
#     if connection:
#         print(f"[SUCCESS] Device {device['name']} is reachable!")
#
#         # Example usage: Configuring an interface
#         interface_result = config_interface(connection, "Loopback0", "10.1.1.1", "255.255.255.255", config, 'config.json')
#         print(interface_result)
#
#         # Example usage: Configuring OSPF
#         ospf_result = config_OSPF(connection)
#         print(ospf_result)
#
#         # Example usage: Configuring ACL for GigabitEthernet1
#         acl_result_g1 = configure_acl(connection, "GigabitEthernet1")
#         print(acl_result_g1)
#
#         # Example usage: Configuring ACL for Loopback0
#         acl_result_lb0 = configure_acl(connection, "Loopback0")
#         print(acl_result_lb0)
#
#         # Example usage: Configuring IPSec
#         ipsec_result = configure_ipsec(connection)
#         print(ipsec_result)
#
#         connection.disconnect()
#         print(f"[INFO] Disconnected from the device {device['name']}.")
#         return f"[SUCCESS] Configuration completed for device {device['name']}"
#     else:
#         return f"[ERROR] Unable to connect to device {device['name']}"
#
# if __name__ == "__main__":
#     config_file_path = 'config.json'
#     config = read_config(config_file_path)
#
#     # Configure multiple devices concurrently
#     configure_multiple_devices(config)
