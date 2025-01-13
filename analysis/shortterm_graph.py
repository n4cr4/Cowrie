import matplotlib.pyplot as plt
import os
import json
import glob

def get_dates_counts_from_path(path):
    with open(path) as f:
        data = json.load(f)

    dates = list(data['ssh_attempts_by_date'].keys())
    counts = list(data['ssh_attempts_by_date'].values())

    dates = [date[8:] for date in dates]
    return dates, counts

def get_shortterm_dirs():
    return glob.glob('../logs/CowrieShortTerm-*')

longterm_dates, longterm_counts = get_dates_counts_from_path('../logs/COWRIE_BASE/daily_connect.json')

plt.rcParams.update({'font.size': 20})
plt.figure(figsize=(11, 7))

plt.plot(longterm_dates, longterm_counts, marker='o', label="LongTerm", color='blue')

num = 1
for shortterm_dir in get_shortterm_dirs():
    shortterm_dates, shortterm_counts = get_dates_counts_from_path(shortterm_dir + '/daily_connect.json')
    # plt.plot(shortterm_dates, shortterm_counts, marker='o', label=f"ShortTerm{num}")
    plt.plot(shortterm_dates, shortterm_counts, marker='o')
    num += 1

plt.xlabel('Date')
plt.ylabel('Counts')
plt.xticks(rotation=90)
plt.tight_layout()
plt.legend()

plt.grid(True)
fig_path = os.getenv('FIG_PATH', '../figs/')
if not os.path.exists(fig_path):
    os.makedirs(fig_path)
plt.savefig(fig_path + 'short_term.png')

