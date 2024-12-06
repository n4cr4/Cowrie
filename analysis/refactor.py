import pandas as pd
import json
from typing import Optional, Callable
import argparse


def logs_loaded_required(func: Callable):
    """ログが読み込まれていることを確認するデコレーター"""

    def wrapper(self, *args, **kwargs):
        if self.logs is None:
            print("ログが読み込まれていません。")
            return None
        return func(self, *args, **kwargs)

    return wrapper


class CowrieLogAnalyzer:
    def __init__(self, logfile: str = "cowrie.json"):
        """初期化メソッド"""
        self.logfile = logfile
        self.logs: Optional[pd.DataFrame] = None

    def load_logs(self):
        """ログファイルを読み込んでDataFrameとして保持"""
        try:
            self.logs = pd.read_json(self.logfile)
            print(f"ログファイル '{self.logfile}' を正常に読み込みました。")
        except json.JSONDecodeError as e:
            print(f"JSONデコードエラー: {e}")
            self.logs = None
        except FileNotFoundError:
            print(f"指定されたファイルが見つかりません: {self.logfile}")
            self.logs = None
        except Exception as e:
            print(f"予期しないエラーが発生しました: {e}")
            self.logs = None

    def parse_timestamp(self, timestamp: str) -> str:
        """タイムスタンプを'yyyy-mm-dd' 形式に変換"""
        try:
            return timestamp.split("T")[0]
        except Exception as e:
            print(f"タイムスタンプの変換に失敗しました: {e}")
            return ""

    @logs_loaded_required
    def analyze_event_stats(self) -> Optional[dict]:
        """イベントごとの件数を集計"""
        try:
            event_counts = self.logs["eventid"].value_counts().to_dict()
            return {"events": event_counts}
        except KeyError:
            print("ログに 'eventid' カラムが見つかりません。")
            return None

    @logs_loaded_required
    def analyze_ip_stats(self) -> Optional[dict]:
        """IPごとの接続回数を集計"""
        try:
            ssh_logs = self.logs[self.logs["eventid"] == "cowrie.session.connect"]
            ip_counts = ssh_logs['src_ip'].value_counts().to_dict()
            return {"ips": ip_counts}
        except KeyError:
            print("ログに 'src_ip' カラムが見つかりません。")
            return None

    @logs_loaded_required
    def analyze_command_failed(self) -> Optional[dict]:
        """実行に失敗したコマンドを集計"""
        try:
            failed_commands = self.logs[self.logs["eventid"] == "cowrie.command.failed"]
            failed_inputs = failed_commands["input"].value_counts().to_dict()
            return {"command_failed": failed_inputs}
        except KeyError:
            print("ログに 'failed' カラムが見つかりません。")
            return None

    @logs_loaded_required
    def analyze_dowload_hash(self) -> Optional[dict]:
        """ダウンロードファイルのハッシュ値を集計"""
        try:
            download_logs = self.logs[self.logs["eventid"].isin(['cowrie.session.file_download', 'cowrie.session.file_upload'])]
            download_hash_counts = download_logs["shasum"].value_counts().to_dict()
            return {"download files": download_hash_counts}
        except KeyError:
            print("ログに 'file_download', 'file_upload' カラムが見つかりません。")
            return None

    @logs_loaded_required
    def analyze_daily_connect(self) -> Optional[dict]:
        """日付別のSSH接続試行回数を集計"""
        try:
            ssh_logs = self.logs[self.logs['eventid'] == 'cowrie.session.connect'].copy()
            ssh_logs['date'] = pd.to_datetime(ssh_logs['timestamp']).dt.strftime('%Y-%m-%d')

            daily_connect_counts = ssh_logs['date'].value_counts().sort_index()
            daily_connect_stats = {
                "ssh_attempts_by_date": daily_connect_counts.to_dict()
            }
        except KeyError:
            print("ログに 'connect' カラムが見つかりません。")
            return None
        return daily_connect_stats


    def save_to_json(self, data: dict, output_file: str):
        """データをJSON形式で保存"""
        try:
            with open(output_file, "w") as f:
                json.dump(data, f, indent=4)
            print(f"データを '{output_file}' に保存しました。")
        except Exception as e:
            print(f"データの保存中にエラーが発生しました: {e}")


# 使用例
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "CowrieログJSONファイルを読み込むスクリプト。\n"
            "ログファイルはあらかじめ `jq -s '.' log.json` などで "
            "正しいJSON形式に整形しておいてください。"
        )
    )
    parser.add_argument(
        "--logfile", 
        type=str, 
        default="cowrie.json", 
        help=(
            "読み込むCowrieログファイルのパス (デフォルト: cowrie.json)。\n"
            "ファイルは1つのJSON配列として整形済みである必要があります。"
        )
    )
    args = parser.parse_args()

    analyzer = CowrieLogAnalyzer(args.logfile)
    analyzer.load_logs()

    # イベント集計
    event_stats = analyzer.analyze_event_stats()
    if event_stats:
        analyzer.save_to_json(event_stats, "event_stats.json")

    # IP集計
    ip_stats = analyzer.analyze_ip_stats()
    if ip_stats:
        analyzer.save_to_json(ip_stats, "ip_stats.json")

    command_failed = analyzer.analyze_command_failed()
    if command_failed:
        analyzer.save_to_json(command_failed, "command_failed.json")

    daily_connect = analyzer.analyze_daily_connect()
    if daily_connect:
        analyzer.save_to_json(daily_connect, "daily_connect.json")

    download_hash = analyzer.analyze_dowload_hash()
    if download_hash:
        analyzer.save_to_json(download_hash, "download_hash.json")
