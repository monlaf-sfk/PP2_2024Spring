import os

path = r'/Users/rasulkerimzhanov/PycharmProjects/PP2_2024Spring/lab_6/dir-and-files/ex04.txt'

with open(path, 'r') as f:
    lines = f.readlines()
    print('Number of lines in {}: {}'.format(os.path.basename(path), len(lines)))