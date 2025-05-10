import logging.handlers
import os 
import time
import shutil
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
import boto3
from boto3 import client
import threading

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

def firstsetup():
    ## Setup required directories and files.
    folderpath = "/etc/NinjaEye/"
    folders = ["logs", "logs/alerts"]
    file_paths = ["logs/log.txt"]

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



def alertmonitoring():  ## Monitors for incoming files in tmp folder and alerts the user if there is one then stores the file
    CHANNEL_ID = os.getenv('CHANNEL_ID')    
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
    folderpath = "/tmp/" ##where files are stored

    ## Code belows splits the file name into sections and stores sets them to "reason" variable to allow ease of passing in slack
    while True:
        for filename in os.listdir(folderpath):
            if filename.startswith("NINJAEYE"):
                source = os.path.join(folderpath, filename)
                destination = "/etc/NinjaEye/alerts"
                shutil.move(source, destination)
                print(f"ALERT! See {destination}/{filename} for more information!")
                logger.info(f"Detected alert and moved to {destination}/{filename}")
                parts = filename.split(':')
                if len(parts) >= 4:
                    prefix = parts[0]
                    ip_address = parts[1]
                    current_time = parts[2]
                    filereason = parts[3]
                else:
                    prefix = "NINJAEYE"
                    ip_address = "Unknown"
                    current_time = "Unknown"
                    filereason = "Unknown"
                
                reason = (f"ALERT! A issue has been detected and moved to {destination}\n"
                          f"Prefix: {prefix}\n"
                          f"IP Address: {ip_address}\n"
                          f"Time: {current_time}\n"
                          f"File Reason: {filereason}")
                
                send_message(CHANNEL_ID, SLACK_BOT_TOKEN, reason)
        time.sleep(5) ##sleep for performance



def get_cat_image():
    ## Code below helper function resposible for getting a random cat image from the API and returning the URL to be passed into slack

    logger.info("Attempting to fetch random cat image")
    CAT_API_KEY = os.getenv('CAT_API_KEY')
    CAT_API_URL = os.getenv('CAT_API_URL')
    headers = {"x-api-key": CAT_API_KEY}
    response = requests.get(CAT_API_URL, headers=headers)
    if response.status_code == 200:
        immage_url = response.json()[0]["url"]
        logger.info(f"Fetched cat image URL: {immage_url}")
        return response.json()[0]["url"]
    return None

def send_message(channel, SLACK_BOT_TOKEN, reason):
    #function responsible for sending slack messages. 

    logger.info(f"attempting to send message to slack channel")
    client = WebClient(token=SLACK_BOT_TOKEN)
    cat_image_url = get_cat_image()
    if not cat_image_url:
        cat_image_url = "https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg"  # Fallback image
        logger.info(f"Failed to fetch cat image, using fallback image {cat_image_url}") 

    ##blocks used to format the slack message.
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Alert!",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{reason}\n"
	

            },
            "accessory": {
                "type": "image",
                "image_url": cat_image_url,
                "alt_text": "Random cat image"
            }
        },
    ]

    try:
        response = client.chat_postMessage(channel=channel, blocks=blocks, text="NinjaEye Alert!")
        logger.info(f"Message sucesfully sent to slack")

    except SlackApiError as e:
        logger.error(f"Error sending message to slack: {e.response['error']}")


def monitor_S3(): ##Modified code from AWS S3 Documentation:  Code examples for Amazon S3 using AWS SDKs - Amazon Simple Storage Service (no date). Available at: https://docs.aws.amazon.com/AmazonS3/latest/API/service_code_examples_s3.html (Accessed: 02 April 2025).

    Access_Key = os.getenv('AccessKey')
    Secret_Key = os.getenv('SecretAccessKey')
    BUCKET_NAME = os.getenv('BUCKET_NAME')
    REGION = os.getenv('REGION')

    ##code itterates over each function in the bucket and downloads it to the /tmp folder then deletes it to save storage. 
    while True:
        try: 
            logger.info("Attempting to access S3 bucket")
            client = boto3.client(
                's3',
                aws_access_key_id=Access_Key,
                aws_secret_access_key=Secret_Key,
                region_name=REGION
            )

            bucketItems = client.list_objects(
                Bucket=BUCKET_NAME
            )
            
            if 'Contents' not in bucketItems:
                logger.info("No files in bucket")
                
            else:
                logger.info("Files found on s3 bucket")
                for item in bucketItems['Contents']:
                    key = item['Key']
                    file_path = os.path.join("/tmp/", key)
                    logger.info(f"Downloading {key} to {file_path}")
                    
                    client.download_file(BUCKET_NAME, key, file_path)
                    client.delete_object(Bucket=BUCKET_NAME, Key=key) ##reccomended to delete the file after download to save space, however optional and can be removed retention is needed. 
                    logger.info(f" {key} removed from S3.") 
                
            time.sleep(5)  ##sleep for performance

        except client.exceptions.NoSuchBucket:
            logger.error("The specified bucket does not exist.")
            return False
        except client.exceptions.ClientError as e:
            logger.error(f"Client error: {e}")
            return False

        except Exception as e:
            logger.error(f"Error accessing S3 bucket: {e}")
            return False
    


if __name__ == "__main__":
    
    firstsetup()
    alertmonitoringThread = threading.Thread(target=alertmonitoring, daemon=True)  ## Create a thread for the alertmonitoring function
    alertmonitoringThread.start() ## Start the thread
    monitor_S3Thread = threading.Thread(target=monitor_S3, daemon=True)  ## Create a thread for the monitor_S3 function
    monitor_S3Thread.start() ## Start the thread

    alertmonitoringThread.join() ## waits for both threads to finish before exiting the program.
    monitor_S3Thread.join()