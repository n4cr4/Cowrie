import boto3

# EC2クライアントを作成
ec2_client = boto3.client('ec2')

# インスタンスIDリストを取得する
def get_running_instances():
    response = ec2_client.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
            {'Name': 'tag:Role', 'Values': ['Cowrie']}
        ]
    )

    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), instance_id)
            instances.append((instance_id, instance_name))

    return instances

# Lambdaハンドラー
def lambda_handler(event, context):
    # インスタンス情報を取得
    instances = get_running_instances()

    # インスタンス情報をログに出力
    for instance_id, instance_name in instances:
        print(f"Instance ID: {instance_id}, Instance Name: {instance_name}")

    # インスタンス情報を返す
    return {
        "statusCode": 200,
        "body": {"instances": [{"instance_id": instance_id, "instance_name": instance_name} for instance_id, instance_name in instances]}
    }
