"""
This is the core logic of unattended script generators.

Copyright 2011-2012 (C) Alexey Eromenko "Technologov". All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY Alexey Eromenko "Technologov" ''AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of Alexey Eromenko "Technologov".
"""
#
# This file encodes the logic of preparing unattended setup scripts for differennt
# guest OSes, such as Windows (NT5/NT6), and Linux (Red Hat, Debian, SUSE).

import subprocess as sub
import sys
import os
import shutil

#debuglevel: 0=disabled, 1=default, 2=debug, 3=deep debug
debuglevel = 3

if debuglevel > 0:
    if sys.platform == 'win32':
        debugfilename = "C:\TEMP\libunattended-log.txt"
    else:
        debugfilename = "/tmp/libunattended-log.txt"
    try:
        dfile = open(debugfilename, 'wb')
    except:
        dfile = False
        print "WARNING: log file cannot be created !"
    if dfile:
        print "Log file = %s" % str(debugfilename)

def debugmsg(level, message):
    if debuglevel == 0:
        return
    if debuglevel >= level:        
        print message
        if dfile:
            #In python 2.6, print with redirections always uses UNIX line-ending,
            # so I must add os-neutral line-endings.
            print >> dfile, message,
            dfile.write(os.linesep)
            dfile.flush()

# Windows logic
def prepareWinNT5script(template_filename, target_filename, password='123456', ProductKey = "12345-12345-12345-12345-12345"):
    debugmsg(2, "prepareWinNT5script(template_filename = %s, target_filename = %s, password = %s, ProductKey = %s)" % (template_filename, target_filename, password, ProductKey))
    # read file template_script_NT5
    scriptTemplateFile=open(template_filename)
    scriptLines=scriptTemplateFile.readlines()
    final_script=""
    for line in scriptLines:
        #print 'line = ', line,
        if line.startswith('AdminPassword ='):
            final_script += 'AdminPassword = %s' % str(password) +'\r\n'
        elif line.startswith('ProductKey ='):
            final_script += 'ProductKey = "%s"' % str(ProductKey) +'\r\n'
        else:
            final_script += line        
    scriptTargetFile=open(target_filename, 'wb')
    print >> scriptTargetFile, final_script,
    scriptTargetFile.write('\r\n')  #Use DOS file-endings.
    scriptTargetFile.flush()

def prepareWinNT6script(template_filename, target_filename, user, password, ProductKey, arch):
    debugmsg(2, "prepareWinNT6script(template_filename = %s, target_filename = %s, user = %s, password = %s, ProductKey = %s)" % (template_filename, target_filename, user, password, ProductKey))  
    # arch can be "x86" or "x64"
    # read file template_script_NT6
    scriptTemplateFile=open(template_filename)
    scriptLines=scriptTemplateFile.read()
    final_script = scriptLines
    final_script = final_script.replace('$password', str(password))
    final_script = final_script.replace('$ProductKey', str(ProductKey))
    final_script = final_script.replace('$user', str(user))
    final_script = final_script.replace('processorArchitecture="x86"', 'processorArchitecture="%s"' % str(arch))    
    scriptTargetFile=open(target_filename, 'wb')
    print >> scriptTargetFile, final_script,
    scriptTargetFile.flush()

# End of Windows logic

# Debian logic
def prepareDebianScript(template_filename, target_filename, user, password, arch):
    debugmsg(2, "prepareDebianScript(template_filename = %s, target_filename = %s, user = %s, password = %s, arch = %s)" % (template_filename, target_filename, user, password, arch))
    # This function prepares Debian's preseed script.
    # arch can be "x86" or "x64"
    scriptTemplateFile=open(template_filename)
    scriptLines=scriptTemplateFile.read()
    final_script = scriptLines
    final_script = final_script.replace('$user', '%s' % str(user))
    final_script = final_script.replace('$password', '%s' % str(password))
    scriptTargetFile=open(target_filename, 'wb')
    print >> scriptTargetFile, final_script,
    scriptTargetFile.flush()

def prepareDebianIsolinuxScript(template_filename, target_filename, arch):
    debugmsg(2, "prepareDebianIsolinuxScript(template_filename = %s, target_filename = %s, arch = %s)" % (template_filename, target_filename, arch))
    # arch can be "x86" or "x64"
    scriptTemplateFile=open(template_filename)
    scriptLines=scriptTemplateFile.read()
    final_script = scriptLines
    if arch is "x86":
        deb_arch = "386"
    elif arch is "x64":
        deb_arch = "amd"
    else:
        print "FATAL: unable to determine CPU architecture (%s)" % arch
        exit()
    final_script = final_script.replace('$arch', '%s' % str(deb_arch))
    scriptTargetFile=open(target_filename, 'wb')
    print >> scriptTargetFile, final_script,
    scriptTargetFile.flush()
    
