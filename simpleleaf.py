# -*- coding: utf-8 -*-
"""
    Leafee OpenClose notification receiver program
"""

from bluepy.btle import Peripheral
import bluepy.btle as btle
import binascii
import sys
import sqlite3
import os

# Leafee address
LEAFEE_ADDR = ("xx:xx:xx:xx:xx:xx", "xx:xx:xx:xx:xx:xx");
LeafeeId = 0;
LeafeeAddr = "";
Options = [];

# Call Back at notification
class LeafeeDelegate(btle.DefaultDelegate):
    def __init__(self, params):
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data): 
        isclose = int(binascii.b2a_hex(data))

        global LeafeeId
        insertdb(LeafeeId, isclose)


# sensor 
class SensorLeaf(Peripheral):
    def __init__(self, addr):
        Peripheral.__init__(self, addr, "public")

# db insert 
# method : 0 = notification, 1 = read in startup, 2 = read by heartbeat
def insertdb(devid, isclose, method = 0):

    global Options
    data= (str(devid),str(isclose),str(method))

    # dbname = "/var/www/data/sqlite"
    dbpath = "/tmp/sqlite"
    dbname = "sensor.db"
    dbtable = "lf_log_table"

    if not os.path.exists(dbpath):
        os.makedirs(dbpath)

    # check options
    if ('save' in Options and 'sqlite' in Options):
        # connect sqlite: this creates new db, if not exists
        conn = sqlite3.connect(dbpath + '/' + dbname)
        c = conn.cursor()
 
        # check the target table exists or not 
        checkdb = conn.execute("SELECT * FROM sqlite_master WHERE type='table' and name='%s'" % dbtable)
        # create new table if not exists
        if checkdb.fetchone() == None:
            create_table = 'CREATE TABLE ' + dbtable + '(id INTEGER PRIMARY KEY AUTOINCREMENT, devid INTEGER, isclose INTEGER, method INTEGER DEFAULT 0, created TEXT DEFAULT CURRENT_TIMESTAMP)'
            c.execute(create_table)
            conn.commit()
 
        # insert into data 
        sql = "INSERT INTO " + dbtable + " (devid,isclose,method) VALUES (?,?,?)"
        c.execute(sql, data)
        conn.commit()
 
        # disconnect
        conn.close()

    if ('print' in Options or 'debug' in Options):
        print "[DEVICE : " + data[0] + "][isClose : " + data[1] + "][isStartup : " + data[2] + "]" 


def main(args):

    if (len(args) < 3):
        sys.exit(1)

    # args[1] = BLE MAC address 
    # args[2] = device index 
    # args[3] = print option

    global LeafeeAddr
    global LeafeeId
    LeafeeAddr = args[1]
    LeafeeId = args[2]

    global Options
    Options = args;

    # initialize 
    leaf = SensorLeaf(LeafeeAddr)

    # delegate
    leaf.setDelegate(LeafeeDelegate(btle.DefaultDelegate))

    # read the current status
    data = leaf.readCharacteristic(0x002a)
    isclose = int(binascii.b2a_hex(data))
    insertdb(LeafeeId, isclose, 1)

    # start notification 
    leaf.writeCharacteristic(0x002b, "\x01\x00", True)

    # start receiving 
    while True:
        leaf.waitForNotifications(1.0)

        """
        if leaf.waitForNotifications(1.0):
            continue
        print "wait..."
        """

if __name__ == "__main__":
    main(sys.argv)
