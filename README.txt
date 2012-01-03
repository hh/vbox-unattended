-----------------------------------------------------------
Design Goals:
-----------------------------------------------------------
The system should:
1. run on any host OS supported by VirtualBox, (avoid host-OS-specific tricks)
2. be simple to implement, 
3. be offline (i.e. not require an Internet connection), 
4. be fast (i.e. generate only minimal remastered boot CD image, rather than whole OS CD image)
5. support both Windows guests and several major Linux guest families (Debian, Red Hat, SUSE).
6. be Open-Source
-----------------------------------------------------------

This version supports Linux hosts, Windows guests and Red Hat Linux guests.

Dependencies:
python (obviously) :)
VirtualBox 4.1.x
7z (7-zip) - used to extract data from ISOs.
mtools - used to copy data to floppy images.

Tested on Debian 6.0 host. 
(Tested guests: RHEL3/4/5 32-bit, WinXP/Vista 32-bit, Debian6, openSUSE 11.4 32-bit)

How to use:
1. edit vboxunattended.py - last 10 lines - this will configure your stuff.
2. run it:
$ python ./vboxunattended.py

Release Notes:
-for each run, you must change VM name inside "vboxunattended.py" - in last 10 lines.
-working from physical CD-ROM is not supported. (only with ISO images)
-RHEL6 and Fedora guest OS support are broken.

License: core logic under BSD, VBox logic under GPL.

Sister projects:
- Oz
http://clalance.blogspot.com/2011/02/oz-version-010.html
http://aeolusproject.org/oz-download.html
Chris Lalancette <clalance@redhat.com>

==============================================



# custom scripts; Step is done in d-i after installed all packages, but before guest OS reboot:
d-i preseed/late_command string \
mv /target/etc/rc.local /target/etc/rc.local.backup; \
echo false >/target/etc/X11/default-display-manager; \

# Generating "rc.local" file, which will act as first-boot script, after reboot:
cat >> /target/etc/rc.local <<EOF \
#!/bin/bash
mkdir /mnt/cdrom
echo
echo "Installing VirtualBox Guest Additions..."
mount -t iso9660 -o ro /dev/cdrom1 /mnt/cdrom
bash /mnt/cdrom/VBoxLinuxAdditions.run
eject /dev/cdrom1
usermod -a -G vboxsf $user
echo "/usr/bin/kdm" >/etc/X11/default-display-manager
#mv /etc/rc.local.backup /etc/rc.local
/usr/bin/kdm
exit 0
EOF
