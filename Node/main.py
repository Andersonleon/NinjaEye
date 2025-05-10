
import os
import datetime
import time
from dotenv import load_dotenv
import threading 
import boto3
from boto3 import client
import logging
import subprocess
import json


load_dotenv() 

##code below is resposible for setting up the logging system

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    "/etc/NinjaEye/logs/log.txt", maxBytes=1000000, backupCount=10 ##rolling logs to save space
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)



print(r"""


.--------------------------------------------------------.
|                                                        |
|                                                        |
|   ________   ___  ________         ___  ________       |
|  |\   ___  \|\  \|\   ___  \      |\  \|\   __  \      |
|  \ \  \\ \  \ \  \ \  \\ \  \     \ \  \ \  \|\  \     |
|   \ \  \\ \  \ \  \ \  \\ \  \  __ \ \  \ \   __  \    |
|    \ \  \\ \  \ \  \ \  \\ \  \|\  \\_\  \ \  \ \  \   |
|     \ \__\\ \__\ \__\ \__\\ \__\ \________\ \__\ \__\  |
|      \|__| \|__|\|__|\|__| \|__|\|________|\|__|\|__|  |
|                                                        |
|                                                        |
|                                                        |
|   _______       ___    ___ _______                     |
|  |\  ___ \     |\  \  /  /|\  ___ \                    |
|  \ \   __/|    \ \  \/  / | \   __/|                   |
|   \ \  \_|/__   \ \    / / \ \  \_|/__                 |
|    \ \  \_|\ \   \/  /  /   \ \  \_|\ \                |
|     \ \_______\__/  / /      \ \_______\               |
|      \|_______|\___/ /        \|_______|               |
|               \|___|/                                  |
|                                               V1.0     |
|                                      Leon Anderson     |
'--------------------------------------------------------'


""")

def configsetup(path="/home/ubuntu/Desktop/config.json"):
    ##loads configuration json to assist file monitoring
    try:
        with open(path, "r") as file:
            config = json.load(file)
        logger.info("config.json loaded sucessfuly")
        return config
    
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        exit(1)

config = configsetup()  

