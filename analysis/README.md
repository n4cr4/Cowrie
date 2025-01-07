# Cowrie Log Analysis

事前にAWS Step Functionsを実行し、ログが指定のs3バケットにアップロードされていることを確認してください。

## 手順

1. AWSコンソールからシークレットをコピーして環境変数にエクスポートします。

2. `download_s3_logs.py` を実行します。
```bash
python download_s3_logs.py
```

3. `format_logs.sh` を実行してログファイルを整形します。
```bash
./format_logs.sh
```

4. `merge_logs.sh` を実行してログファイルをマージします。
```bash
./merge_logs.sh
```

5. `analyze_logs.sh` を実行してログファイルを分析します。
```bash
./analyze_logs.sh
```

6. VirusTotalを使用するために、環境変数を設定します。
```bash
export API_KEY=your_api_key
```
7. `get_vt_report.sh`を実行してファイル解析を行います。
```bash
./get_vt_report.sh
```
8. `merge_vt_report.sh`を実行して必要な情報を抽出します。
```bash
./merge_vt_report.sh
```
9. `randomssh_graph.py`と`shortterm_graph.py`を使用してグラフを作成します。
```bash
python randomssh_graph.py && python shortterm_graph.py
```
