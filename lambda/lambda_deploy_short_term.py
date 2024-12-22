import json
import os
from datetime import datetime, timezone
import boto3

ec2 = boto3.client('ec2')

def list_instances():
    # EC2インスタンスのフィルタ: Running 状態のインスタンスのみ取得
    response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
    )

    # インスタンスIDとNameタグを取得するためのリストを作成
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            launch_time = instance['LaunchTime']

            # Nameタグを探す
            instance_name = ''
            if 'Tags' in instance:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']

            # インスタンスIDとNameをリストに追加
            instances.append({
                'InstanceId': instance_id,
                'Name': instance_name,
                'LaunchTime': launch_time
            })

    return instances

def stop_instance(instance_id):
    try:
        # インスタンスの停止
        response = ec2.stop_instances(InstanceIds=[instance_id])

        # インスタンスの停止状態を取得
        stopping_instances = response['StoppingInstances']

        for instance in stopping_instances:
            current_state = instance['CurrentState']['Name']
            previous_state = instance['PreviousState']['Name']
            print(f"インスタンス {instance_id} は {previous_state} から {current_state} に変わりました")

        return {
            'statusCode': 200,
            'body': f'インスタンス {instance_id} が停止されました'
        }

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'インスタンス {instance_id} の停止中にエラーが発生しました: {str(e)}'
        }


def start_instance(launch_template_id):
    current_date = datetime.now().strftime('%Y%m%d')
    instance_name = f'CowrieShortTerm-{current_date}'

    try:
        # 起動テンプレートからインスタンスを起動
        response = ec2.run_instances(
            LaunchTemplate={
                'LaunchTemplateId': launch_template_id,
            },
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': instance_name
                        }
                    ]
                }
            ]
        )

        # 新しく起動されたインスタンスIDを取得
        instance_id = response['Instances'][0]['InstanceId']
        print(f"新しいインスタンスが起動されました: {instance_id}")

        return {
            'statusCode': 200,
            'body': f'インスタンス {instance_id} がテンプレート {launch_template_id} から起動されました'
        }

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'インスタンス起動中にエラーが発生しました: {str(e)}'
        }

def lambda_handler(event, context):
    # 今日の日付を取得
    today = datetime.now(timezone.utc)

    # インスタンスのリストを取得
    instances = list_instances()

    for instance in instances:
        instance_name = instance['Name']

        # CowrieShortTerm-* のインスタンスのみ処理
        if instance_name.startswith('CowrieShortTerm-'):
            # インスタンスの起動日を取得
            launch_date = instance['LaunchTime']

            # 起動日からの経過日数を計算
            days_running = (today - launch_date).days

            # 起動してから4日以上経過しているかを確認
            if days_running >= 4:
                print(f"インスタンス {instance['InstanceId']} を停止します (Name: {instance_name})")
                stop_instance(instance['InstanceId'])


    # 新しいインスタンスを起動
    launch_template_id = os.getenv('COWRIE_TEMPLATE')
    if launch_template_id:
        start_instance(launch_template_id)
    else:
        print("COWRIE_TEMPLATE 環境変数が設定されていません")

    return {
        'statusCode': 200,
        'body': 'Lambda実行が完了しました'
    }
