# Remember SSH to device manually at first time
import difflib
import tkinter as tk
from tkinter import simpledialog, messagebox # Creating simple GUI
import yaml
from netmiko import ConnectHandler
from tkinter.scrolledtext import ScrolledText # Enable users to scroll down in the output

# Hardened configuration guidelines as a Python dictionary
HARDEN_CONFIG = [
    'service password-encryption',
    'no ip http server',
    'no cdp run',
    'no ip source-route',
    'transport input ssh',
    'no transport input telnet'
]

def read_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config  # return a dictionary by pyyaml lab
    except FileNotFoundError:
        print(f"Error: The configuration file '{file_path}' was not found.")

        # Create a default YAML file if not found
        default_config = {
            'devices': [
                {
                    'name': 'default_device',
                    'ip': '192.168.1.1',
                    'username': 'admin',
                    'password': 'password',
                    'connection_type': 'ssh',
                    'secret': 'enable_password'
                }
            ]
        }

        with open(file_path, 'w') as file:
            yaml.dump(default_config, file)

        print(f"A default configuration file '{file_path}' has been created. Please update it with the correct device information.")
        return default_config


def create_ssh_connection(ip, secret, username, password):
    # Connect to device and enter into previlledge mode
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
        connection.enable()
        # Avoiding incomplete output
        connection.send_command('terminal length 0')
        return connection
    except Exception as e:
        print(f"Fail to connect via SSH :{e}")
        return None


def compare_running_with_startup(connection):
    try:
        # Using 2 variables to store the configurations
        running_config = connection.send_command('show running-config')
        startup_config = connection.send_command('show startup-config')
        # Using diff lib to collect the differecences between files and save it
        diff = difflib.unified_diff(startup_config.splitlines(), running_config.splitlines(),
                                    fromfile='Startup-Configuration', tofile='Running-Configuration', lineterm='')
        diff_output = list(diff)
        if not diff_output:
            # Displaying window to inform users
            messagebox.showinfo("Comparison Result", "No differences found between running-config and startup-config.")
        else:
            show_colored_diff(diff_output, "Differences between running-config and startup-config:")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to compare running-config with startup-config: {e}")


def compare_running_with_local(connection, local_file_path):
    try:
        running_config = connection.send_command('show running-config')
        with open(local_file_path, 'r') as file:
            local_config = file.read()
        diff = difflib.unified_diff(local_config.splitlines(), running_config.splitlines(),
                                    fromfile='Local Configuration', tofile='Running Configuration', lineterm='')
        diff_output = list(diff)
        if not diff_output:
            # Displaying window to inform users
            messagebox.showinfo("Comparison Result", "No differences found between running-config and local configuration.")
        else:
            show_colored_diff(diff_output, "Differences between Running Configuration and Local Configuration:")
    except FileNotFoundError:
        # Displaying window to inform users
        messagebox.showerror("Error", f"The local configuration file '{local_file_path}' was not found.")
    except Exception as e:
        # Displaying window to inform users
        messagebox.showerror("Error", f"Failed to compare running-config with local configuration: {e}")


def compare_running_with_harden(connection):
    try:
        running_config = connection.send_command('show running-config')
        running_config_lines = running_config.splitlines()
        # Define a list to store the missing Harden Configuration
        missing_configs = []
        for config in HARDEN_CONFIG:
            if config not in running_config_lines:
                missing_configs.append(config)

        if not missing_configs:
            # Displaying window to inform users
            messagebox.showinfo("Hardening Check", "All hardening configurations are present in the running configuration.")
        else:
            result = "The following hardening configurations are missing from the running configuration:\n"
            for config in missing_configs:
                result += f"  [Missing] {config}\n"
            # Displaying window to inform users
            messagebox.showinfo("Hardening Check Result", result)
    except Exception as e:
        # Displaying window to inform users
        messagebox.showerror("Error", f"Failed to compare running-config with hardening guidelines: {e}")


def config_syslog(connection, syslog_server_ip):
    try:
        command = f'logging host {syslog_server_ip}'
        connection.send_config_set([command])
        # Displaying window to inform users
        messagebox.showinfo("Success", f"Syslog server {syslog_server_ip} configured successfully.")
    except Exception as e:
        # Displaying window to inform users
        messagebox.showerror("Error", f"Failed to configure syslog server: {e}")


def show_colored_diff(diff_output, title):
    diff_window = tk.Toplevel() # Create a new top window to show the differences
    diff_window.title(title) # Set the title for the window
    text_area = ScrolledText(diff_window, width=100, height=30) # Create a Scrollable text area
    text_area.pack(fill=tk.BOTH, expand=True) # Fill the entire window and expand automatically when the window is resized
    # Read difference line by line
    for line in diff_output:
        # Using added to tag the added lines
        if line.startswith('+') and not line.startswith('+++'):
            text_area.insert(tk.END, f"{line}\n", 'added')
        # Using removed to tag the removed lines
        elif line.startswith('-') and not line.startswith('---'):
            text_area.insert(tk.END, f"{line}\n", 'removed')
        # Using context to tag the context lines
        elif line.startswith('@'):
            text_area.insert(tk.END, f"{line}\n", 'context')
        # Other lines are inserted directly
        else:
            text_area.insert(tk.END, f"{line}\n")

    text_area.tag_config('added', foreground='red') # Using red font to notice added lines
    text_area.tag_config('removed', foreground='blue')# Using blue font to notice removed lines
    text_area.tag_config('context', foreground='green')# Using green font to notice context lines
    # Set area as only read to prevent modification
    text_area.config(state=tk.DISABLED)

def main_():
    # Create a root tkinter window
    root = tk.Tk()
    root.withdraw()  # Hide the root window cause we don't need to display it

    config = read_config('config.yaml')
    if config is None:
        return

    for device in config['devices']:
        ip = device['ip']
        username = device['username']
        password = device['password']
        secret = device['secret']
        connection = create_ssh_connection(ip, secret, username, password)

        if not connection:
            continue

        while True:
            choice = simpledialog.askstring("Select Option", "Enter your choice:\n1. Compare Running with Startup Configuration\n2. Compare Running with Local Configuration\n3. Compare Running with Harden Configuration\n4. Configure Syslog Server\n0. Exit")

            if choice == '0':
                connection.disconnect()
                break
            elif choice == '1':
                compare_running_with_startup(connection)
            elif choice == '2':
                local_file_path = simpledialog.askstring("Input", "Enter the local configuration file path:")
                if local_file_path:
                    compare_running_with_local(connection, local_file_path)
            elif choice == '3':
                compare_running_with_harden(connection)
            elif choice == '4':
                syslog_server_ip = simpledialog.askstring("Input", "Enter the syslog server IP:")
                if syslog_server_ip:
                    config_syslog(connection, syslog_server_ip)
            else:
                messagebox.showwarning("Invalid Choice", "Please enter a valid number between 0 and 4.")

if __name__ == "__main__":
    main_()
