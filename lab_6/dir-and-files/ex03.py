import os 

path = r'/Users/rasulkerimzhanov/PycharmProjects/PP2_2024Spring/lab_6'
# path.replace('\\', '/')

if os.path.exists(path):
    print('Path exists')
    print('Filename:', os.path.basename(path))
    print('Directory:', os.path.dirname(path))
else:
    print('This path doesn\'t exist')