import boto3

# SSMクライアントを作成
ssm_client = boto3.client('ssm')

# Lambdaハンドラー
def lambda_handler(event, context):
    # 受け取ったインスタンス情報を解析
    instances = event['body']['instances']

    # インスタンスごとに処理
    for instance in instances:
        instance_id = instance['instance_id']
        instance_name = instance['instance_name']

        # コマンド内容
        commands = [
            "cd /home/admin/Cowrie",
            "sudo docker compose cp cowrie:/cowrie/cowrie-git/var .",
            f"aws s3 cp var/log/cowrie/ s3://cowrie-log/{instance_name}/ --recursive"
        ]

        # SSM send_command の呼び出し
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": commands
            }
        )

        # コマンドIDを取得してログに出力
        command_id = response['Command']['CommandId']
        print(f"Command ID for instance {instance_name}: {command_id}")

    return {
        "statusCode": 200,
        "body": "Logs upload initiated for all instances"
    }