def extractFromDebianISO(cdfile, target_path, VBoxGuestAdditionsISO = ""):
    debugmsg(2, "extractFromDebianISO(cdfile = '%s', target_path = '%s')" % (cdfile, target_path))
    # note that 'isolinux/' directory must be removed, else Anaconda tries to read from there and fails.
    p = sub.Popen('cd %s && rm -Rvf * && 7z x %s install.386/ install.amd/ isolinux/' % (target_path, cdfile), shell=True)
    p.communicate()
    extractGuestAdditionsFromISO(cdfile, target_path, VBoxGuestAdditionsISO)

def prepareUnattendedDebianCD(cdfile, sourcepath):
    debugmsg(2, "prepareDebianUnattendedCD(cdfile = '%s', sourcepath = '%s')" % (cdfile, sourcepath))
    if not os.path.exists(os.path.dirname(cdfile)):
        os.makedirs(os.path.dirname(cdfile))
    p = sub.Popen('cd %s && genisoimage -o %s -r -b isolinux/isolinux.bin  -c isolinux/boot.cat -no-emul-boot -boot-load-size 4  -boot-info-table -R -J -v -T .' % (sourcepath, cdfile), shell=True)
    p.communicate()
# End of Debian logic

# Red Hat logic
def prepareELscript(template_filename, target_filename, osSubType, user='myuser', password='123456'):
    # This function prepares Red Hat Enterprise Linux kickstart script
    debugmsg(2, "prepareELscript()")
    scriptTemplateFile=open(template_filename)
    scriptLines=scriptTemplateFile.read()
    scriptTemplateFile.close()
    final_script = scriptLines

    # prepares encrypted user passwords for Linux guests
    import crypt
    import random, string
    def getsalt(chars = string.letters + string.digits):
        # generate a random 2-character 'salt'
        return random.choice(chars) + random.choice(chars)
    userpasswd_encrypted = crypt.crypt(password, getsalt())
    debugmsg(3, "userpasswd_encrypted = %s" % str(userpasswd_encrypted))
    
    #RHEL3/4 - remove "key". Old Anaconda kickstart do not support it.
    if osSubType.__contains__('EL3') or osSubType.__contains__('EL4'):
        final_script = final_script.replace('key --skip', '#key --skip')
    #RHEL3 - remove "--log".
    if osSubType.__contains__('EL3'):
        final_script = final_script.replace('%post --log=/root/ks-post.log', '%post')
    #RHEL3 - needs "kernel-source", else VBoxAdditions fail to install.
    if not osSubType.__contains__('EL3'):
        final_script = final_script.replace('kernel-source', '#kernel-source')
    #RHEL6 dropped 'langsupport' and 'mouse' kickstart parameters; It auto-detects them.
    if osSubType.__contains__('EL6'):
        final_script = final_script.replace('langsupport --default en_US', '##')
        final_script = final_script.replace('mouse generic3ps/2', '##')
        final_script = final_script.replace('xconfig --resolution=800x600', '##')
        final_script = final_script.replace('%packages --resolvedeps', '%packages')        
    final_script = final_script.replace('rootpw $password', 'rootpw %s' % password)
    final_script = final_script.replace('adduser $user', 'adduser %s' % user)
    final_script = final_script.replace('usermod -p $userpassword_encrypted $user', 'usermod -p %s %s' % (userpasswd_encrypted, user))
    final_script = final_script.replace('usermod -a -G vboxsf $user', 'usermod -a -G vboxsf %s' % user)
    
    scriptTargetFile=open(target_filename, 'wb')
    print >> scriptTargetFile, final_script,
    scriptTargetFile.flush()
    scriptTargetFile.close()

def extractFromRedHatISO(cdfile, target_path, VBoxGuestAdditionsISO = ""):
    # cd target-path/ && 7z e /path/to/Red-hat-like.iso isolinux/ && rm -Rvf isolinux/
    debugmsg(2, "extractFromRedHatISO(cdfile = '%s', target_path = '%s')" % (cdfile, target_path))
    # note that 'isolinux/' directory must be removed, else Anaconda tries to read from there and fails.
    p = sub.Popen('cd %s && rm -Rvf * && 7z e %s isolinux/ && rm -Rvf isolinux/' % (target_path, cdfile), shell=True)
    p.communicate()
    extractGuestAdditionsFromISO(cdfile, target_path, VBoxGuestAdditionsISO)

