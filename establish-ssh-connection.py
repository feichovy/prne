import yaml
from netmiko import ConnectHandler
import pexpect

# Read the configuration of the device from the YAML file
def read_config(file_path):
    try:
        with open(file_path,'r') as file:
            config = yaml.safe_load((file))
        return config # return a dictionary by pyyaml lab
    except FileNotFoundError:
        print(f"Error: The configuration file '{file_path}' was not found.")

# Telnet to the device, using pexpect lab.
def telnet_connect(ip, username, password, new_hostname, secret):
    try:
        t_connect = pexpect.spawn(f'telnet {ip}', timeout=30)

        # Login steps
        t_connect.expect('Username:')
        t_connect.sendline(username)
        t_connect.expect('Password:')
        t_connect.sendline(password)

        # expect '#' instead of '>'
        t_connect.expect('#')

        # Disable paging to get complete running-config
        t_connect.sendline('terminal length 0')
        t_connect.expect('#')

        # Change hostname
        t_connect.sendline('configure terminal') # avoid incomplete output, interrupted by prompt "--more--"
        t_connect.expect(r'\(config\)#')
        t_connect.sendline(f'hostname {new_hostname}')
        t_connect.expect(r'\(config\)#')
        print(f"Hostname changed successfully via Telnet to {new_hostname}")

        # Get running-config
        t_connect.sendline('exit')
        t_connect.expect('#')
        t_connect.sendline('show running-config')
        t_connect.expect('#')

        # Output the running-config and save to file locally
        running_config = t_connect.before.split('show running-config')[-1].strip()  # make sure only output configuration content
        with open(f'{new_hostname}_running-config.txt', 'w') as file:
            file.write(running_config)
        print(running_config)

        t_connect.sendline('exit')
        t_connect.close()
    except Exception as e:
        print(f"Failed to connect via Telnet: {e}")


# SSH to the device, using netmiko module.
def ssh_connect(ip,username,password,new_hostname,secret):
    try:
        network_device = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': username,
            'password': password,
            'secret': secret,
            'timeout': 30
        }# define a dictionary to store the configuration of device

        connection = ConnectHandler(**network_device) # generate SSH connect

        #  enter enable mode if not there
        if not connection.check_enable_mode():
            connection.enable()

        connection.config_mode() # enter configurate terminal
        connection.send_command(f'hostname {new_hostname}') # change the hostname
        connection.exit_config_mode()

        print(f"Hostname changed successfully via SSH to {new_hostname}")

        connection.send_command('terminal length 0') # avoid incomplete output, interrupted by prompt "--more--"
        # Output the running-config and save to file locally
        running_config = connection.send_command('show running-config')
        with open(f'{new_hostname}_running-config.txt','w') as file:
            file.write(running_config)
        print(f'Running-config saved to {new_hostname}_running-config.txt')

        connection.disconnect()
    except Exception as e:
        print(f"Faild to connect via SSH: {e}")

# Main program
def main():
    config = read_config('config.yaml') # Using relative path, make sure scriptions and yaml file in the same directiory.
    if config is None:
        return
    for device in config['device']: # using a loop to configure all the devices
        ip = device['ip']
        username = device['username']
        password = device['password']
        connection_type = device['connection_type']
        secret = device['secret']
        new_hostname = input(f"Enter the new hostname for {device['name']}:") # input new hostname

        if connection_type == 'telnet':
            telnet_connect(ip, username, password, new_hostname,secret)
        elif connection_type == 'ssh':
            ssh_connect(ip, username, password, new_hostname,secret)
        else:
            print(f"Please input valid connection type for device {device['name']}")


if __name__ == "__main__":
    main()
