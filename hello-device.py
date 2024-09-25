import pexpect
ping = pexpect.spawn('ping -c 5 localhost')
result = ping.expect([pexpect.EOF, pexpect.TIMEOUT])
print(ping.before.decode('utf-8', 'ignore'))
