# Cowrie Log Analysis

## 手順

1. AWSコンソールからシークレットをコピーして環境変数にエクスポートします。
    ```bash
    export API_KEY=your_api_key
    export HASH_LIST_PATH=your_hash_list_path
    export DOWNLOAD_DIR=your_download_dir
    ```

2. `download_logs.py` を実行します。
    ```bash
    python download_logs.py
    ```

3. `format_logs.sh` を実行してログファイルを整形します。
    ```bash
    ./format_logs.sh
    ```

4. `merge_logs.sh` を実行してログファイルをマージします。
    ```bash
    ./merge_logs.sh
    ```

5. `analysis.py` を実行してログファイルを分析します。
    ```bash
    python analysis.py
    ```
