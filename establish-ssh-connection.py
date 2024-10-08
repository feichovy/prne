# Import required modules/packages/library
import pexpect

# Define variables
ip_address = '192.168.56.101'
username = 'prne'
password = 'cisco123!'
password_enable = 'class123!'

# Create the SSH session
session = pexpect.spawn('ssh ' + username + '@' + ip_address,
 encoding='utf-8', timeout=20)
result = session.expect(['Password:', pexpect.TIMEOUT, pexpect.EOF])

# Check for error, if exists then display error and exit
if result != 0:
print('--- FAILURE! creating session for: ', ip_address)
exit()

# Session expecting password, enter details
session.sendline(password)
result = session.expect(['>', pexpect.TIMEOUT, pexpect.EOF])
# Check for error, if exists then display error and exit
if result != 0:
 print('--- FAILURE! entering password: ', password)
exit()

# Enter enable mode
session.sendline('enable')
result = session.expect(['Password:', pexpect.TIMEOUT, pexpect.EOF])
# Check for error, if exists then display error and exit
if result != 0:
 print('--- Failure! entering enable mode')
 exit()
# Send enable password details
session.sendline(password_enable)
result = session.expect(['#', pexpect.TIMEOUT, pexpect.EOF])
# Check for error, if exists then display error and exit
if result != 0:
 print('--- Failure! entering enable mode after sending password')
exit()
