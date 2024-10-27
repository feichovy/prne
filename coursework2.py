import difflib
from telnet_ssh_connection import read_config
from netmiko import ConnectHandl er
def create_ssh_connection(ip,secret,username,password):
    try:
        network_device = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': username,
            'password': password,
            'secret': secret,
            'timeout': 30
        }
        connection = ConnectHandler(**network_device)
        return connection
    except Exception as e:
        print(f"Fail to connect via SSH :{e}")

def compare_running_with_startup(connection):
    try:
        connection.config_mode()
        connection.send_command('terminal length 0')
        running_config = connection.send_command('show running-config')
        startup_config = connection.send_command('show startup-config')
        diff = difflib.unified_diff(startup_config.splitlines(),running_config.splitlines(),
                                    fromfile='Startup-Configuration',tofile='Running-Configuration',lineterm='')
        diff_output = list(diff)
        if not diff_output:
            print("No differences found between running-config and startup-config.")
        else:
            print("Differences between running-config and startup-config:")
            for line in diff_output:
                if line.startswith('+') and not line.startswith('+++'):
                    print(f"[Added]{line[1:]}")
                elif line.startswith('-') and not line.startswith('---'):
                    print(f"[Removed]{line[1:]}")
                elif line.startswith('@'):
                    print(f"[Context] {line}")
    except Exception as e:
        print(f"Failed to compare running-config with startup-config: {e}")

def compare_running_with_local(connection,local_file_path):
    try:
        connection.config_mode()
        connection.send_command('terminal length 0')
        running_config = connection.send_command('show running-config')
        with open(local_file_path,'r') as file:
            local_config = file.read()
        diff = difflib.unified_diff(local_config.splitlines(), running_config.splitlines(),
                                    fromfile='Local Configuration', tofile='Running Configuration', lineterm='')
        diff_output = list(diff)
        if not diff_output:
            print("No differences found between running-config and local configuration.")
        else:
            print("Differences between Running Configuration and Local Configuration:")
            for line in diff_output:
                if line.startswith('+') and not line.startswith('+++'):
                    print(f"[Added] {line[1:]}")
                elif line.startswith('-') and not line.startswith('---'):
                    print(f"[Removed] {line[1:]}")
                elif line.startswith('@'):
                    print(f"[Context] {line}")
    except FileNotFoundError:
        print(f"Error: The local configuration file '{local_file_path}' was not found.")
    except Exception as e:
        print(f"Failed to compare running-config with local configuration: {e}")


def config_syslog(connection, syslog_server_ip):


def main_():
    config = read_config('config.yaml')
    if config is None:
        return

    for device in config['devices']:
        ip = device['ip']
        username = device['username']
        password = device['password']
        secret = device['secret']
        syslog_server_ip = input(f"Enter the syslog server IP for {device['name']}:")
        local_file_path = input(f"Enter the local configuration file path for {device['name']}:")
        connection = create_ssh_connection(ip,username,password,secret)
        if not connection:
            return

        while True:
            print("\nSelect an option:")
            print("1. Compare Running with Startup Configuration")
            print("2. Compare Running with Local Configuration")
            print("3. Compare Running with Harden Configuration")
            print("4. Configure Syslog Server")
            print("0. Exit")
            choice = input("Enter your choice (0-4): ")

            if choice == '0':
                connection.disconnect()
                break
            elif choice == '1':
                compare_running_with_startup(connection)
            elif choice == '2':
                compare_running_with_local(connection, local_file_path)
            elif choice == '3':
                harden_config_path = input("Enter the hardening configuration file path: ")
                compare_running_with_harden(connection, harden_config_path)
            elif choice == '4':
                config_syslog(connection, syslog_server_ip)
            else:
                print("Invalid choice. Please enter a number between 0 and 4.")

if __name__ == "__main__":