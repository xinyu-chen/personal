import paramiko
import logging

hostname = ''
username = ''
password = ''
source = ''
destination = ''

def sftp():
    # Instantiate client
    ssh_client = paramiko.SSHClient()
    # Set missing key policy (For local machine)
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=hostname, username=username,password=password)
    logging.info('Connected to server.')

    # Put file in server from local path
    ftp = ssh_client.open_sftp()
    ftp.put(source+'/'+payment_name+'.csv', destination)
    ftp.put(source+'/'+loan_tape_name+'.csv', destination)
    ftp.close