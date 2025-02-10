import matplotlib.pyplot as plt
import os
import json

def get_dates_counts_from_path(path):
    with open(path) as f:
        data = json.load(f)

    dates = list(data['ssh_attempts_by_date'].keys())
    counts = list(data['ssh_attempts_by_date'].values())

    dates = [date[8:] for date in dates]
    return dates, counts


longterm_dates, longterm_counts = get_dates_counts_from_path('../logs/COWRIE_BASE/daily_connect.json')
randomssh_dates, randomssh_counts = get_dates_counts_from_path('../logs/COWRIE_RANDOM_SSH/daily_connect.json')

dates = [ i for i in range(1, len(longterm_dates) + 1)]
plt.rcParams.update({'font.size': 20})
plt.figure(figsize=(11, 7))

plt.plot(dates, longterm_counts, marker='o', label="LongTerm", color='blue')
plt.plot(dates, randomssh_counts, marker='o', label="RandomSSH", color='orange')

plt.xlabel('Date')
plt.ylabel('Counts')
plt.yscale('log')
plt.xticks(rotation=90)
plt.tight_layout()
plt.legend()

plt.grid(True)
fig_path = os.getenv('FIG_PATH', '../figs/')
if not os.path.exists(fig_path):
    os.makedirs(fig_path)
plt.savefig(fig_path + 'random_ssh.png')

