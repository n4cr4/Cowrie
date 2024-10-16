import glob
import json
from collections import defaultdict
from datetime import datetime

def parse_timestamp(timestamp):
    """タイムスタンプをdatetimeオブジェクトに変換する"""
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ") if timestamp else None


def handle_event_type(event_type, log_entry, events_by_type):
    """イベントタイプを集計"""
    if event_type:
        events_by_type[event_type] += 1

def handle_ssh_attempt(event_type, log_entry, ssh_attempts_by_date, session_start_times, session_src_ips):
    """SSH接続試行の処理"""
    if event_type == "cowrie.session.connect":
        timestamp = log_entry.get("timestamp")
        log_date = parse_timestamp(timestamp).strftime("%Y-%m-%d") if timestamp else None

        session_id = log_entry.get("session")

        if log_date:
            ssh_attempts_by_date[log_date] += 1

        if session_id and timestamp:
            session_start_times[session_id] = parse_timestamp(timestamp)
            session_src_ips[session_id] = log_entry.get("src_ip", "不明")

def handle_login_attempt(event_type, log_entry, actual_login_attempts_by_date):
    """ログイン試行の処理"""
    if event_type in ("cowrie.login.success", "cowrie.login.failed"):
        timestamp = log_entry.get("timestamp")
        log_date = parse_timestamp(timestamp).strftime("%Y-%m-%d") if timestamp else None
        if log_date:
            actual_login_attempts_by_date[log_date] += 1


def handle_failed_command(event_type, log_entry, failed_commands):
    """失敗したコマンドの処理"""
    if event_type == "cowrie.command.failed":
        command = log_entry.get("input")
        if command:
            failed_commands[command] += 1

def handle_command_input(event_type, log_entry, commands_per_session):
    """コマンド入力の処理"""
    if event_type == "cowrie.command.input":
        session_id = log_entry.get("session")
        if session_id:
            commands_per_session[session_id] += 1

def handle_session_closed(event_type, log_entry, session_start_times, commands_per_session, no_command_sessions, session_durations, session_src_ips):
    """セッション終了時の処理"""
    if event_type == "cowrie.session.closed":
        session_id = log_entry.get("session")
        timestamp = log_entry.get("timestamp")

        if session_id and commands_per_session[session_id] == 0:
            no_command_sessions[0] += 1

        if session_id in session_start_times and timestamp:
            start_time = session_start_times[session_id]
            end_time = parse_timestamp(timestamp)
            duration = (end_time - start_time).total_seconds() if start_time and end_time else 0

            session_durations[session_id] = {
                "duration": duration,
                "commands": commands_per_session[session_id],
                "src_ip": session_src_ips.get(session_id, "不明"),
            }

def handle_manual_connection(event_type, log_entry, session_src_ips, terminal_info):
    """仮想端末情報の処理"""
    event_type = log_entry.get("eventid")
    session_id = log_entry.get("session")
    
    if event_type == "cowrie.client.size":
        width = log_entry.get("width")
        height = log_entry.get("height")

        terminal_info[session_id] = {
        "width": width,
        "height": height,
        "src_ip": session_src_ips.get(session_id, "不明")
        }


def analyze_cowrie_logs(log_file):
    """Cowrieログファイルを解析し、集計を行う"""
    events_by_type = defaultdict(int)
    ssh_attempts_by_date = defaultdict(int)
    actual_login_attempts_by_date = defaultdict(int)
    failed_commands = defaultdict(int)
    commands_per_session = defaultdict(int)
    session_start_times = {}

    session_durations = {}
    terminal_info = {}

    session_src_ips = {}
    no_command_sessions = [0]

    with open(log_file, "r") as f:
        for line in f:
            try:
                log_entry = json.loads(line)
                event_type = log_entry.get("eventid")

                handle_event_type(event_type, log_entry, events_by_type)
                handle_ssh_attempt(event_type, log_entry, ssh_attempts_by_date, session_start_times, session_src_ips)
                handle_login_attempt(event_type, log_entry, actual_login_attempts_by_date)
                handle_failed_command(event_type, log_entry, failed_commands)
                handle_command_input(event_type, log_entry, commands_per_session)
                handle_session_closed(event_type, log_entry, session_start_times, commands_per_session, no_command_sessions, session_durations, session_src_ips)
                handle_manual_connection(event_type, log_entry, session_src_ips, terminal_info)

            except json.JSONDecodeError:
                print(f"JSONデコードエラー: {line}")

    return {
        "events_by_type": events_by_type,
        "ssh_attempts_by_date": ssh_attempts_by_date,
        "actual_login_attempts_by_date": actual_login_attempts_by_date,
        "failed_commands": failed_commands,
        "no_command_sessions": no_command_sessions[0],
        "session_durations": session_durations,
        "terminal_info": terminal_info
    }

def aggregate_results(log_file_pattern):
    """複数のログファイルを集計し、結果を返す"""


    analysis_results = {
        "events_by_type": defaultdict(int),
        "ssh_attempts_by_date": defaultdict(int),
        "actual_login_attempts_by_date": defaultdict(int),
        "failed_commands": defaultdict(int),
        "no_command_sessions": 0,  # no_command_sessions は整数で保持
    }

    session_durations = {}
    terminal_info = {}
    input_commands = defaultdict(list)

    for log_file_path in glob.glob(log_file_pattern):

        result = analyze_cowrie_logs(log_file_path)

        for key in analysis_results:

            # 'no_command_sessions' は整数として処理
            if key == "no_command_sessions":
                analysis_results[key] += result[key]
            else:
                for k, v in result[key].items():
                    analysis_results[key][k] += v


        session_durations.update(result["session_durations"])
        terminal_info.update(result["terminal_info"])

        with open(log_file_path, "r") as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    event_type = log_entry.get("eventid")
                    session_id = log_entry.get("session")

                    if event_type == "cowrie.command.input" and session_id:
                        command = log_entry.get("input")
                        if command:
                            input_commands[session_id].append(command)

                except json.JSONDecodeError:
                    print(f"JSONデコードエラー: {line}")

    return analysis_results, session_durations, input_commands, terminal_info

