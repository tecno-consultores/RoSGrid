# model = RB750Gr3
# serial number = 6C1105XXXXXX
/interface bridge
add admin-mac=48:A9:8A:11:22:33 auto-mac=no comment=defconf name=bridge
/interface list
add comment=defconf name=WAN
add comment=defconf name=LAN
/ip pool
add name=default-dhcp ranges=192.168.88.10-192.168.88.254
/ip dhcp-server
add address-pool=default-dhcp interface=bridge name=defconf
/ip address
add address=192.168.88.1/24 comment=defconf interface=bridge network=192.168.88.0
/ip service
set telnet disabled=no
set ftp disabled=no
set www disabled=no
set ssh disabled=no
set api disabled=no
set winbox disabled=no
