def main_():
    root = tk.Tk()
    root.withdraw()  # Hide the root window

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