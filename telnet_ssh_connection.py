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
def telnet_connect(ip, username, password, new_hostname):
    try:
        t_connect = pexpect.spawn(f'telnet {ip}') # generate subprocess

        t_connect.expect('Username:') # enter console
        t_connect.sendline(username)

        t_connect.expect('>') # enter previlege mode
        t_connect.sendline('enable')
        t_connect.expect('Password:')
        t_connect.sendline(password)
        t_connect.expect('#')

        t_connect.sendline('configure terminal') # enter configutation terminal
        t_connect.expect(r'\(config\)#')
        t_connect.sendline(f'hostname {new_hostname}') # change the hostname
        print(f"Hostname changed successfully via Telnet to {new_hostname}")

        # Output the running-config and save to file locally
        t_connect.sendline('exit')
        t_connect.expect('#')
        t_connect.sendline('sh running-conf')
        t_connect.expect('#') # to avoid 'sh running-conf' incomplete execution

        running_config = t_connect.before.decode() # save the running-config to file locally
        with open(f'{new_hostname}_running-config.txt','w') as file:
            file.write(running_config)
        print(f"Running-config saved to {new_hostname}_running-config") # output the running-config, python would create the file automatically

        t_connect.sendline('exit')
        t_connect.close()
    except Exception as e:
        print(f"Failed to connect via Telnet: {e}") # catch the errors

# SSH to the device, using netmiko lab.
def ssh_connect(ip,username,password,new_hostname):
    try:
        network_device = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': username,
            'password': password,
        }# define a dictionary to store the configuration of device

        connection = ConnectHandler(**network_device) # generate SSH connect
        connection.enable() # enter previlege mode

        connection.config_mode() # enter configurate terminal
        connection.send_command(f'hostname {new_hostname}') # change the hostname
        connection.exit_config_mode()

        print(f"Hostname changed successfully via SSH to {new_hostname}")

        # Output the running-config and save to file locally
        running_config = connection.send_command('sh running-config')
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
        new_hostname = input(f'Enter the new hostname for {device['name']}:') # input new hostname

        if connection_type == 'telnet':
            telnet_connect(ip, username, password, new_hostname)
        elif connection_type == 'ssh':
            ssh_connect(ip, username, password, new_hostname)
        else:
            print(f"Please input valid connection type for device {device['name']}")


if __name__ == "__main__":
    main()
