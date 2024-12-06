import json
import glob

# ファイルのパスリストを取得
json_files = glob.glob("./**/vt.json", recursive=True)

merged_data = {}

for file in json_files:
    with open(file, "r") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):  # ファイルが配列形式であることを確認
                for item in data:
                    if isinstance(item, dict) and "id" in item:
                        merged_data[item["id"]] = item
                    else:
                        print(f"Invalid item in file {file}: {item}")
            else:
                print(f"Invalid JSON structure in file {file}: {data}")
        except json.JSONDecodeError as e:
            print(f"Error reading JSON from {file}: {e}")

# 結果を出力（または保存）
with open("vt.json", "w") as out_file:
    json.dump(list(merged_data.values()), out_file, indent=2)
