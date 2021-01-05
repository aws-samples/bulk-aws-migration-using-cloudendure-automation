#Copyright 2008-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

#Permission is hereby granted, free of charge, to any person obtaining a copy of this
#software and associated documentation files (the "Software"), to deal in the Software
#without restriction, including without limitation the rights to use, copy, modify,
#merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#permit persons to whom the Software is furnished to do so.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import print_function
import sys
import requests
import json
import yaml
import os
import boto3
import datetime
from botocore.exceptions import ClientError

def createimage(session, headers, endpoint, HOST, projectname, configfile, region):
           
    r = requests.get(HOST + endpoint.format('projects'), headers=headers, cookies=session)
    if r.status_code != 200:
        print("ERROR: Failed to fetch the project....")
        sys.exit(1)
    try:
        # Get Project ID
        projects = json.loads(r.text)["items"]
        project_exist = False
        for project in projects:
            if project["name"] == projectname:
               project_id = project["id"]
               project_exist = True
        if project_exist == False:
            print("ERROR: Project Name does not exist....")
            sys.exit(2)
    except:
        print(sys.exc_info())
        sys.exit(6)
        
    with open(os.path.join(sys.path[0], configfile), 'r') as ymlfile:
     config = yaml.load(ymlfile, yaml.FullLoader)
    
    migration_wave = config["project"]["waves"]
              
    m = requests.get(HOST + endpoint.format('projects/{}/machines').format(project_id), headers=headers, cookies=session)
    
    data = json.loads(m.text)["items"]
    machinelist = {}
    machine_exist = False
    
    for machine in data:
      machinelist[machine['id']] = machine['sourceProperties']['name']
      machine_name=machine['sourceProperties']['name']
      r_id=machine['replica']
      
      r = requests.get(HOST + endpoint.format('projects/{}/replicas/{}').format(project_id, r_id), headers=headers, cookies=session)
      replicas = json.loads(r.text)
      instance_id = replicas['machineCloudId']
      machine_exist = True
      try:
          ec2_client = boto3.client("ec2", region_name=region)
      except ClientError as e:
          print("Unexpected error(Make sure you have entered correct AWS region & AWS credentials available on machine): %s" % e)
          return
      
      timestamp = datetime.datetime.utcnow().strftime('%Y%m%d')
      try:
          image = ec2_client.create_image(InstanceId=instance_id, Name=machine_name+'-'+timestamp, Description='Image of CloudEndure migrated instance: '+machine_name,
                                         NoReboot=True,
                                         TagSpecifications=[
                                            {
                                                'ResourceType': 'image',
                                                'Tags': [
                                                    {
                                                        'Key': 'Name',
                                                        'Value': machine_name
                                                    },
                                                    {
                                                        'Key': 'instance',
                                                        'Value': instance_id
                                                    },
                                                    {
                                                        'Key': 'migration-wave',
                                                        'Value': migration_wave
                                                    },                                                
                                                ]
                                            },
                                        ]
                                        )
          print("Image creation initiated for "+ machine_name + " with image id: " + image['ImageId'])  
      except:
          print("Create AMI failed")
      
    if machine_exist == False:
        print ('There are no machines launched in cutover mode. No instances available to create image.')
        return
          