#!/usr/bin/ruby
#

cmd = `time $(dd if=/dev/zero of=test bs=1000 count=100000 && sync)`

puts cmd
