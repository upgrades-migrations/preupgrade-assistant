#version=DEVEL
# Firewall configuration
firewall --enabled --port=22:tcp
# X Window System configuration information
xconfig  --startxonboot
# Install OS instead of upgrade
install
# Use network installation
# Root password
# System authorization information
auth --enableshadow --enablemd5
# System language
lang en_US.UTF-8
# SELinux configuration
selinux --enforcing
# Installation logging level
logging --level=info

# System timezone
timezone --isUtc Europe/Prague
# Network information
network  --bootproto=dhcp --device=eth0 --onboot=on
# System bootloader configuration
bootloader --append="rhgb quiet" --driveorder="vda"

%include /tmp/part-include


%packages

%end
