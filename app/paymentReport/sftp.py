import logging
import sys


#find folder directory
direct = sys.argv[0].split('/')
direct = '/'.join(direct[:-1])

import paramiko

hostname = 'sftp.peeriq.com'
username = 'behalf'
password = 'Behalf2017!'
directory = '/Inbound/'
source = '/opt/behalf/cto/reporting/data/'

today = dt.datetime.today().strftime('%Y_%m_%d')
loan_tape_name = 'lt_' + today
payment_name = 'p_' + today

key_filename = direct+'/id_rsa'
# Instantiate client
ssh_client = paramiko.SSHClient()
# Accept server public key
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# Connect and autheticate with password
ssh_client.connect(hostname=hostname, username=username,password=password, key_filename = key_filename)
logging.info('Connected to server.')

# Put file in server from local path
ftp = ssh_client.open_sftp()
ftp.put(source+'/'+payment_name, directory+payment_name)
ftp.put(source+'/'+loan_tape_name, directory+loan_tape_name)
ftp.close()