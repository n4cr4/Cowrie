import matplotlib.pyplot as plt

# データ
dates = ["14", "15", "16", "17", "18", "19", "20"]
longterm_counts = [40, 397, 66, 16875, 91, 56, 112]
shortterm_counts = [25, 37, 13, 151, 84, 103, 23]

plt.rcParams.update({'font.size': 20})

# グラフ作成
plt.figure(figsize=(11, 7))
plt.plot(dates, longterm_counts, marker='o', label="LongTerm", color='blue')
plt.plot(dates, shortterm_counts, marker='o', label="ShortTerm", color='orange')

# グラフの詳細設定
plt.xlabel('Date')
plt.ylabel('Counts')
plt.legend()

# グラフ表示
plt.grid(True)
plt.savefig('res.png')

