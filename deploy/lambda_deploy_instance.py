import os
import boto3

# Get the Launch Template IDs from environment variables
LAUNCH_TEMPLATE_COWRIE_BASE = os.getenv('LAUNCH_TEMPLATE_COWRIE_BASE')
LAUNCH_TEMPLATE_COWRIE_RANDOM_SSH = os.getenv('LAUNCH_TEMPLATE_COWRIE_RANDOM_SSH')

# Initialize a session using Amazon Lambda
session = boto3.Session()
ec2 = session.client('ec2')

def create_instance(launch_template_id, template_name):
    if not launch_template_id:
        print(f"Launch Template ID が設定されていません: {template_name}")
        return

    response = ec2.run_instances(
        MinCount=1,
        MaxCount=1,
        LaunchTemplate={
            'LaunchTemplateId': launch_template_id
        },
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': template_name
                    }
                ]
            }
        ]
    )
    print("Instance created:", response['Instances'][0]['InstanceId'])

def lambda_handler(event, context):
    launch_template_ids = {
        "COWRIE_BASE": LAUNCH_TEMPLATE_COWRIE_BASE,
        "COWRIE_RANDOM_SSH": LAUNCH_TEMPLATE_COWRIE_RANDOM_SSH
    }

    for template_name, launch_template_id in launch_template_ids.items():
        print(template_name, launch_template_id)
        create_instance(launch_template_id, template_name)
