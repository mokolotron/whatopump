import csv

with open('quote_btc.txt') as file:
    # s = file.readline()
    # if s[-1] == ',':
    #     s = s[:-1]
    reader = csv.reader(file)
    for row in reader:
        print(row)

