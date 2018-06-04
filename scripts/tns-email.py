#!/usr/bin/python
import sys

with open('/root/email-log/email-log.txt', 'a') as f:
    for line in sys.stdin:
        if 'https://wis-tns.weizmann.ac.il/object' in line:
            f.write(line[1:(line[1:].index('*') + 2)] + '\n')
