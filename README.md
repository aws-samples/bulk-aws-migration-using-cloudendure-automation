
# Automated bulk AWS migration using CloudEndure 
Templates and scripts to automate the aws migration using CloudEndure.
This solution is ideal for bulk migration of 2 to 25+ servers in one go.

With this approach the servers are migrated in batches which is called as migration 'wave'.

If you have 50+ servers, it is recommended to use the Migration factory solution mentioned here https://docs.aws.amazon.com/solutions/latest/aws-cloudendure-migration-factory-solution/welcome.html

The python scripts are referenced from the [automating-aws-migration-with-cloudendure-scripts](https://github.com/aws-samples/automating-aws-migration-with-cloudendure-scripts) samples. 

## Prerequisites

1. Experience with the CloudEndure service, installing the agent, and using it from the console. Learn more about [how to use CloudEndure](https://docs.cloudendure.com/).
2. CloudEndure account created. Fill the simple form to create CloudEndure account and note the credentials used. [Get started now with free CloudEndure Migration licenses](https://migration-register.cloudendure.com/). CloudEndure migration licenses are provided at no cost for customers and partners.
3. Target AWS account to migrate the servers.

## Architecture
![Architecture diagram](CloudEndure-Migration-Pattern.png "Architecture")

## Files and their purpose

- **config-cutover.yml** – The config file for the production environment.
- **config-test.yml** – Config file for the test environment.
- **config-project.yml** – Config file for project replication settings.
- **CloudEndure.py** – Master Python script to drive the orchestration process.
- **CheckMachine.py** – Python script to check the status of the machine before migration.
- **LaunchMachine.py** – Python script to launch the machine in a test or production environment.
- **Machine.py** – Python script to call three other functions: check status, update blueprint, and launch target machines.
- **StatusCheck.py** – Python script to check the migration status of the target machine.
- **UpdateBlueprint.py** – Python script to update the machine blueprint, such as security group, subnet ID, tags, etc.
- **UpdateProject.py** – The Python script to update settings for the replication server, such as encryption key, security group ID, and subnet ID.
- **Cleanup.py** – Python script to remove machines from CloudEndure after cut over.
- **CreateCloudEndureProject.yml** - CloudFormation to create the CloudEndure project and AWS resources in target AWS account. 
- **MigrationExecutionServer.yml** - CloudFormation template to launch the Migration Execution server.

## Migration Steps

Assuming that you want to migrate the servers in single target AWS account, below are the steps to follow.
If you have servers to be migrated in different AWS accounts, please repeat below steps for each aws account.

### 1. Create CloudEndure project
- Login to target AWS account.
- Download the CloudEndureProjectLambda Lambda zip file from below link. https://marketplace-sa-resources.s3.amazonaws.com/ctlabs/migration/CloudEndureProjectLambda.zip
- Create a s3 bucket to upload the Lambda function zip file. This bucket will be referred in next step.
- Navigate to AWS CloudFormation console and **Create Stack** using the cloudformation template **CreateCloudEndureProject.yml**. Pass the above bucket as a parameter for lambda.
- Once the stack is created, it will create a CloudEndure project, IAM user & KMS key in AWS account. Note the KMS Key ARN from stack output.
- The created CloudEndure project will be linked to the AWS account from which it is created. 

### 2. Create Migration execution server
- Login to Target AWS account and create stack using CloudFormation template **MigrationExecutionServer.yml**. This will launch a Amazon Linux ec2 instance with required migration scripts. Make sure this server has access to internet to copy the 
scripts from the github repository as well as to call the CloudEndure APIs.
- The migration scripts(from the github) will be downloaded at bootstrapping of the ec2 at the location `/home/ec2-user/`. If for any reason it fails, you can download it from the repository using below command.
`wget https://github.com/aws-samples/bulk-aws-migration-using-cloudendure-automation/archive/master.zip` 

### 3. Config files preparation
- Make sure you already have a VPC created in target AWS account where you will migrate the servers. Identify the public and private subnets where migrated servers will be launched.
- Please change below configuration files on the Migration execution server we launched in previous step.
- **config-projects.yml** - To update the Replication Settings, edit this file with target encryption key, subnetID, securitygroupIDs. Get these value from step#1 cloudformation stack output section.
- **config-test.yml** - Add your servers to this file and update the subnet and security group IDs for the test environment.
- **config-cutover.yml** - Need to change the security groups and subnet IDs to the one in your production VPC. This file is similar to the Config-test.yml. 

### 4. Create Replication settings & Generate API token
- Login to CloudEndure and in Setup & Info > Replication Settings, configure fields like Migration Source, Migration Target, Replication Server instance type, Converter instance type, dedicated Replication Server option and keep other things as it is. We will change the Subnet, Security group and Encryption Key in next step via script.
- In CloudEndure console, click Setup & Info and choose Other Settings. Next, scroll down to the bottom. Do not use the installation token, which is for agent installation only. If the API token does not exist, click the Generate New Token button at the right bottom.
- Update the Replication settings. \
`python3 CloudEndure.py --userapitoken <APIToken> --projectname <project name> --configfile config-projects.yml --updateproject Yes`

### 5. Install CloudEndure Agent
- Go to CloudEndure and click on Machines. Copy the agent installation commands for source machines depending on the OS type.
- Goto the source machines and install the CloudEndure agent on them.
- As soon as the agent is installed, the machine will start the replication to CloudEndure. These machines will start appearing on the CloudEndure console.
- Wait until the DATA REPLICATION PROGRESS show as 'Continuous Data Replication'. This is indication to carry next steps.


### 6. Launch Test environment
- Before Test environment launch, validate the YAML syntax with dry run. \
`python3 CloudEndure.py --userapitoken <APIToken> --projectname <project name> --configfile config-test.yml --launchtype test --dryrun Yes`
- Launch the Test environment \
`python3 CloudEndure.py --userapitoken <APIToken> --projectname <project name> --configfile config-test.yml --launchtype test`
- Check the status of launch \
`python3 CloudEndure.py --userapitoken <APIToken> --projectname <project name> --configfile config-test.yml --launchtype test --statuscheck Yes`
- When Test environment launch is complete, please test the servers and application on it. If everything is OK, move ahead to launch the production environment.

### 7. Launch the Production Environment
- Validate YAML file syntax \
`python3 CloudEndure.py --userapitoken <APIToken> --projectname <project name> --configfile config-cutover.yml --launchtype cutover --dryrun Yes`
- Launch the Production environment  \
`python3 CloudEndure.py --userapitoken <APIToken> --projectname <project name> --configfile config-cutover.yml --launchtype cutover`
- Check the status of launch \
`python3 CloudEndure.py --userapitoken <APIToken> --projectname <project name> --configfile config-cutover.yml --launchtype cutover --statuscheck Yes`
- Test the final production servers. 

### 8. Clean up
- After complete migration, run the following command to remove machines from the CloudEndure console. This command will not terminate machines from AWS. \
`python3 CloudEndure.py --userapitoken <APIToken> --projectname <project name> --configfile config-cutover.yml --cleanup Yes`
- Also delete the CloudFormation stack for CloudEndureProject creation(step# 1) and Migration execution Server(step# 2) setup.


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License Summary
This sample code is made available under the MIT-0 license. See the LICENSE file.