def format_commands(input_commands):
    """input_commandsをコマンドごとにセッションIDを集約した形式に整形"""
    command_to_sessions = defaultdict(lambda: {"sessions": []})

    # input_commandsの各セッションIDごとのコマンドを集計
    for session_id, commands in input_commands.items():
        for command in commands:
            command_to_sessions[command]["sessions"].append(session_id)

    # コマンドごとの識別子を作成（コマンドそのものをキーにしても良い）
    result_commands = {f"command_{i}": {"command": cmd, "sessions": data["sessions"]}
                       for i, (cmd, data) in enumerate(command_to_sessions.items())}
    
    return result_commands

def save_to_json(data, filename):
    """辞書データをJSON形式でファイルに保存"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_to_markdown(analysis_results, session_durations, input_commands, terminal_info, filename):

    """解析結果をMarkdown形式でファイルに保存（表形式とインラインコード使用）"""
    with open(filename, "w") as f:
        # イベントタイプ別の集計
        f.write("# イベントタイプ別の集計\n")

        f.write("| イベントタイプ | 件数 |\n")
        f.write("| ------------- | ---- |\n")
        for event_type, count in analysis_results["events_by_type"].items():
            f.write(f"| {event_type} | {count} 件 |\n")

        # 日付別のSSH接続試行
        f.write("\n# 日付別のSSH接続試行\n")
        f.write("| 日付 | SSH接続試行数 |\n")
        f.write("| ---- | ------------- |\n")
        for date, count in analysis_results["ssh_attempts_by_date"].items():
            f.write(f"| {date} | {count} 件 |\n")

        # 日付別のログイン試行
        f.write("\n# 日付別のログイン試行\n")
        f.write("| 日付 | ログイン試行数 |\n")
        f.write("| ---- | -------------- |\n")
        for date, count in analysis_results["actual_login_attempts_by_date"].items():
            f.write(f"| {date} | {count} 件 |\n")

        # 実行が失敗したコマンド
        f.write("\n# 実行が失敗したコマンド\n")
        f.write("| コマンド | 失敗回数 |\n")
        f.write("| -------- | -------- |\n")
        for command, count in analysis_results["failed_commands"].items():
            f.write(f"| `{command}` | {count} 回 |\n")

        # コマンド実行なしで終了したセッション数
        f.write(f"\n# コマンド実行なしで終了したセッション数\n{analysis_results['no_command_sessions']} 件\n")

        # 仮想端末情報
        f.write("# 仮想端末情報\n\n")
        f.write("| セッションID | 幅 (Width) | 高さ (Height) | 接続元IP (src_ip) |\n")
        f.write("| ------------ | --------- | ------------ | ---------------- |\n")

        # `terminal_info`の内容を表として出力
        for session_id, info in terminal_info.items():
            width = info.get("width", "不明")
            height = info.get("height", "不明")
            src_ip = info.get("src_ip", "不明")
            
            # 各行のデータをMarkdown形式で書き込む
            f.write(f"| {session_id} | {width} | {height} | {src_ip} |\n")

        # コマンド実行セッションの接続時間
        command_sessions_durations = [

            details["duration"] for details in session_durations.values() if details["commands"] > 0
        ]
        if command_sessions_durations:
            avg_duration = sum(command_sessions_durations) / len(command_sessions_durations)
            min_duration = min(command_sessions_durations)
            max_duration = max(command_sessions_durations)

            f.write("\n# コマンド実行セッションの接続時間\n")
            f.write(f"- **平均**: {avg_duration:.2f} 秒\n")
            f.write(f"- **最小**: {min_duration:.2f} 秒\n")
            f.write(f"- **最大**: {max_duration:.2f} 秒\n")

        # 接続時間が長いセッション TOP10
        top_10_sessions = sorted(

            session_durations.items(), key=lambda x: x[1]["duration"], reverse=True
        )[:10]


        if top_10_sessions:
            f.write("\n# 接続時間が長いセッション TOP10\n")
            f.write("| セッションID | 接続時間（秒） | コマンド実行回数 | 入力コマンド | src_ip |\n")
            f.write("| ------------ | -------------- | ---------------- | ----------- | ------- |\n")
            for session_id, details in top_10_sessions:
                duration = details["duration"]
                commands = details["commands"]
                src_ip = details["src_ip"]

                commands_str = ", ".join([f"`{cmd}`" for cmd in input_commands.get(session_id, [])]) or "なし"
                f.write(f"| {session_id} | {duration:.2f} | {commands} | {commands_str} | {src_ip} |\n")
        else:
            f.write("\nコマンド実行セッションはありませんでした。\n")

# メイン処理
log_file_pattern = "../../log/cowrie.json*"
analysis_results, session_durations, input_commands, terminal_info = aggregate_results(log_file_pattern)
save_to_json(format_commands(input_commands), "command.json")
save_to_markdown(analysis_results, session_durations, input_commands, terminal_info, "results.md")


print("command.json and analysis_results.md have been created.")


