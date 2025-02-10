import json
import os

def calculate_operation_stats(directory, threshold=100):
    """
    指定されたディレクトリ内のCowrieShortTerm-* ディレクトリにある daily_connect.json ファイルを処理し、
    閾値を超えた日の割合を計算します。

    Args:
        directory (str): CowrieShortTerm-* ディレクトリが含まれるディレクトリのパス。
        threshold (int, optional): 閾値。 デフォルトは 100。

    Returns:
        float: 閾値を超えた稼働日数の割合。ファイルが見つからない場合はNoneを返します.
    """

    total_days = 0
    threshold_exceeded_days = 0

    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path) and item.startswith("CowrieShortTerm-"):
            daily_connect_path = os.path.join(item_path, "daily_connect.json")

            if os.path.exists(daily_connect_path):
                try:
                    with open(daily_connect_path, "r") as f:
                        data = json.load(f)
                        ssh_attempts_by_date = data.get("ssh_attempts_by_date", {})
                        total_days += len(ssh_attempts_by_date)
                        threshold_exceeded_days += sum(1 for count in ssh_attempts_by_date.values() if count > threshold)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error processing {daily_connect_path}: {e}")
                    continue
            else:
                print(f"{daily_connect_path} not found.")

    return threshold_exceeded_days ,total_days

threshold = 100
directory_path = "../logs/"

threshold_exceeded_days, total_days = calculate_operation_stats(directory_path, threshold)

if threshold_exceeded_days is not None and total_days is not None:
    ratio = (threshold_exceeded_days / total_days) * 100 if total_days > 0 else 0.0
    print(f"閾値({threshold})を超えた稼働日数: {threshold_exceeded_days}")
    print(f"総稼働日数: {total_days}")
    print(f"閾値({threshold})を超えた稼働日数の割合: {ratio:.2f}%")
else:
    print("ファイルが見つかりませんでした。")
