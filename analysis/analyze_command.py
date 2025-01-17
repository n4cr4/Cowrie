import json
import re
import argparse
from typing import List, Dict, Any
import glob
import yaml
import os

# パスを指定してSigmaルールを取得
def load_sigma_rules(rules_path="./sigma/rules/**/*.yml"):
    rules = []
    for rule_file in glob.glob(rules_path, recursive=True):
        try:
            with open(rule_file, 'r', encoding='utf-8') as file:
                rule = yaml.safe_load(file)
                rules.append(rule)
        except Exception as e:
            print(f"Error reading {rule_file}: {e}")
    return rules

# Sigmaルール内の文字列をエスケープする
def _escape_string(pattern):
    return re.escape(pattern)

# modifiersを考慮して正規表現を作成する
def _convert_string_with_modifiers_to_regex(pattern, modifiers=[]):
    regex = _escape_string(pattern)
    if 'contains' in modifiers:
        regex = f".*{regex}.*"
    if 'startswith' in modifiers:
        regex = f"^{regex}.*"
    if 'endswith' in modifiers:
        regex = f".*{regex}$"
    return regex

# ルールから正規表現を生成し、辞書形式で返す関数
def generate_regex_patterns(rules):
    regex_patterns = {}
    for rule in rules:
        try:
            logsource = rule.get("logsource", {})
            product = logsource.get("product", None)
            if product != "linux":
                continue # logsource.productがlinux以外はスキップ

            title = rule.get("title", "No Title")
            description = rule.get("description", None)
            detection = rule.get("detection", {})

            if (title, description) not in regex_patterns:
                regex_patterns[(title, description)] = []

            for key, value in detection.items(): # key は selection or condition
                if key == "condition":
                    continue # conditionはスキップ
                if isinstance(value, dict):
                    for field, patterns in value.items(): # field は CommandLine or User or ...
                        if field == "type":
                            continue
                        if isinstance(patterns, list): # or string
                            for pattern_obj in patterns:
                                if isinstance(pattern_obj, str):
                                    regex = _escape_string(pattern_obj)
                                    regex_patterns[(title, description)].append({
                                        "field": field,
                                        "match": regex,
                                        "not": False
                                    })
                                elif isinstance(pattern_obj, dict):
                                    for modifier_type, target_pattern in pattern_obj.items():
                                        if isinstance(target_pattern, str):
                                            if modifier_type == "not":
                                                regex = _escape_string(target_pattern)
                                                regex_patterns[(title, description)].append({
                                                    "field": field,
                                                    "match": regex,
                                                    "not": True
                                                })
                                            else:
                                                modifiers = [modifier_type]
                                                regex = _convert_string_with_modifiers_to_regex(target_pattern, modifiers)
                                                regex_patterns[(title, description)].append({
                                                    "field": field,
                                                    "match": regex,
                                                    "not": False
                                                })
                                        elif isinstance(target_pattern, list):
                                            for tp in target_pattern:
                                                if modifier_type == "not":
                                                    regex = _escape_string(tp)
                                                    regex_patterns[(title, description)].append({
                                                        "field": field,
                                                        "match": regex,
                                                        "not": True
                                                    })
                                                else:
                                                    modifiers = [modifier_type]
                                                    regex = _convert_string_with_modifiers_to_regex(tp, modifiers)
                                                    regex_patterns[(title, description)].append({
                                                        "field": field,
                                                        "match": regex,
                                                        "not": False
                                                    })
                        elif isinstance(patterns, str):
                            regex = _escape_string(patterns)
                            regex_patterns[(title, description)].append({
                                "field": field,
                                "match": regex,
                                "not": False
                            })
                elif isinstance(value, str):
                  regex = _escape_string(value)
                  regex_patterns[(title, description)].append({
                      "field": key,
                      "match": regex,
                      "not": False
                  })
        except Exception as e:
            print(f"Error processing rule '{title}': {e}")

    formatted_regex_patterns = []
    for (title, description), patterns in regex_patterns.items():
      formatted_regex_patterns.append({
          "title": title,
          "description": description,
          "patterns": patterns
      })
    return formatted_regex_patterns

def analyze_log_with_sigma(log_file: str, regex_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    指定されたログファイルを読み込み、Sigmaルールで生成した正規表現パターンと照合してラベル付けを行います。

    Args:
        log_file (str): 解析対象のログファイルのパス。
        regex_patterns (List[Dict[str, Any]]): Sigmaルールから生成された正規表現パターン。

    Returns:
        Dict[str, Any]: 解析結果。各コマンドの `input` をキーとし、マッチしたルールを `rules` リストに格納した辞書。
    """
    analyzed_commands = {}
    try:
        with open(log_file, 'r') as f:
            data = json.load(f)
            for command in data.get('commands', []):
                input_text = command.get('input', '')
                matches = []
                for rule in regex_patterns:
                    title = rule.get("title")
                    description = rule.get("description")
                    for pattern in rule.get("patterns", []):
                      regex = pattern.get("match", "")
                      field = pattern.get("field", "")
                      not_flag = pattern.get("not", False)

                      if not_flag:
                        if not re.search(regex, input_text):
                           matches.append({
                               "title": title,
                               "description": description,
                               "field": field,
                               "match": regex,
                                "not": True,
                            })
                      elif re.search(regex, input_text):
                          matches.append({
                              "title": title,
                              "description": description,
                              "field": field,
                              "match": regex,
                              "not": False,
                          })

                if matches:
                   analyzed_commands[input_text] = {
                        "rules": [{
                                "title": match["title"],
                                "description": match["description"],
                                "field": match["field"],
                                "match": match["match"],
                                "not": match["not"],
                            }
                             for match in matches
                            ]
                    }
                else:
                   analyzed_commands[input_text] = {"rules": []}
    except Exception as e:
        print(f"Error processing {log_file}: {e}")
    return analyzed_commands

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze log file with Sigma rules.')
    parser.add_argument('--logfile', type=str, required=True, help='Path to the log file')
    args = parser.parse_args()

    sigma_rules = load_sigma_rules()
    print(f"Loaded {len(sigma_rules)} Sigma rules")

    regex_patterns = generate_regex_patterns(sigma_rules)
    print(f"Generated {len(regex_patterns)} regex patterns")

    analyzed_data = analyze_log_with_sigma(args.logfile, regex_patterns)

    # 出力先のファイルパスを決定
    log_dir = os.path.dirname(args.logfile)
    output_file = os.path.join(log_dir, "command_analysis.json")

    # 解析結果をJSONファイルに保存
    with open(output_file, 'w') as f:
        json.dump(analyzed_data, f, indent=4)

    print(f"Analysis results saved to {output_file}")
