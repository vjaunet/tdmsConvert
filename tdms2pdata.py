#!/opt/miniconda3/bin/python
#
#
#           Convertisseur NI tdms file to lib_pressdata binary format
#
#     ** npTdms must be installed :
#                  https://nptdms.readthedocs.io/en/latest/index.html
#     ** npTdms comes with a handy "tdmsinfo" command line program
#
#  author   : vincent jaunet
#  date     : 01/03/2019
#  comments : first version
#=========================================================================

import sys, getopt


def main(argv):
    #=====================================================
    # option parser
    #====================================================

    inputfile = ''
    outputfile = ''
    verbose = False
    calibConv = False

    try:
        opts, args = getopt.getopt(argv,"hi:o:c:v",["help","ifile=","ofile="])
    except getopt.GetoptError:
        print('tdms2pdata.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('tdms2pdata.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
            outputfile = inputfile[:-5]
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-c","--calib"):
            calibfile = arg
            calibConv = True
        elif opt == "-v":
            verbose = True

    if verbose :
        print('Input file is "', inputfile,'"')
        if calibConv :
            print('Calib file is "', calibfile,'"')


    #=====================================================
    # main
    #====================================================
    from nptdms import TdmsFile
    from array import array
    import numpy as np
    import struct

    tdms_file = TdmsFile(inputfile)
    tdmsFileGroups= tdms_file.groups()

    if verbose :
        print('Available groups are :')
        print(tdmsFileGroups)

    #for all groups in the tdmsfile
    igrp = 0
    for group in tdmsFileGroups:
        groupChans = tdms_file.group_channels(group)

        nsamples= len(groupChans[0].data)
        nchan = len(groupChans)
        samplingFreq = int(1.0/groupChans[0].property('wf_increment'))

        #handling the calibration
        if calibConv :
            kMic = np.genfromtxt(calibfile,usecols=0)

        ichan = 0
        dataTot = np.zeros((len(groupChans), nsamples),dtype='f')

        #for all aquisition channels
        for chan in groupChans:
            if calibConv :
                dataTot[ichan][:] = chan.data/kMic[ichan]
            else :
                dataTot[ichan][:] = chan.data
            ichan = ichan+1

        #===============================================
        # data conversion to pressData format
        # assumes that all channels have same length
        #===============================================
        if len(tdmsFileGroups) > 1:
            if verbose :
                print('Output file is "',outputfile+'_gp'+str(igrp)+'.bin','"')
            ofile=open(outputfile+'_gp'+str(igrp)+'.bin',"wb")
        else :
            if verbose :
                print('Output file is "',outputfile+'.bin','"')
            ofile=open(outputfile+'.bin',"wb")

        #Header ==============================================
        ofile.write(b'v0.1')
        ofile.write(bytearray(struct.pack("i", nchan)))
        ofile.write(bytearray(struct.pack("i", nsamples)))
        ofile.write(bytearray(struct.pack("f", samplingFreq)))
        ofile.write(bytearray(struct.pack("f", 1.0)))
        for x in range(500):
            ofile.write(b'x')
        for x in range(nchan*2):
            ofile.write(bytearray(struct.pack("f", 0.0)))
        #Header ==============================================
        dataTot.astype('f').tofile(ofile)
        ofile.close()
        igrp=igrp+1

if __name__ == "__main__":
    main(sys.argv[1:])
