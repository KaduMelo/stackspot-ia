#!/usr/bin/expect -f

set mesage [lindex $argv 0]

set timeout 100
spawn stk ai
expect ">>>"
sleep 0.5
send "$mesage \r"
sleep 0.5
send "\x1b\x0d"
expect "LANIF"

interact