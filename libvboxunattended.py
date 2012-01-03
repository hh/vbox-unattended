#!/usr/bin/env python
#
# Copyright (c) 2011-2012 Alexey Eromenko "Technologov"
#
# License: GPLv2-or-later at your option as published by the Free Software Foundation.
# http://www.gnu.org/licenses/gpl-2.0.html
# Dependencies: mtools, VBox 4.1, ...
# Parser generators and core logic (libunattended) goes via 2clause-BSD license,
# VBox and GUI logic goes GPL.

"""
# Basic VirtualBox initialization commands: (provided as example)

from vboxapi import VirtualBoxManager
mgr = VirtualBoxManager(None, None)
vbox = mgr.vbox
session = mgr.mgr.getSessionObject(vbox)
constants = mgr.constants

name = "my VM name"
mach = vbox.findMachine(name)

progress = mach.launchVMProcess(session, "gui", "")
progress.waitForCompletion(-1)

console=session.console
"""

from vboxapi import VirtualBoxManager
import subprocess as sub
import libunattended
import sys
import os

#debuglevel: 0=disabled, 1=default, 2=debug, 3=deep debug
debuglevel = 3

if debuglevel > 0:
    if sys.platform == 'win32':
        debugfilename = "C:\TEMP\\vboxunattended-log.txt"
    else:
        debugfilename = "/tmp/vboxunattended-log.txt"
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

__version__ = "0.5.1"