def prepareUnattendedRedHatCD(cdfile, sourcepath):
    debugmsg(2, "prepareUnattendedCD(cdfile = '%s', sourcepath = '%s')" % (cdfile, sourcepath))
    if not os.path.exists(os.path.dirname(cdfile)):
        os.makedirs(os.path.dirname(cdfile))
    p = sub.Popen('cd %s && genisoimage -o %s -r -b isolinux.bin  -c boot.cat -no-emul-boot -boot-load-size 4  -boot-info-table -R -J -v -T .' % (sourcepath, cdfile), shell=True)
    p.communicate()

# End of Red Hat logic

# SUSE logic
def prepareSuseScript(template_filename, target_filename, user, password):
    debugmsg(2, "prepareSuseScript(template_filename = %s, target_filename = %s, user = %s, password = %s)" % (template_filename, target_filename, user, password))
    scriptTemplateFile=open(template_filename)
    scriptLines=scriptTemplateFile.read()
    final_script = scriptLines
    final_script = final_script.replace('$user', '%s' % str(user))
    final_script = final_script.replace('$password', '%s' % str(password))
    scriptTargetFile=open(target_filename, 'wb')
    print >> scriptTargetFile, final_script,
    scriptTargetFile.flush()

def prepareSuseIsolinuxScript(template_filename, target_filename, arch):
    debugmsg(2, "prepareSuseIsolinuxScript(template_filename = %s, target_filename = %s, arch = %s)" % (template_filename, target_filename, arch))
    # arch can be "x86" or "x64"
    scriptTemplateFile=open(template_filename)
    scriptLines=scriptTemplateFile.read()
    final_script = scriptLines
    if arch is "x86":
        SUSEarch = "i386"
    elif arch is "x64":
        SUSEarch = "amd64"
    else:
        print "FATAL: unable to determine CPU architecture (%s)" % arch
        exit()
    final_script = final_script.replace('$arch', '%s' % str(SUSEarch))
    scriptTargetFile=open(target_filename, 'wb')
    print >> scriptTargetFile, final_script,
    scriptTargetFile.flush()
    
def extractFromSuseISO(cdfile, target_path, VBoxGuestAdditionsISO, arch):
    debugmsg(2, "extractFromSuseISO(cdfile = '%s', target_path = '%s')" % (cdfile, target_path))
    if arch is "x86":
        SUSEarch = "i386"
    elif arch is "x64":
        SUSEarch = "amd64"
    else:
        print "FATAL: unable to determine CPU architecture (%s)" % arch
        exit()
    p = sub.Popen('cd %s && rm -Rvf * && 7z e %s \
      boot/%s/loader/initrd \
      boot/%s/loader/linux \
      boot/%s/loader/isolinux.bin \
       ' % (target_path, cdfile, SUSEarch, SUSEarch, SUSEarch), shell=True)
    p.communicate()
    # SUSE Linux does not provide "boot.cat" as a file, so we must extract it:
    p = sub.Popen('geteltorito -o %s/boot.cat %s' % (target_path, cdfile), shell=True)
    p.communicate()
    extractGuestAdditionsFromISO(cdfile, target_path, VBoxGuestAdditionsISO)

def prepareUnattendedSuseCD(cdfile, sourcepath):
    debugmsg(2, "prepareUnattendedSuseCD(cdfile = '%s', sourcepath = '%s')" % (cdfile, sourcepath))
    if not os.path.exists(os.path.dirname(cdfile)):
        os.makedirs(os.path.dirname(cdfile))
    p = sub.Popen('cd %s && genisoimage -o %s -r -b isolinux.bin  -c boot.cat -no-emul-boot -boot-load-size 4  -boot-info-table -R -J -v -T .' % (sourcepath, cdfile), shell=True)
    p.communicate()
# End of SUSE logic

# Generic Logic
def prepareFormattedFloppy(floppyfile):
    debugmsg(2, "prepareFormattedFloppy(floppyfile = %s)" % floppyfile)
    floppydir = os.path.dirname(floppyfile)
    if not os.path.exists(floppydir):
        os.makedirs(floppydir)
    p = sub.Popen('dd if=/dev/zero of=%s count=1440 bs=1024' % floppyfile, shell=True)
    p.communicate()
    p = sub.Popen('/sbin/mkfs.msdos %s' % floppyfile, shell=True)
    p.communicate()

def prepareUnattendedFloppy(floppyfile, file1, file2=""):
    # This function copies up to 2 files to the floppy image (usually NT5+NT6 scripts)
    debugmsg(2, "prepareUnattendedFloppy(floppyfile = %s, file1 = %s, file2 = %s)" % (floppyfile, file1, file2))
    p = sub.Popen('mcopy -i %s %s %s ::' % (floppyfile, file1, file2), shell=True)
    p.communicate()