def firstsetup():
    ## function that is responsible for setting up the directories and files needed for the program to run
    folderpath = "/etc/NinjaEye/"
    folders = ["logs", "logs/alerts", "file_compare"]
    file_paths = ["logs/log.txt"]

    ##creates the folders and files needed for the program to run
    try:
        
        for folder_name in folders:
            folder_path = os.path.join(folderpath, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            logger.info(f"Created directory: {folder_path}")

        
        for file_name in file_paths:
            file_path = os.path.join(folderpath, file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)  
            if not os.path.exists(file_path):
                logger.info(f"Creating file: {file_path}")
                with open(file_path, 'w') as f:
                    pass  

        print(f"Directories and files set up successfully in {folderpath}.")
    except PermissionError:
        print("Permission denied: Please run the script with elevated privileges.")
        exit(1)
  

def get_env_variable():
    ## function that loads the enviroment variables from the .env file needed for scp
    try:
       ip_address = os.getenv('IP_ADDRESS')
       ssh_username = os.getenv('SSH_USERNAME')
    
       logger.info("loaded enviroment variables")
       return ip_address, ssh_username
    
    except Exception as e:
        logger.error(f"An error occurred when loading the enviroment variables: {e}")
        return None

def commandConnection(ip_address, ssh_username, data, filereason):    
    ##main function used for connecting to command node using scp and S3
    currentTime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
    filename = f"NINJAEYE:{ip_address}:{currentTime}:{filereason}"  
    filepath = f"/etc/NinjaEye/logs/alerts/{filename}"

    ## Write "data" to file 
    with open(filepath, "w") as f:
        f.write(data)
    logger.info(f"Created alert: {filepath}")

    upload_to_s3(filepath) ##uploads to aws
    subprocess.run(f"scp {filepath} {ssh_username}@{ip_address}:/tmp", shell=True)
    logger.info(f"alert sent to {ssh_username}@{ip_address}:/tmp through scp")
    return


def sshLog(): ## gathers ssh logs and places them into a compare file
        sshCmd = "grep sshd /var/log/auth.log > /etc/NinjaEye/logs/ssh.txt"  
        subprocess.run(sshCmd, shell=True)
        logger.info(f"ssh log created using command: {sshCmd}")
        sshCompare() ## calls the ssh compare function to compare the logs


def sshCompare(): ## comparison function of ssh logs to predefined ssh log
    filereason = "unauthorizedSSH" 
    while True:

        sshCmd = "grep sshd /var/log/auth.log > /etc/NinjaEye/logs/sshCompare.txt"  
        subprocess.run(sshCmd, shell=True)
        logger.info(f"ssh log created using command: {sshCmd}")

        afterLog = open("/etc/NinjaEye/logs/sshCompare.txt")
        beforeLog = open("/etc/NinjaEye/logs/ssh.txt")

        logger.info("ssh comparison started")

        beforeLog_data = beforeLog.readlines()
        afterLog_data = afterLog.readlines()

        before_set = set(beforeLog_data)
        after_set = set(afterLog_data)
    
        differences = after_set - before_set ##diffrences between the two files

        if differences:
            alert_data = "" 
            for line in differences:
                logger.warning(f"ALERT! {line.strip()}")
                alert_data += line ##combines the alert data 

                ##sends information to command 
            commandConnection(ip_address, ssh_username, alert_data, filereason)  ##call helped function too parse information to command
            updatedLog = open("/etc/NinjaEye/logs/ssh.txt", "w")
            updatedLog.writelines(afterLog_data)
            updatedLog.close()
            logger.info("ssh log /etc/NinjaEye/logs/ssh.txt updated with new data")

        else:
            logger.info("No differences found in ssh logs.")


        afterLog.close()
        beforeLog.close()
        time.sleep(time_interval) ##checks after time interval set in config.json



def fileCompare(path, label, time_interval):
    ##function responsible for comparing files/folders using os.stat


    filereason = "unauthorizedAccess"
    beforefile = f"/etc/NinjaEye/file_compare/{label}_before.txt"
    afterfile = f"/etc/NinjaEye/file_compare/{label}_after.txt"

    open(beforefile, "a").close()
    open(afterfile, "a").close()

    test =  os.stat(path) ## the file that is being accessed to test the function using nano
    logger.info("files are being checked using stat")

    with open(beforefile, "w") as file: 
        file.write(f"{test.st_atime} : {test.st_mtime} \n")
    logger.info(f"{beforefile} modified wth updated timestamp")


    while True:

        monitoredfile = os.stat(path) ## the file that is being accessed to test the function using nano
        logger.info("files are being checked using stat")

        with open(afterfile, "w") as file:
            file.write(f"{monitoredfile.st_atime} : {monitoredfile.st_mtime} \n")
        logger.info(f"{afterfile} modified with updated timestamps")
        
        afterLog = open(afterfile) ## the file that has the current time the file was accessed
        beforeLog = open(beforefile)

        beforeLog_data = beforeLog.readlines()
        afterLog_data = afterLog.readlines()

        before_set = set(beforeLog_data)
        after_set = set(afterLog_data)
    
        differences = after_set - before_set 

        if differences:
            alert_data = "" 
            for line in differences:
                logger.warning(f"ALERT! {line.strip()}")
                alert_data += line #combines the alert data 

                ##sends information to command 
            commandConnection(ip_address, ssh_username, alert_data, filereason) ##call helper function too parse information to command

        else:
            logger.info("No differences found in file compare.")

        afterLog.close()
        beforeLog.close()

        with open(beforefile, "w") as file: 
            file.write(f"{monitoredfile.st_atime} : {monitoredfile.st_mtime} \n")
        logger.info(f"{beforefile} modified with updated timestamps")

        time.sleep(time_interval) 



def upload_to_s3(file_name, object_name=None): ##Modified code from AWS S3 Documentation:  Code examples for Amazon S3 using AWS SDKs - Amazon Simple Storage Service (no date). Available at: https://docs.aws.amazon.com/AmazonS3/latest/API/service_code_examples_s3.html (Accessed: 02 April 2025).
##function that uploads the alert file to S3 bucket using boto3


    Access_Key = os.getenv('AccessKey')
    Secret_Key = os.getenv('SecretAccessKey')
    BUCKET_NAME = os.getenv('BUCKET_NAME')
    REGION = os.getenv('REGION')

    if object_name is None:
        object_name = os.path.basename(file_name)

    # Initialize S3 client
    logger.info("Initializing S3 client")
    s3 = boto3.client(
        's3',
        aws_access_key_id=Access_Key,
        aws_secret_access_key=Secret_Key,
        region_name=REGION
    )

    try:
        logger.info(f"Uploading {file_name} to s3")
        s3.upload_file(file_name, BUCKET_NAME, object_name)

        return True
    
    except FileNotFoundError:
        print(" File not found")
        logger.error("File not found")
        return False
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return False
    

if __name__ == "__main__":
  
    firstsetup()
    ip_address, ssh_username = get_env_variable()
    
    sshThread = threading.Thread(target=sshLog, daemon=True)  # Create a thread for the sshCompare function
    sshThread.start() ## Start the thread

    time_interval = config["monitored_files"]["time_interval"]

    for x in config["monitored_files"]["file_paths"]:
        label = x["filename"]
        path = x["filepath"]

        fileThread = threading.Thread(target=fileCompare, args=(path, label, time_interval), daemon=True)  # Create a thread for each name
        fileThread.start() ## Start the thread

    sshThread.join()  ##waits for both threads to finish before exiting the program.
    fileThread.join()
  