class LibVBoxUnattended():
    def __init__(self, VMname, Memory, Hard_Disk_SizeGB, CDROM1, user, password, productKey, GuestOsType, GuestOsSubType, arch, VBoxGuestAdditionsISO):
        debugmsg(2, "class LibVBoxUnattended::__init__(VMname = %s, Memory = %s, Hard_Disk_SizeGB = %s, CDROM1 = %s, user = %s, password = %s, productKey = %s, GuestOsType = %s, GuestOsSubType = %s, arch = %s, VBoxGuestAdditionsISO = %s)" % (VMname, str(Memory), str(Hard_Disk_SizeGB), CDROM1, user, password, productKey, GuestOsType, GuestOsSubType, arch, VBoxGuestAdditionsISO))
        # General settings:
        self.VMname = str(VMname)
        self.Memory = int(Memory)
        self.Hard_Disk_SizeGB = int(Hard_Disk_SizeGB)
        self.VBoxGuestAdditionsISO=VBoxGuestAdditionsISO
        self.GuestOsType=GuestOsType
        self.GuestOsSubType=GuestOsSubType
        # Unattended-specific settings:
        self.user=user
        self.password=password
        self.productKey=productKey
        self.arch=arch
        # preparations:
        self.prepareVBoxAPI()
        self.CDROM1=CDROM1
        self.CDROM2 = libunattended.PreProcessLinuxGuests(self.VMpath, GuestOsType)
        self.Floppy = self.VMpath + os.sep + "floppy_script.img"
        if self.GuestOsType == 'RedHatLinux' or self.GuestOsType == 'SuseLinux':
            # Red Hat and SUSE Linux guest don't need floppy.
            self.Floppy = ""
        else:
            debugmsg(2, "floppy path = %s" % self.Floppy)
        libunattended.ProcessAllGuests(
          CDROM1=self.CDROM1,
          CDROM2=self.CDROM2,
          VBoxGuestAdditionsISO=VBoxGuestAdditionsISO,
          Floppy=self.Floppy,
          GuestOsType=GuestOsType,
          GuestOsSubType=GuestOsSubType,
          user=user,
          password=password,
          productKey=productKey,
          arch=arch
          )
        self.PostProcessLinuxGuests()
        self.prepareVM()
        self.startVM()

    def PostProcessLinuxGuests(self):
        debugmsg(2, "LibVBoxUnattended::PostProcessLinuxGuests()")
        # Post-processing of all Linux guests:
        if self.GuestOsType.__contains__("Linux"):
            # for Linux guests, we swap CD-ROMs.
            # CDROM1 is the original disc with OS (read-only), but we don't want to boot from it;
            # we want to boot from our custom-made image CDROM2, while the CD with OS becomes data CD,
            # and goes into CDROM 2.
            # VirtualBox does not support booting from CDROM2, so we must swap.
            self.CDROM3 = self.CDROM1
            self.CDROM1 = self.CDROM2.replace('\ ',' ')
            self.CDROM2 = self.CDROM3
            debugmsg(2, "CDROM1 path = %s" % self.CDROM1)
            debugmsg(2, "CDROM2 path = %s" % self.CDROM2)

    def prepareVBoxAPI(self):
        debugmsg(2, "LibVBoxUnattended::prepareVBoxAPI()")
        self.mgr = VirtualBoxManager(None, None)
        self.vbox = self.mgr.vbox
        self.session = self.mgr.mgr.getSessionObject(self.vbox)
        self.constants = self.mgr.constants
        self.VMpath = os.path.dirname(self.vbox.composeMachineFilename(self.VMname,''))
        if not sys.platform == 'win32':
            self.VMpath = self.VMpath.replace(" ", "\ ")  # work with spaces in folder and file names
        print "VMpath = %s" % self.VMpath

    def prepareVM(self):
        debugmsg(2, "LibVBoxUnattended::prepareVM()")
        #self.mach = self.vbox.createMachine(self.VMname, self.VMname, "", "", False)
        debugmsg(3, "LibVBoxUnattended::prepareVM() - creating machine.")
        self.mach = self.vbox.createMachine("", self.VMname, "", "", True)
        self.vbox.registerMachine(self.mach)
        self.mach.lockMachine(self.session, 1)
        
        #Creating mutable object "mach2", for changing machine's basic settings:
        mach2 = self.session.machine
        debugmsg(3, "LibVBoxUnattended::prepareVM() - setting Memory.")
        mach2.memorySize = self.Memory
        mach2.saveSettings()
        # Create IDE controller + HDD image
        debugmsg(3, "LibVBoxUnattended::prepareVM() - adding IDE Controller.")
        strctl = mach2.addStorageController("IDE Controller", self.constants.StorageBus_IDE)
        mach2.saveSettings()
        #klaus recommends: IVirtualBox::composeMachineFilename()
        path = os.path.dirname(mach2.settingsFilePath) + os.sep + self.VMname + ".vdi"
        #p = sub.Popen('rm -vf %s' % path.replace(' ','\ '), shell=True)
        #p.communicate()
        #if not sys.platform == 'win32':
        #    path = path.replace(" ", "\ ")  # work with spaces in folder and file names
        debugmsg(3, "LibVBoxUnattended::prepareVM() - creating Hard Disk.")
        debugmsg(3, "path = %s" % path)
        mediumHDD = self.vbox.createHardDisk("vdi", path)
        progress = mediumHDD.createBaseStorage(1024*1024*1024*self.Hard_Disk_SizeGB,
            self.constants.MediumVariant_Standard)
        progress.waitForCompletion(-1)
        print "progress = ", progress.percent
        
        if int(progress.percent) == 100 and mediumHDD:
            debugmsg(3, "LibVBoxUnattended::prepareVM() - Hard Disk created.")
        else:
            debugmsg(3, "LibVBoxUnattended::prepareVM() - failed to create HDD...")
            exit()
            
        debugmsg(3, "LibVBoxUnattended::prepareVM() - adding Hard Disk to VM.")
        mach2.attachDevice("IDE Controller", 0, 0, self.constants.DeviceType_HardDisk, mediumHDD)
        mach2.saveSettings()
        # now we must attach 2x CD-ROMS -or- CDx2 + floppy.
        debugmsg(3, "LibVBoxUnattended::prepareVM() - adding CDROM1 added to VM.")
        mediumCD1=self.vbox.openMedium(self.CDROM1, self.constants.DeviceType_DVD, self.constants.AccessMode_ReadOnly, 0)
        mach2.attachDevice("IDE Controller", 1, 0, self.constants.DeviceType_DVD, mediumCD1)
        
        if self.GuestOsType.__contains__('Linux') and self.CDROM2:
            # CDROM1 = custom-made (bootable), CDROM2 = original OS (non-bootable)
            debugmsg(3, "LibVBoxUnattended::prepareVM() - adding CDROM2 added to VM.")
            mediumCD2=self.vbox.openMedium(self.CDROM2, self.constants.DeviceType_DVD, self.constants.AccessMode_ReadOnly, 0)
            mach2.attachDevice("IDE Controller", 1, 1, self.constants.DeviceType_DVD, mediumCD2)
        elif self.GuestOsType is 'Windows':
            # CDROM1 = original OS (bootable), CDROM2 = Guest Additions (non-bootable)
            debugmsg(3, "LibVBoxUnattended::prepareVM() - adding CDROM2 added to VM.")
            mediumCD2=self.vbox.openMedium(self.VBoxGuestAdditionsISO, self.constants.DeviceType_DVD, self.constants.AccessMode_ReadOnly, 0)
            mach2.attachDevice("IDE Controller", 1, 1, self.constants.DeviceType_DVD, mediumCD2)
        
        # attach floppy (needed for all guests, except Red Hat Linux)
        if self.Floppy:
            strctlFloppy = mach2.addStorageController("Floppy Controller", self.constants.StorageBus_Floppy)
            mediumFloppy= self.vbox.openMedium(self.Floppy.replace('\ ',' '), self.constants.DeviceType_Floppy, 
                self.constants.AccessMode_ReadOnly, 0)
            mach2.attachDevice("Floppy Controller", 0, 0, self.constants.DeviceType_Floppy, mediumFloppy)        
        
        # boot order: HDD->CD-ROM->Floppy (first number = boot priority)
        # second number = device. devices: 1 = floppy, 2 = CD, 3 = HDD, 4 = Network (PXE)
        mach2.setBootOrder(1, 3)
        mach2.setBootOrder(2, 2)
        mach2.setBootOrder(3, 1)
        self.networkConfigVM(mach2)
        mach2.saveSettings()
        self.session.unlockMachine()

    def networkConfigVM(self, machine):
        netadp = machine.getNetworkAdapter(0)
        netadp.adapterType = 3 # 1 / 2 = "AMD PCnet-II / III", 3 = Intel PRO/1000 MT Desktop, 6 = VirtIO
        netadp.enabled=True
        netadp.cableConnected=True
        netadp.attachmentType=self.constants.NetworkAttachmentType_NAT        

    def startVM(self):
        debugmsg(2, "LibVBoxUnattended::startVM()")
        progress = self.mach.launchVMProcess(self.session, "gui", "")
        progress.waitForCompletion(-1)
        self.console=self.session.console
