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
            ip_counts = self.logs["src_ip"].value_counts().to_dict()
            return {"ips": ip_counts}
        except KeyError:
            print("ログに 'src_ip' カラムが見つかりません。")
            return None

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
