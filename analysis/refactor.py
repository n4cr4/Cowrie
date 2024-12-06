import pandas as pd
import json
from typing import Optional, Callable
import argparse


def logs_loaded_required(func: Callable):
    """Decorator to ensure that logs are loaded"""
    def wrapper(self, *args, **kwargs):
        if self.logs is None:
            print("Logs are not loaded.")
            return None
        return func(self, *args, **kwargs)

    return wrapper

def save_to_json(data: dict, output_file: str):
    """Save data to a JSON file"""
    try:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to '{output_file}'.")
    except Exception as e:
        print(f"Error occurred while saving data: {e}")


class CowrieLogAnalyzer:
    def __init__(self, logfile: str = "cowrie.json"):
        """Initialize with the log file path"""
        self.logfile = logfile
        self.logs: Optional[pd.DataFrame] = None

    def load_logs(self):
        """Load log file into a DataFrame"""
        try:
            self.logs = pd.read_json(self.logfile)
            print(f"Log file '{self.logfile}' loaded successfully.")
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            self.logs = None
        except FileNotFoundError:
            print(f"File '{self.logfile}' not found.")
            self.logs = None
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            self.logs = None

    def parse_timestamp(self, timestamp: str) -> str:
        """Convert timestamp to 'yyyy-mm-dd' format"""
        try:
            return timestamp.split("T")[0]
        except Exception as e:
            print(f"Failed to convert timestamp: {e}")
            return ""

    @logs_loaded_required
    def analyze_event_stats(self) -> Optional[dict]:
        """Aggregate event counts and extract specific event data"""
        try:
            event_counts = self.logs["eventid"].value_counts().to_dict()

            terminal_info = []
            if "cowrie.client.size" in event_counts:
                client_size_logs = self.logs[self.logs["eventid"] == "cowrie.client.size"]
                terminal_info = client_size_logs[["session", "width", "height", "src_ip"]].fillna("Unknown").to_dict(orient="records")

            return {
                "events": event_counts,
                **({"terminal_info": terminal_info} if terminal_info else {})
            }
        except Exception as e:
            print(f"Error occurred while analyzing event stats: {e}")
            return None

    @logs_loaded_required
    def analyze_ip_stats(self) -> Optional[dict]:
        """Aggregate connection attempts by IP"""
        try:
            ssh_logs = self.logs[self.logs["eventid"] == "cowrie.session.connect"]
            ip_counts = ssh_logs['src_ip'].value_counts().to_dict()
            return {"ips": ip_counts}
        except Exception as e:
            print(f"Error occurred while analyzing IP stats: {e}")
            return None

    @logs_loaded_required
    def analyze_client_version(self) -> Optional[dict]:
        """Aggregate client version counts"""
        try:
            version_logs = self.logs[self.logs["eventid"] == "cowrie.client.version"]
            version_counts = version_logs["version"].value_counts().to_dict()
            return {"client_versions": version_counts}
        except Exception as e:
            print(f"Error occurred while analyzing client versions: {e}")
            return None

    @logs_loaded_required
    def analyze_command_failed(self) -> Optional[dict]:
        """Aggregate failed commands"""
        try:
            failed_commands = self.logs[self.logs["eventid"] == "cowrie.command.failed"]
            failed_inputs = failed_commands["input"].value_counts().to_dict()
            return {"command_failed": failed_inputs}
        except Exception as e:
            print(f"Error occurred while analyzing failed commands: {e}")
            return None

    @logs_loaded_required
    def analyze_dowload_hash(self) -> Optional[dict]:
        """Aggregate download file hashes"""
        try:
            download_logs = self.logs[self.logs["eventid"].isin(['cowrie.session.file_download', 'cowrie.session.file_upload'])]
            download_hash_counts = download_logs["shasum"].value_counts().to_dict()
            return {"download_files": download_hash_counts}
        except Exception as e:
            print(f"Error occurred while analyzing download hashes: {e}")
            return None

    @logs_loaded_required
    def analyze_daily_connect(self) -> Optional[dict]:
        """Aggregate SSH connection attempts by date"""
        try:
            ssh_logs = self.logs[self.logs['eventid'] == 'cowrie.session.connect'].copy()
            ssh_logs['date'] = pd.to_datetime(ssh_logs['timestamp']).dt.strftime('%Y-%m-%d')

            daily_connect_counts = ssh_logs['date'].value_counts().sort_index()
            daily_connect_stats = {
                "ssh_attempts_by_date": daily_connect_counts.to_dict()
            }
        except Exception as e:
            print(f"Error occurred while analyzing daily connections: {e}")
            return None
        return daily_connect_stats

    @logs_loaded_required
    def analyze_uniq_command(self) -> Optional[dict]:
        """Aggregate unique commands executed"""
        try:
            command_logs = self.logs[self.logs['eventid'] == "cowrie.command.input"]
            command_uniq_df = command_logs.groupby('input')['session'].agg(list).reset_index()
            command_uniq = {
                "commands": command_uniq_df.to_dict(orient="records")
            }
        except Exception as e:
            print(f"Error occurred while analyzing unique commands: {e}")
            return None
        return command_uniq

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Cowrie log JSON file reader.\n"
            "Ensure the log file is formatted correctly using 'jq -s '.' log.json'."
        )
    )
    parser.add_argument(
        "--logfile", 
        type=str, 
        default="cowrie.json", 
        help=(
            "Path to the Cowrie log file (default: cowrie.json).\n"
            "The file should be a single JSON array."
        )
    )
    args = parser.parse_args()

    analyzer = CowrieLogAnalyzer(args.logfile)
    analyzer.load_logs()

    # Event stats aggregation
    event_stats = analyzer.analyze_event_stats()
    if event_stats:
        save_to_json(event_stats, "event_stats.json")

    # IP stats aggregation
    ip_stats = analyzer.analyze_ip_stats()
    if ip_stats:
        save_to_json(ip_stats, "ip_stats.json")

    # Command failed aggregation
    command_failed = analyzer.analyze_command_failed()
    if command_failed:
        save_to_json(command_failed, "command_failed.json")

    # Daily connection aggregation
    daily_connect = analyzer.analyze_daily_connect()
    if daily_connect:
        save_to_json(daily_connect, "daily_connect.json")

    # Download hash aggregation
    download_hash = analyzer.analyze_dowload_hash()
    if download_hash:
        save_to_json(download_hash, "download_hash.json")

    # Unique command aggregation
    command_uniq = analyzer.analyze_uniq_command()
    if command_uniq:
        save_to_json(command_uniq, "command_uniq.json")

    # Client version aggregation
    client_version = analyzer.analyze_client_version()
    if client_version:
        save_to_json(client_version, "client_version.json")
