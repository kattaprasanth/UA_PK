#!/usr/bin/perl
#
#

print "Hello World\n";

my $output = system('time $(dd if=/dev/zero of=test01 bs=1000 count=100000 && sync)');

print $output;
