#!/usr/bin/python

import subprocess

out_put = subprocess.check_output("time $(dd if=/dev/zero of=test001 bs=1000 count=100000 && sync)",
                                   shell=True)

print out_put
