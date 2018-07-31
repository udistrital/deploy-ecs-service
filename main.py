import boto3
import json
import urllib
from urllib2 import Request, urlopen, URLError, HTTPError
import logging


taskRoles= {"develop":"arn:aws:iam::699001025740:role/apis_preprod", "master":"arn:aws:iam::699001025740:role/apis_prod"}
environmentMapping = {"develop":"desarrollo","master":["prod", "produccion"]}
serviceEnvironmentSufix = {"develop":"desarrollo","master":"prod"}
clusters = {"develop":"oas","master":"oas"}
serviceSeparator = "_"
taskDefinitionSeparator = "_"
memoryValue = 128


def getApiName(filepath):
    
    filename = filepath.split("/")[-1]
    filebase = filename.split(".")[0]
    fileArr = filebase.split("-")
    
    environment = fileArr[-1]
    apiName = fileArr[:-1]
    if isinstance(apiName,list):
        apiName = "-".join(apiName)
    return apiName, environment
    
def lambda_handler(event, context):
    client = boto3.client('ecs')
    
    filepath = event["Records"][0]["s3"]["object"]["key"]
    
    #filepath = "apps/titan-api-crud-develop.zip"
    
    apiName, environment = getApiName(filepath)
    
    for environmentMappingLabel in environmentMapping[environment]:
        try:
            familyName = apiName+taskDefinitionSeparator+environmentMappingLabel
            
            actualTaskDefinition = client.describe_task_definition(
                taskDefinition=familyName
            )
            break
        except:
            print "Tarea no encontrada"
    
    print actualTaskDefinition
    
    containerDefinition = actualTaskDefinition['taskDefinition']['containerDefinitions']
    print containerDefinition
    
    containerDefinition[0]['memoryReservation'] = memoryValue
    
    newTaskDefinition = client.register_task_definition(
        family=familyName,
        taskRoleArn=taskRoles[environment],
        containerDefinitions=containerDefinition)
    
    print newTaskDefinition
    
    serviceUpdated = client.update_service(
        cluster=clusters[environment],
        service=apiName+serviceSeparator+serviceEnvironmentSufix[environment],
        taskDefinition=newTaskDefinition["taskDefinition"]["taskDefinitionArn"])
    
    print serviceUpdated
    
    
    BOT_ID = "SECRET"
    CHAT_ID = "-129350403"
    API_ENDPOINT = "https://api.telegram.org/%s/sendMessage" % BOT_ID
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    message=apiName+" "+environment+" updated"
    msg = {
        "chat_id":CHAT_ID,
        "text": message
    }
    logger.info(str(msg))
    req = Request(API_ENDPOINT, urllib.urlencode(msg))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", CHAT_ID)
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)
    
    
    return True
