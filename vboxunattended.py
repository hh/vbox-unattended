#!/usr/bin/env python
#
# Copyright (c) 2011-2012 Alexey Eromenko "Technologov"

import libvboxunattended

if __name__ == '__main__':
    print "VirtualBox Unattended (version %s)" % str(libvboxunattended.__version__)
    print 'Copyright (c) 2011-2012 Alexey Eromenko "Technologov"'
    print

    libvboxunattended.LibVBoxUnattended(
      VMname = 'Unattended_Debian_VM01',
      Memory = 512, 
      Hard_Disk_SizeGB = 32, 
      CDROM1='[path-to-my-CD.iso]',
      #CDROM1='/D/OSes2/debian-6.0.0-amd64-DVD-1of8.iso',
      user='myuser',
      # password is the same for 'user' and 'root'/Administrator
      password='123456q',
      productKey='[my-cd-key]', # for Windows guests only !
      # GuestOsType - Can be 'Windows' or 'DebianLinux' or 'SuseLinux' or 'RedHatLinux' guest OS
      GuestOsType='DebianLinux', 
      # GuestOsSubType is used for better customization for guests;
      # GuestOsSubType can be: 'EL3', 'EL4', 'EL5', 'EL6', corresponding to RHEL versions;
      # 'EL' - stands for 'Enterprise Linux' - usually Red Hat Enterprise Linux,
      # but can be from community (CentOS) or Oracle.
      # (currently applies only to RedHat guests; otherwise ignored)
      GuestOsSubType='EL5',
      # arch can be "x86" or "x64" (for 32-bit or 64-bit PC, correspondingly)
      # it is translated accordingly to each guest OS; Example: i386 and amd64 for Debian.
      # It is relevant only for NT6, SUSE and Debian; Ignored on RedHat and NT5 backends.
      arch='x64',
      VBoxGuestAdditionsISO = "/opt/VirtualBox/additions/VBoxGuestAdditions.iso"
      )
