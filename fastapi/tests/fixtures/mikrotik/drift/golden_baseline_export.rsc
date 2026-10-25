# RoSGrid Golden Baseline v1.0.0
# Network Role = CORE / DISTRIBUTION
/interface bridge
add name=bridge-lan
/ip address
add address=10.250.3.8/24 interface=ether1 network=10.250.3.0
/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=yes
set ssh address=10.250.0.0/16 disabled=no
set api disabled=yes
set winbox address=10.250.0.0/16 disabled=no
/system logging action
add name=rosgridsyslog remote=10.250.3.1 remote-port=5514 target=remote
/system logging
add action=rosgridsyslog topics=info,warning,error,critical
