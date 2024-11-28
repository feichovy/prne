from netmiko import ConnectHandler
import json
from django.shortcuts import render
from django.http import HttpResponse
from .forms import DeviceConfigForm

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

# Write updated configuration back to the file
def write_config(file_path, config):
    try:
        with open(file_path, 'w') as file:
            json.dump(config, file, indent=4)
        print(f"[INFO] Configuration file '{file_path}' updated successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to update configuration file '{file_path}': {str(e)}")

# Django view for configuring device
def config_device(request):
    if request.method == 'POST':
        form = DeviceConfigForm(request.POST)
        if form.is_valid():
            # 获取表单数据
            ip = form.cleaned_data['ip']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            secret = form.cleaned_data['secret']
            interface = form.cleaned_data['interface']
            ip_addr = form.cleaned_data['ip_addr']
            mask = form.cleaned_data['mask']

            # 使用 Python 脚本配置设备
            connection = connect_to_device(username, ip, password, secret)
            if connection:
                result = config_interface(connection, interface, ip_addr, mask, {}, '')
                connection.disconnect()
                return HttpResponse(f"Configuration Result: {result}")
            else:
                return HttpResponse('[ERROR] Unable to connect to the device.')
    else:
        form = DeviceConfigForm()

    return render(request, 'network_app/config_device.html', {'form': form})
