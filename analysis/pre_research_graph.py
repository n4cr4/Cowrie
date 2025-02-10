import matplotlib.pyplot as plt
import os
import json

dates = [i for i in range(1, 15)]

counts = [183, 472, 6132, 11284, 489, 97, 45, 52, 48, 51, 49, 53, 46, 50]

for i in range(1, len(counts)):
    counts[i] += counts[i - 1]

plt.rcParams.update({'font.size': 20})
plt.figure(figsize=(11, 7))

plt.plot(dates, counts, marker='o', label="SingleInstance", color='blue')

plt.xlabel('Date')
plt.ylabel('Counts')
plt.xticks(rotation=90)
plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
plt.tight_layout()
plt.legend()

plt.grid(True)
fig_path = os.getenv('FIG_PATH', '../figs/')
if not os.path.exists(fig_path):
    os.makedirs(fig_path)
plt.savefig(fig_path + 'base_connection.png')

