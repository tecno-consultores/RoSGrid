# RoSGrid Golden Baseline v1.0.0 (Tampered)
/interface bridge
add name=bridge-lan
/ip address
add address=10.250.3.8/24 interface=ether1 network=10.250.3.0
/ip service
set telnet disabled=no
set ftp disabled=yes
set www disabled=yes
set ssh address=0.0.0.0/0 disabled=no
set api disabled=no
set winbox address=0.0.0.0/0 disabled=no
/system logging action
add name=rosgridsyslog remote=10.250.3.1 remote-port=5514 target=remote
/system logging
add action=rosgridsyslog topics=info,warning,error,critical