def extractGuestAdditionsFromISO(cdfile, target_path, VBoxGuestAdditionsISO = ""):
    # Ability to skip GuestAdditions step
    if VBoxGuestAdditionsISO:
      p = sub.Popen('cd %s && 7z e %s VBoxLinuxAdditions.run' % (target_path, VBoxGuestAdditionsISO), shell=True)
      p.communicate()

def ProcessAllGuests(CDROM1, CDROM2, VBoxGuestAdditionsISO, Floppy, GuestOsType, GuestOsSubType, user, password, productKey, arch):  
    # This is the main function, that determines guest OS, prepares 
    # scripts, and packages them into images accordingly.
    #
    # parameters:
    # CDROM1 = path to original CDROM with operating-system (read-only)
    # CDROM2 = path to our custom, on-the-fly-generated CDROM (writable, bootable)
    # VBoxGuestAdditionsISO = path to Guest Additions.ISO
    # Floppy = path to to our custom, on-the-fly-generated floppy with scripts (writable, non-bootable)
    # GuestOsType = See "vboxunattended.py" for options
    # GuestOsSubType = See "vboxunattended.py" for options
    # user = username of the primary user created in guest OS
    # password = password of both the primary user and of root/Administrator in guest OS
    # productKey = CD-key (currently used only for Windows guests)
    # arch = processor architecture; Can be: "x86" (for 32-bit) or "x64" (for 64-bit)
    
    if GuestOsType == 'Windows':
        winNT5_Target_File='/tmp/winnt.sif'
        winNT6_Target_File='/tmp/autounattend.xml'
        prepareFormattedFloppy(Floppy)
        prepareWinNT5script("win_nt5_template_winnt.sif", winNT5_Target_File, password, productKey)
        prepareWinNT6script("win_nt6_template_autounattend.xml", winNT6_Target_File, user, password, productKey, arch)
        prepareUnattendedFloppy(Floppy, winNT5_Target_File, winNT6_Target_File)
        
    elif GuestOsType is "DebianLinux":
        prepareFormattedFloppy(Floppy)
        extractFromDebianISO(CDROM1, '/tmp/bootiso/', VBoxGuestAdditionsISO)
        prepareDebianScript('linux_debian_template_preseed.cfg', '/tmp/bootiso/preseed.cfg', user, password, arch)
        prepareDebianIsolinuxScript('linux_debian_template_isolinux.cfg', '/tmp/bootiso/isolinux/isolinux.cfg', arch)
        prepareUnattendedDebianCD(CDROM2, '/tmp/bootiso/')
        prepareUnattendedFloppy(Floppy, '/tmp/bootiso/preseed.cfg')

    elif GuestOsType is "SuseLinux":
        extractFromSuseISO(CDROM1, '/tmp/bootiso/', VBoxGuestAdditionsISO, arch)
        prepareSuseScript('linux_suse_template_autoinst.xml', '/tmp/bootiso/autoinst.xml', user, password)
        prepareSuseIsolinuxScript('linux_suse_template_isolinux.cfg', '/tmp/bootiso/isolinux.cfg', arch)
        prepareUnattendedSuseCD(CDROM2, '/tmp/bootiso/')

    elif GuestOsType is "RedHatLinux":
        extractFromRedHatISO(CDROM1, '/tmp/bootiso/', VBoxGuestAdditionsISO)
        prepareELscript('linux_rhel_template_ks.cfg', '/tmp/bootiso/ks.cfg', GuestOsSubType, user, password)
        shutil.copy('linux_rhel_template_isolinux.cfg', '/tmp/bootiso/isolinux.cfg')
        prepareUnattendedRedHatCD(CDROM2, '/tmp/bootiso/')
        
    else:
        print "FATAL: Non-supported OS family (%s)." % str(GuestOsType)
        exit()

def PreProcessLinuxGuests(VMpath, GuestOsType):
    # Pre-processing of all Linux guests:
    if not os.path.exists('%s/isolinux/' % VMpath):
        os.makedirs('%s/isolinux/' % VMpath)
    if GuestOsType.__contains__("Linux"):
        if not os.path.exists('/tmp/bootiso/'):
            os.makedirs('/tmp/bootiso/')
        if GuestOsType is "DebianLinux":
            CDROM2 = VMpath +'/debian_boot.iso'
        elif GuestOsType is "SuseLinux":
            CDROM2 = VMpath +'/suse_boot.iso'
        elif GuestOsType is "RedHatLinux":
            CDROM2 = VMpath +'/redhat_boot.iso'
        debugmsg(2, "CDROM2 path = %s" % CDROM2)        
        return CDROM2
    else:
        return ""
    

# End of Generic Logic
