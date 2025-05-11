
<h1 align="center">NinjaEye - Intrusion Detection and Prevention System</h1>
<p>
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-blue.svg?cacheSeconds=2592000" />
  <a href="#" target="_blank">
    <img alt="License: Apache License" src="https://img.shields.io/badge/License-Apache%202.0-yellow.svg" />
  </a>
</p>

# 

An open-source intrusion detection and prevention system for Debian-based systems.



## Demo

Coming soon...


## ✨ Features

- SSH Monitoring
- File Integrity Monitoring
- File Access Monitoring
- AWS S3 Integration
- Slack Integration
- Config Files

## ✅ Requirements

- Python 3.8+
- pip packages (install with `pip install -r requirements.txt`)
- Debian based system (e.g, Ubuntu)


## 📋 Installation

Clone the project with git

### Command 
```bash
  git clone https://github.com/Andersonleon/NinjaEye.git
  cd NinjaEye/Command
```
### Node

```bash
  git clone https://github.com/Andersonleon/NinjaEye.git
  cd NinjaEye/Node
```


## Deployment

To deploy this project run

### Command
```bash
  sudo python3 main.py
```

### Node
```bash
  sudo python3 main.py
```

## 🙈 Environment Variables

To run this project, you will need to have these variables assigned within there respected .env files.
### Command .env File
#### Slack Configuration
`SLACK_BOT_TOKEN`
`CHANNEL_ID`
#### Cat API Configuration
`CAT_API_KEY`
`CAT_API_URL`
#### AWS Configuration
`AccessKey`
`SecretAccessKey`
`BUCKET_NAME`
`REGION`

### Node .env File
#### SCP Configuration
`IP_ADDRESS`
`SSH_USERNAME`
#### AWS Configuration
`AccessKey`
`SecretAccessKey`
`BUCKET_NAME`
`REGION`


## 🛠️ Node Config.json Example Structure

```JSON
{
    "monitored_files": {
      "time_interval": 30,
      "file_paths": [
        {
          "filename": "test1",
          "filepath": "/home/ubuntu/Desktop/Folder1"
        },
        {
          "filename": "test2",
          "filepath": "/home/ubuntu/Desktop/test2.txt"
        },
        {
          "filename": "test3",
          "filepath": "/home/ubuntu/Desktop/test3.txt"
        }
      ]
    }
  }
  
```


## 📆 Features In Development

- Prevention Integration
- Process Monitoring
- Network Monitoring


## 👤 Author

 **Leon Anderson**

* Website: https://leonanderson.uk
* Github: [@Andersonleon](https://github.com/Andersonleon)
* LinkedIn: [@leonanderson2](https://www.linkedin.com/in/leonanderson2/)



