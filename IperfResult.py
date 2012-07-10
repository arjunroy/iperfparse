#!/usr/bin/python

'''
Simple script for parsing Iperf CSV output files.
TODO: Requires more testing.
'''

def convertToEpoch(timestr):
    if len(timestr) != 14:
        return None
    year = int(timestr[0:4])
    month = int(timestr[4:6])
    day = int(timestr[6:8])
    hour = int(timestr[8:10])
    minute = int(timestr[10:12])
    seconds = int(timestr[12:14])

    epoch = int(time.mktime((year, month, day, hour, minute, seconds, 0, 0, -1)))
    return epoch

class IperfResult:
    def __init__(self, resultfile):
        try:
            self.readResults(resultfile)
            self.valid = True
        except:
            self.valid = False

    def readResults(self, resultfile):
        fd = open(resultfile)
        lines = fd.readlines()
        fd.close()

        firstLine = lines[0]
        lastLine = lines[len(lines) - 1]
        splits = firstLine.split(",")
        lastSplits = lastLine.split(",")

        # First get src and dst IP and port
        self.srcip = splits[1]
        self.srcport = splits[2]
        self.dstip = splits[3]
        self.dstport = splits[4]

        # Also get the start time and end time
        self.startTime = convertToEpoch(splits[0])
        self.endTime = convertToEpoch(lastSplits[0])

        self.perThreadData = {}
        for line in lines:
            splits = line.split(",")
            time = convertToEpoch(splits[0])
            threadId = int(splits[5])
            bytesInPeriod = int(splits[7])
            bpsInPeriod = int(splits[8])

            period = splits[6]
            periodSplit = period.split("-")
            periodStart = float(periodSplit[0])
            periodEnd = float(periodSplit[1])
            periodDelta = int(periodEnd - periodStart)
            # We skip the aggregate lines at end
            # And in particular, we only want stats for a given period
            # We don't explicitly check that the period + start time
            # lines up with the current timestamp, we just trust it is right.
            if periodDelta > 1:
                continue

            if threadId not in self.perThreadData:
                self.perThreadData[threadId] = []
            self.perThreadData[threadId].append((time, bytesInPeriod, bpsInPeriod))
        # If more than one thread defined, we must have thread -1 referring
        # to aggregate of all data, else we have an error.
        if len(self.perThreadData.keys()) > 1 and -1 not in self.perThreadData:
            raise "Error: Multiple threads but no aggregate data."

    def getBytesTotal(self, startTime, endTime):
        if startTime > endTime:
            raise "Start time > End Time!"
        # Two cases: only one thread defined,
        # or multiple threads defined including thread -1,
        # and any other case is error that has already been caught.
        bytesTotal = 0
        keys = self.perThreadData.keys()
        if len(keys) == 1:
            for record in self.perThreadData[keys[0]]:
                if record[0] >= startTime and record[0] <= endTime:
                    bytesTotal += record[1]
        else:
            for record in self.perThreadData[-1]:
                if record[0] >= startTime and record[0] <= endTime:
                    print "Adding time %d bytes %d" % (record[0], record[1])
                    bytesTotal += record[1]

        print "retval %d" % bytesTotal
        return bytesTotal

