
import os
import calendar
from tkinter.messagebox import showinfo
import math

class swat_utils():

    def __init__(self):

        self.dummy = "dummy"

    def read_file_cio(self, proj_path):
        """
        This function read in the contents in the
        file.cio and get the required information
        :param proj_path:
        :return: info_file_cio
        """
        path_file_cio = os.path.join(proj_path, "txtinout", "file.cio")
        try:
            with open(path_file_cio, 'r') as swatFile:
                lif = swatFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                folder and make sure you have a complete set".format(path_file_cio, e))
            return
        # Get information needed and store them into dict
        info_file_cio = dict()
        info_file_cio["simtotal"] = int(lif[7].split("|")[0])
        info_file_cio["startyr"] = int(lif[8].split("|")[0])
        start_juline_day = int(lif[9].split("|")[0])
        end_julian_day = int(lif[10].split("|")[0])
        info_file_cio["warmup"] = int(lif[59].split("|")[0])
        info_file_cio["endyear"] = info_file_cio["startyr"] + info_file_cio["simtotal"]

        startmon, startday = self.julianday_to_yymmdd(info_file_cio["startyr"], start_juline_day)
        endmon, endday = self.julianday_to_yymmdd(info_file_cio["endyear"], end_julian_day)
        info_file_cio["startdate"] = "{}/{}/{}".format(startmon, startday, info_file_cio["startyr"])
        info_file_cio["endyear"] = info_file_cio["startyr"] + info_file_cio["simtotal"] - 1
        info_file_cio["enddate"] = "{}/{}/{}".format(endmon, endday, info_file_cio["endyear"])
        iprint = int(lif[58].split("|")[0])

        if iprint == 0:
            info_file_cio["iprint"] = "monthly"
        elif iprint == 1:
            info_file_cio["iprint"] = "daily"
        elif iprint == 2:
            info_file_cio["iprint"] = "annual"

        return info_file_cio


    def julianday_to_yymmdd(self, year, julian_day):
        """
        convert julian day in a year into date
        :param year:
        :param julian_day:
        :return:
        """
        month = 1
        while julian_day - calendar.monthrange(year, month)[1] > 0 and month <= 12:
            julian_day = julian_day - calendar.monthrange(year,month)[1]
            month = month + 1

        return month, julian_day


    # def date_to_julianday(self, year, month, day):
    #     """
    #     convert date of a year into julian day
    #     :param year:
    #     :param month:
    #     :param day:
    #     :return: julianday
    #     """
    #     d0 = date(year, 1, 1)
    #     d1 = date(year, month, day)
    #     delta = d1 - d0
    #     julianday = delta.days + 1
    #
    #     return julianday


    ##########################################################################
    def updateParInSub(self,
                       fnSwatSubLvl,
                       parInFile,
                       proj_path,
                       fdname_running):

        # First readin the contents of the old file
        fnpSwatSub = os.path.join(proj_path,
                                  fdname_running,
                                  "{}.sub".format(fnSwatSubLvl))
        try:
            with open(fnpSwatSub, 'r') as subFile:
                lif = subFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpSwatSub, e))
            return
        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        for lidx in range(len(lif)):
            # Line 26 for parameter CH_S1
            if ((lidx == 25) and ("CH_SI" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CH_SI"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | CH_SI : Average slope of tributary channel [m/m]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CH_SI"]["TestVal"]))

            #  Line 28 for parameter CH_K1
            if ((lidx == 27) and ("CH_KI" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CH_KI"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | CH_KI : Effective hydraulic conductivity in tributary channel [mm/hr]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CH_KI"]["TestVal"]))

            # Line 29 for parameter CH_N1
            if ((lidx == 28) and ("CH_NI" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CH_NI"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | CH_NI : Manning"s "n" value for the tributary channels\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CH_NI"]["TestVal"]))

        # Then write the contents into the same file
        with open(fnpSwatSub, 'w') as subFile:
            subFile.writelines(lif)


    ##########################################################################
    def updateParInRte(self,
                       fnSwatSubLvl,
                       parInFile,
                       proj_path,
                       fdname_running):
        # First readin the contents of the original file in the swattio folder
        fnpSwatRteOrig = os.path.join(proj_path,
                                      "txtinout",
                                      "{}.rte".format(fnSwatSubLvl))
        try:
            with open(fnpSwatRteOrig, 'r', encoding="ISO-8859-1") as rteFileOrig:
                lifOrig = rteFileOrig.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                    folder and make sure you have a complete set".format(fnpSwatRteOrig, e))
            return
        # First readin the contents of the new file in the working folder
        fnpSwatRte = os.path.join(proj_path,
                                  fdname_running,
                                  "{}.rte".format(fnSwatSubLvl))
        try:
            with open(fnpSwatRte, 'r', encoding="ISO-8859-1") as rteFile:
                lif = rteFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                                folder and make sure you have a complete set".format(fnpSwatRte, e))
            return

        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        for lidx in range(len(lif)):
            # Line 4 for parameter CH_SII
            # In the matlab code, the CH_S2 was modified using the following code:
            # (in matlab): CH_S2=str2double(strtok(line))*(1+CH_SII);
            # This means, the script get the current value of slope and time it by percent.
            if ((lidx == 3) and ("CH_SII" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CH_SII"]["selectFlag"]) == 1):
                    # Determine whether this is modified by fraction or absolute value
                    origVal = float(lifOrig[lidx].split("|")[0])
                    newVal = origVal * (1 + float(parInFile.loc[parInFile["Symbol"] == "CH_SII"]["TestVal"]))
                    lif[lidx] = """{:14.3f}    | CH_SII : Main channel slope [m/m]\n""".format(newVal)

            #  Line 6 for parameter CH_NII
            if ((lidx == 5) and ("CH_NII" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CH_NII"]["selectFlag"]) == 1):
                    lif[lidx] = """{:14.3f}    | CH_NII : Manning"s nvalue for main channel\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CH_NII"]["TestVal"]))

            # Line 7 for parameter CH_KII
            if ((lidx == 6) and ("CH_KII" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CH_KII"]["selectFlag"]) == 1):
                    lif[lidx] = """{:14.3f}    | CH_KII : Effective hydraulic conductivity [mm/hr]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CH_KII"]["TestVal"]))

            # Line 8 for parameter CH_COV1
            if ((lidx == 7) and ("CH_COV1" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CH_COV1"]["selectFlag"]) == 1):
                    lif[lidx] = """{:14.3f}    | CH_COV1 : Channel erodibility factor\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CH_COV1"]["TestVal"]))

            # Line 9 for parameter CH_COV2
            if ((lidx == 8) and ("CH_COV2" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CH_COV2"]["selectFlag"]) == 1):
                    lif[lidx] = """{:14.3f}    | CH_COV2 : Channel cover factor\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CH_COV2"]["TestVal"]))

        # Then write the contents into the same file
        with open(fnpSwatRte, 'w', encoding="ISO-8859-1") as rteFile:
            rteFile.writelines(lif)

        return "rte"


    ##########################################################################
    def updateParInSwq(self,
                       fnSwatSubLvl,
                       parInFile,
                       proj_path,
                       fdname_running):
        # First readin the contents of the old file

        fnpSwatSwq = os.path.join(proj_path,
                                  fdname_running,
                                  "{}.swq".format(fnSwatSubLvl))

        try:
            with open(fnpSwatSwq, 'r', encoding="ISO-8859-1") as swqFile:
                lif = swqFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                                folder and make sure you have a complete set".format(fnpSwatSwq, e))
            return

        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        for lidx in range(len(lif)):
            #  Line 3 for parameter CH_NII
            if ((lidx == 2) and ("RS1" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RS1"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | RS1 : Local algal settling rate in the reach at 20 [m/day]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RS1"]["TestVal"]))

            # Line 4 for parameter RS2
            if ((lidx == 3) and ("RS2" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RS2"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | RS2 : Benthic (sediment) source rate for dissolved phosphorus in the reach at 20 [m/day]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RS2"]["TestVal"]))

            # Line 5 for parameter RS3
            if ((lidx == 4) and ("RS3" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RS3"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | RS3 : Benthic source rate for NH4-N in the reach at 20 [mg NH4-N/[m2ay]]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RS3"]["TestVal"]))

            # Line 6 for parameter RS4
            if ((lidx == 5) and ("RS4" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RS4"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | RS4 : Rate coefficient for organic N settling in the reach at 20 [day-1]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RS4"]["TestVal"]))

            # Line 7 for parameter RS5
            if ((lidx == 6) and ("RS5" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RS5"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | RS5 : Organic phosphorus settling rate in the reach at 20 [day-1]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RS5"]["TestVal"]))

            # Line 16 for parameter BC1
            if ((lidx == 15) and ("BC1" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "BC1"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | BC1 : Rate constant for biological oxidation of NH4 to NO2 in the reach at 20C [day-1]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "BC1"]["TestVal"]))

            # Line 17 for parameter BC2
            if ((lidx == 16) and ("BC2" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "BC2"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | BC2 : Rate constant for biological oxidation of NO2 to NO3 in the reach at 20C [day-1]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "BC2"]["TestVal"]))

            # Line 18 for parameter BC3
            if ((lidx == 17) and ("BC3" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "BC3"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | BC3 : Rate constant for hydrolysis of organic N to NH4 in the reach at 20C [day-1]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "BC3"]["TestVal"]))

            # Line 19 for parameter BC4
            if ((lidx == 18) and ("BC4" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "BC4"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | BC4 : Channel cover factor\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "BC4"]["TestVal"]))

        # Then write the contents into the same file
        with open(fnpSwatSwq, 'w', encoding="ISO-8859-1") as swqFile:
            swqFile.writelines(lif)


    ##########################################################################
    def updateParInGw(self,
                      fnSwatHruLvl,
                      parInFile,
                      proj_path,
                      fdname_running):

        # First readin the contents of the old file
        fnpOrig = os.path.join(proj_path,
                               "txtinout",
                               "{}.gw".format(fnSwatHruLvl))
        try:
            with open(fnpOrig, 'r') as swatFileOrig:
                lifOrig = swatFileOrig.readlines()
        except IOError as e:

            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpOrig, e))
            return


        # First readin the contents of the old file
        fnpGW = os.path.join(proj_path,
                           fdname_running,
                           "{}.gw".format(fnSwatHruLvl))

        try:
            with open(fnpGW, 'r') as swatFile:
                lif = swatFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpGW, e))
            return

        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        for lidx in range(len(lif)):
            #  Line 4 for parameter GW_DELAY
            if ((lidx == 3) and ("GW_DELAY" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "GW_DELAY"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | GW_DELAY : Groundwater delay [days]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "GW_DELAY"]["TestVal"]))

            # Line 5 for parameter ALPHA_BF
            if ((lidx == 4) and ("ALPHA_BF" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "ALPHA_BF"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | ALPHA_BF : BAseflow alpha factor [days]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "ALPHA_BF"]["TestVal"]))

            # Line 6 for parameter GWQMN
            if ((lidx == 5) and ("GWQMN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "GWQMN"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | GWQMN : Threshold depth of water in the shallow aquifer required for return flow to occur [mm]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "GWQMN"]["TestVal"]))

            # Line 7 for parameter GW_REVAP
            if ((lidx == 6) and ("GW_REVAP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "GW_REVAP"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | GW_REVAP : Groundwater "revap" coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "GW_REVAP"]["TestVal"]))

            # Line 8 for parameter REVEP_MN
            if ((lidx == 7) and ("REVEP_MN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "REVEP_MN"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | REVEP_MN : Threshold depth of water in the shallow aquifer for "revap" to occur [mm]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "REVEP_MN"]["TestVal"]))

            # Line 9 for parameter RCHRG_DP
            if ((lidx == 8) and ("RCHRG_DP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RCHRG_DP"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | RCHRG_DP : Deep aquifer percolation fraction\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RCHRG_DP"]["TestVal"]))

            # Line 10 for parameter GWHT
            if ((lidx == 9) and ("GWHT" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "GWHT"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | GWHT : Initial groundwater height [m]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "GWHT"]["TestVal"]))

            # Line 11 for parameter GW_SPYLD
            if ((lidx == 10) and ("GW_SPYLD" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "GW_SPYLD"]["selectFlag"]) == 1):
                    # Determine whether this is modified by fraction or absolute value
                    origVal = float(lifOrig[lidx].split("|")[0])
                    newVal = origVal * (1 + float(parInFile.loc[parInFile["Symbol"] == "GW_SPYLD"]["TestVal"]))
                    lif[lidx] = """{:16.3f}    | GW_SPYLD : Specific yield of the shallow aquifer [m3/m3]\n""".format(
                        newVal)

            # Line 12 for parameter SHALLST_N
            if ((lidx == 11) and ("SHALLST_N" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SHALLST_N"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | SHALLST_N : Initial concentration of nitrate in shallow aquifer [mg N/l]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SHALLST_N"]["TestVal"]))

            # Line 14 for parameter HLIFE_NGW
            if ((lidx == 13) and ("HLIFE_NGW" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "HLIFE_NGW"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | HLIFE_NGW : Half-life of nitrate in the shallow aquifer [day]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "HLIFE_NGW"]["TestVal"]))

        # Then write the contents into the same file
        with open(fnpGW, 'w') as swatFile:
            swatFile.writelines(lif)


    ##########################################################################
    def updateParInHru(self,
                       fnSwatHruLvl,
                       parInFile,
                       proj_path,
                       fdname_running):
        # First readin the contents of the old file
        fnpOrig = os.path.join(proj_path,
                               "txtinout",
                               "{}.hru".format(fnSwatHruLvl))
        try:
            with open(fnpOrig, 'r') as swatFileOrig:
                lifOrig = swatFileOrig.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpOrig, e))
            return

        # First readin the contents of the old file
        fnpNewHRU = os.path.join(proj_path,
                           fdname_running,
                           "{}.hru".format(fnSwatHruLvl))
        try:
            with open(fnpNewHRU, 'r') as swatFile:
                lif = swatFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpNewHRU, e))
            return

        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        for lidx in range(len(lif)):
            # Line 3 for parameter SLSUBBSN
            if ((lidx == 2) and ("SLSUBBSN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SLSUBBSN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SLSUBBSN : Average slope length [m]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SLSUBBSN"]["TestVal"]))

            # Line 4 for parameter SLOPE
            # Slope need to be modified by fraction
            if ((lidx == 3) and ("SLOPE" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SLOPE"]["selectFlag"]) == 1):
                    origVal = float(lifOrig[lidx].split("|")[0])
                    newVal = origVal * (1 + float(parInFile.loc[parInFile["Symbol"] == "SLOPE"]["TestVal"]))
                    lif[lidx] = """{:16.3f}    | SLOPE : Main channel slope [m/m]\n""".format(newVal)

            # Line 5 for parameter OV_N
            if ((lidx == 4) and ("OV_N" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "OV_N"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | OV_N : Manning"s "n" value for overland flow\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "OV_N"]["TestVal"]))

            # Line 9 for parameter CANMX
            if ((lidx == 8) and ("CANMX" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CANMX"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | CANMX : Maximum canopy storage [mm]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CANMX"]["TestVal"]))

            # Line 10 for parameter ESCO
            if ((lidx == 9) and ("ESCO" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "ESCO"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | ESCO : Soil evaporation compensation factor\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "ESCO"]["TestVal"]))

            # Line 12 for parameter RSDIN
            if ((lidx == 11) and ("RSDIN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RSDIN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | RSDIN : Initial residue cover [kg/ha]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RSDIN"]["TestVal"]))

            # Line 24 for parameter DEP_IMP
            if ((lidx == 23) and ("DEP_IMP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "DEP_IMP"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | DEP_IMP : Depth to impervious layer in soil profile [mm]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "DEP_IMP"]["TestVal"]))

        # Then write the contents into the same file
        with open(fnpNewHRU, 'w') as swatFile:
            swatFile.writelines(lif)


    ##########################################################################
    def updateParInMgt(self,
                       fnSwatHruLvl,
                       parInFile,
                       proj_path,
                       fdname_running,
                       rowCropLst):
        """
        For mgt, information from HRU and SOL files are required.
        The required information in the HRU file is land type.
        The required information in the SOL file is the hydrologic soil group.
        """
        # First readin the contents of the old file
        fnpHru = os.path.join(proj_path, fdname_running,
                              "{}.hru".format(fnSwatHruLvl))

        fnpMgt = os.path.join(proj_path, fdname_running,
                              "{}.mgt".format(fnSwatHruLvl))

        fnpSol = os.path.join(proj_path, fdname_running,
                              "{}.sol".format(fnSwatHruLvl))

        fnpMgtOrig = os.path.join(proj_path, "txtinout",
                                  "{}.mgt".format(fnSwatHruLvl))



        try:
            with open(fnpHru, 'r') as hruFile:
                lifHru = hruFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpHru, e))
            return

        try:
            with open(fnpSol, 'r') as solFile:
                lifSol = solFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpSol, e))
            return

        try:
            with open(fnpMgtOrig, 'r') as mgtFileOrig:
                lifmgtOrig = mgtFileOrig.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpMgtOrig, e))
            return

        try:
            with open(fnpMgt, 'r') as mgtFile:
                lif = mgtFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpMgt, e))
            return

        # First get the required information from the lines in the HRU and SOL file
        isRowCrops = False

        for rcIdx in rowCropLst:
            if lifHru[0].find(rcIdx):
                isRowCrops = True
                break

        # Get the soil HSG from soil file
        is_soilHSG_BCD = False
        soilHSG = lifSol[2].split(":")[1].replace(" ", "")
        if soilHSG in ["B", "C", "D"]:
            is_soilHSG_BCD = True

        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        for lidx in range(len(lif)):
            # Line 10 for parameter BIOMIX
            if ((lidx == 9) and ("BIOMIX" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "BIOMIX"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | BIOMIX: Biological mixing efficiency\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "BIOMIX"]["TestVal"]))

            # Line 11 for parameter CN_F
            if ((lidx == 10) and ("CN_F" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CN_F"]["selectFlag"]) == 1):
                    origVal = float(lifmgtOrig[lidx].split("|")[0])
                    newVal = origVal * (1 + float(parInFile.loc[parInFile["Symbol"] == "CN_F"]["TestVal"]))
                    lif[lidx] = """{:16.3f}    | CN2: Initial SCS CN II value\n""".format(newVal)

            # Line 12 for parameter USLE_P
            if ((lidx == 11) and ("USLE_P" in varLst) and isRowCrops):
                if (int(parInFile.loc[parInFile["Symbol"] == "USLE_P"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | USLE_P: USLE support practice factor\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "USLE_P"]["TestVal"]))

            # Line 13 for parameter BIOMIN
            if ((lidx == 12) and ("BIOMIN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "BIOMIN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | BIOMIN: Minimum biomass for grazing (kg/ha)\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "BIOMIN"]["TestVal"]))

            # Line 14 for parameter FILTERW
            if ((lidx == 13) and ("FILTERW" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "FILTERW"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | FILTERW: width of edge of field filter strip (m)\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "FILTERW"]["TestVal"]))

            # Line 25 for parameter FILTERW
            if ((lidx == 24) and ("DDRAIN" in varLst) and is_soilHSG_BCD):
                if (int(parInFile.loc[parInFile["Symbol"] == "DDRAIN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | DDRAIN: depth to subsurface tile drain (mm)\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "DDRAIN"]["TestVal"]))

            # Line 26 for parameter TDRAIN
            if ((lidx == 25) and ("TDRAIN" in varLst) and is_soilHSG_BCD):
                if (int(parInFile.loc[parInFile["Symbol"] == "TDRAIN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | TDRAIN: time to drain soil to field capacity (hr)\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "TDRAIN"]["TestVal"]))

            # Line 27 for parameter GDRAIN
            if ((lidx == 26) and ("GDRAIN" in varLst) and is_soilHSG_BCD):
                if (int(parInFile.loc[parInFile["Symbol"] == "GDRAIN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | GDRAIN: drain tile lag time (hr)\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "GDRAIN"]["TestVal"]))

        # Then write the contents into the same file
        with open(fnpMgt, 'w') as swatFile:
            swatFile.writelines(lif)


    ##########################################################################
    def updateParInChm(self,
                       fnSwatHruLvl,
                       parInFile,
                       proj_path,
                       fdname_running):

        fnpSol = os.path.join(proj_path, fdname_running,
            "{}.sol".format(fnSwatHruLvl))

        fnpChm = os.path.join(proj_path, fdname_running,
            "{}.chm".format(fnSwatHruLvl))

        try:
            with open(fnpSol, 'r') as solFile:
                lifSol = solFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpSol, e))
            return

        try:
            with open(fnpChm, 'r') as chmFile:
                lif = chmFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpChm, e))
            return
        # Get the soil depth (line 8) and soil Organic N (line 12) from the sol file
        solDepLst = lifSol[7].split(":")[1][:-1].split(" ")
        while "" in solDepLst:
            solDepLst.remove("")
        solDepLst = list(map(float, solDepLst))
        avgSolDep = sum(solDepLst)/float(len(solDepLst))

        solOCLst = lifSol[11].split(":")[1][:-1].split(" ")
        while "" in solOCLst:
            solOCLst.remove("")
        solOCLst = list(map(float, solOCLst))

        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        for lidx in range(len(lif)):

            # Line 4 for parameter SOLN
            # In the matlab code, the SOLN value was scaled by the following equation:
            # str_SolN = [ones(1,n_layers).*exp(-avg_depth/1000) zeros(1,10-length(sol_depth))];
            # SOLN = x(cellfun(@(x) isequal(x, 'SOLN'), symbol))*str_SolN;
            # We will keep it as it is in the matlab code.
            if ((lidx == 3) and ("SOLN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SOLN"]["selectFlag"]) == 1):
                    preText = lif[lidx].split(":")[0]
                    solValues = lif[lidx].split(":")[1][:-1].split(" ")
                    while "" in solValues:
                        solValues.remove("")
                    solValNoDataInLyr = solValues[len(solDepLst):]
                    newSolNVal = float(parInFile.loc[parInFile["Symbol"] == "SOLN"]["TestVal"])
                    solValHasDataInLyr = [newSolNVal * math.exp(-avgSolDep/1000)] * len(solDepLst)
                    wholeLst = solValHasDataInLyr + list(map(float,solValNoDataInLyr))
                    newValPartinLine = "".join(["{:12.2f}".format(valLayer) for valLayer in wholeLst])
                    lif[lidx] = """{}:{}\n""".format(preText, newValPartinLine)

            # Line 5 for parameter OGRN
            if ((lidx == 4) and ("ORGN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "ORGN"]["selectFlag"]) == 1):
                    preText = lif[lidx].split(":")[0]
                    solValues = lif[lidx].split(":")[1][:-1].split(" ")
                    while "" in solValues:
                        solValues.remove("")
                    solValNoDataInLyr = solValues[len(solDepLst):]
                    newSolNVal = float(parInFile.loc[parInFile["Symbol"] == "ORGN"]["TestVal"])
                    # Soil Organic N depends on the soil organic carbon content in the first layer
                    # print(solOCLst)
                    if not solOCLst[0] == 0.00:
                        mutiPlier = [soc/solOCLst[0] for soc in solOCLst]
                    else:
                        mutiPlier = [0.00] * len(solOCLst)
                    solValHasDataInLyr = [newSolNVal * mutip for mutip in mutiPlier]
                    wholeLst = solValHasDataInLyr + list(map(float,solValNoDataInLyr))
                    newValPartinLine = "".join(["{:12.2f}".format(valLayer) for valLayer in wholeLst])
                    lif[lidx] = """{}:{}\n""".format(preText, newValPartinLine)

            # Line 6 for parameter LABP
            if ((lidx == 5) and ("LABP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "LABP"]["selectFlag"]) == 1):
                    preText = lif[lidx].split(":")[0]
                    solValues = lif[lidx].split(":")[1][:-1].split(" ")
                    while "" in solValues:
                        solValues.remove("")
                    solValNoDataInLyr = solValues[len(solDepLst):]
                    newSolNVal = float(parInFile.loc[parInFile["Symbol"] == "LABP"]["TestVal"])
                    # Soil Organic N depends on the soil organic carbon content in the first layer
                    solValHasDataInLyr =  [newSolNVal] * len(solDepLst)
                    wholeLst = solValHasDataInLyr + list(map(float,solValNoDataInLyr))
                    newValPartinLine = "".join(["{:12.2f}".format(valLayer) for valLayer in wholeLst])
                    lif[lidx] = """{}:{}\n""".format(preText, newValPartinLine)

            # Line 7 for parameter ORGP
            if ((lidx == 6) and ("ORGP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "ORGP"]["selectFlag"]) == 1):
                    preText = lif[lidx].split(":")[0]
                    solValues = lif[lidx].split(":")[1][:-1].split(" ")
                    while "" in solValues:
                        solValues.remove("")
                    solValNoDataInLyr = solValues[len(solDepLst):]
                    newSolNVal = float(parInFile.loc[parInFile["Symbol"] == "ORGP"]["TestVal"])
                    # Soil Organic N depends on the soil organic carbon content in the first layer
                    solValHasDataInLyr =  [newSolNVal] * len(solDepLst)
                    wholeLst = solValHasDataInLyr + list(map(float,solValNoDataInLyr))
                    newValPartinLine = "".join(["{:12.2f}".format(valLayer) for valLayer in wholeLst])
                    lif[lidx] = """{}:{}\n""".format(preText, newValPartinLine)

        # Then write the contents into the same file
        with open(fnpChm, 'w') as swatFile:
            swatFile.writelines(lif)


    ##########################################################################
    def updateParInSol(self,
                       fnSwatHruLvl,
                       parInFile,
                       proj_path,
                       fdname_running):

        fnpOrig = os.path.join(proj_path, "txtinout",
            "{}.sol".format(fnSwatHruLvl))

        try:
            with open(fnpOrig, 'r') as swatFileOrig:
                lifOrig = swatFileOrig.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnpOrig, e))
            return

        fnp = os.path.join(proj_path, fdname_running,
            "{}.sol".format(fnSwatHruLvl))

        try:
            with open(fnp, 'r') as swatFile:
                lif = swatFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnp, e))
            return

        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        for lidx in range(len(lif)):

            # Line 8 for parameter SOL_Z
            if ((lidx == 7) and ("SOL_Z" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SOL_Z"]["selectFlag"]) == 1):
                    preText = lifOrig[lidx].split(":")[0]
                    solValues = lifOrig[lidx].split(":")[1][:-1].split(" ")
                    while "" in solValues:
                        solValues.remove("")
                    origValLst = list(map(float, solValues))
                    mutiPlier = 1.00+float(parInFile.loc[parInFile["Symbol"] == "SOL_Z"]["TestVal"])
                    newValLst = "".join(["{:12.3f}".format(origV * mutiPlier) for origV in origValLst])
                    lif[lidx] = """{}:{}\n""".format(preText, newValLst)

            # Line 10 for parameter SOL_AWC
            if ((lidx == 9) and ("SOL_AWC" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SOL_AWC"]["selectFlag"]) == 1):
                    preText = lifOrig[lidx].split(":")[0]
                    solValues = lifOrig[lidx].split(":")[1][:-1].split(" ")
                    while "" in solValues:
                        solValues.remove("")
                    origValLst = list(map(float, solValues))
                    mutiPlier = 1.00+float(parInFile.loc[parInFile["Symbol"] == "SOL_AWC"]["TestVal"])
                    newValLst = "".join(["{:12.1f}".format(origV * mutiPlier) for origV in origValLst])
                    lif[lidx] = """{}:{}\n""".format(preText, newValLst)

            # Line 11 for parameter SOL_K
            if ((lidx == 10) and ("SOL_K" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SOL_K"]["selectFlag"]) == 1):
                    preText = lifOrig[lidx].split(":")[0]
                    solValues = lifOrig[lidx].split(":")[1][:-1].split(" ")
                    while "" in solValues:
                        solValues.remove("")
                    origValLst = list(map(float, solValues))
                    mutiPlier = 1.00+float(parInFile.loc[parInFile["Symbol"] == "SOL_K"]["TestVal"])
                    newValLst = "".join(["{:12.1f}".format(origV * mutiPlier) for origV in origValLst])
                    lif[lidx] = """{}:{}\n""".format(preText, newValLst)

            # Line 17 for parameter SOL_ALB
            if ((lidx == 16) and ("SOL_ALB" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SOL_ALB"]["selectFlag"]) == 1):
                    preText = lifOrig[lidx].split(":")[0]
                    solValues = lifOrig[lidx].split(":")[1][:-1].split(" ")
                    while "" in solValues:
                        solValues.remove("")
                    origValLst = list(map(float, solValues))
                    mutiPlier = 1.00+float(parInFile.loc[parInFile["Symbol"] == "SOL_ALB"]["TestVal"])
                    newValLst = "".join(["{:12.3f}".format(origV * mutiPlier) for origV in origValLst])
                    lif[lidx] = """{}:{}\n""".format(preText, newValLst)

            # Line 18 for parameter USLE_K
            if ((lidx == 17) and ("USLE_K" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "USLE_K"]["selectFlag"]) == 1):
                    preText = lifOrig[lidx].split(":")[0]
                    solValues = lifOrig[lidx].split(":")[1][:-1].split(" ")
                    while "" in solValues:
                        solValues.remove("")
                    origValLst = list(map(float, solValues))
                    mutiPlier = 1+float(parInFile.loc[parInFile["Symbol"] == "USLE_K"]["TestVal"])
                    newValLst = "".join(["{:12.3f}".format(origV * mutiPlier) for origV in origValLst])
                    lif[lidx] = """{}:{}\n""".format(preText, newValLst)

        # Then write the contents into the same file
        with open(fnp, 'w') as swatFile:
            swatFile.writelines(lif)


    ##########################################################################
    def updateParInBsn(self,
                       parInFile,
                       proj_path,
                       fdname_running):

        fnp = os.path.join(proj_path, fdname_running,
            "basins.bsn")

        try:
            with open(fnp, 'r') as swatFile:
                lif = swatFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                            folder and make sure you have a complete set".format(fnp, e))
            return

        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        for lidx in range(len(lif)):
            # Line 4 for parameter SFTMP
            if ((lidx == 3) and ("SFTMP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SFTMP"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SFTMP : Snowfall temperature\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SFTMP"]["TestVal"]))

            # Line 5 for parameter SMTMP
            if ((lidx == 4) and ("SMTMP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SMTMP"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SMTMP : Snow melt base temperature\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SMTMP"]["TestVal"]))

            # Line 6 for parameter SMFMX
            if ((lidx == 5) and ("SMFMX" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SMFMX"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SMFMX : Melt factor for snow on June 21 [mm H2O/oC-day]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SMFMX"]["TestVal"]))

            # Line 7 for parameter SMFMN
            if ((lidx == 6) and ("SMFMN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SMFMN"]["selectFlag"]) == 1):
                    smfMnVal = float(parInFile.loc[parInFile["Symbol"] == "SMFMN"]["TestVal"])
                    smfMxVal = float(parInFile.loc[parInFile["Symbol"] == "SMFMX"]["TestVal"])
                    if smfMnVal> smfMxVal:
                        smfMnVal = smfMxVal
                    lif[lidx] = """{:16.3f}    | SMFMN : Melt factor for snow on December 21 [mm H2O/oC-day]\n""".format(
                        smfMnVal)

            # Line 8 for parameter TIMP
            if ((lidx == 7) and ("TIMP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "TIMP"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | TIMP : Snow pack temperature lag factor\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "TIMP"]["TestVal"]))

            # Line 9 for parameter SNOCOVMX
            if ((lidx == 8) and ("SNOCOVMX" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SNOCOVMX"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SNOCOVMX : Minimum snow water content that corresponds to 100% snow cover [mm]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SNOCOVMX"]["TestVal"]))

            # Line 10 for parameter SNO50COV
            if ((lidx == 9) and ("SNO50COV" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SNO50COV"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SNO50COV : Fraction of snow volume represented by SNOCOVMX that corresponds to 50% snow cover\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SNO50COV"]["TestVal"]))

            # # Line 13 for parameter ESCO
            # if ((lidx == 9) and ("ESCO" in varLst)):
            #     if (int(parInFile.loc[parInFile["Symbol"] == "ESCO"]["selectFlag"]) == 1):
            #         lif[lidx] = """{:16.3f}    | ESCO :  soil evaporation compensation factor\n""".format(
            #             float(parInFile.loc[parInFile["Symbol"] == "ESCO"]["TestVal"]))

            # Line 14 for parameter EPCO
            if ((lidx == 13) and ("EPCO" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "EPCO"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | EPCO : plant water uptake compensation factor\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "EPCO"]["TestVal"]))

            # Line 15 for parameter EVLAI
            if ((lidx == 14) and ("EVLAI" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "EVLAI"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | EVLAI : Leaf area index at which no evaporation occurs from water surface [m2/m2]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "EVLAI"]["TestVal"]))

            # Line 20 for parameter SURLAG
            if ((lidx == 19) and ("SURLAG" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SURLAG"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SURLAG : Surface runoff lag time [days]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SURLAG"]["TestVal"]))

            # Line 21 for parameter ADJ_PKR
            if ((lidx == 20) and ("ADJ_PKR" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "ADJ_PKR"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | ADJ_PKR : Peak rate adjustment factor for sediment routing in the subbasin (tributary channels)\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "ADJ_PKR"]["TestVal"]))

            # Line 22 for parameter PRF
            if ((lidx == 21) and ("PRF" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "PRF"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | PRF_BSN : Peak rate adjustment factor for sediment routing in the main channel\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "PRF"]["TestVal"]))

            # Line 23 for parameter SPCON
            if ((lidx == 22) and ("SPCON" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SPCON"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SPCON : Linear parameter for calculating the maximum amount of sediment that can be reentrained during channel sediment routing\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SPCON"]["TestVal"]))

            # Line 24 for parameter SPEXP
            if ((lidx == 23) and ("SPEXP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SPEXP"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SPEXP : Exponent parameter for calculating sediment reentrained in channel sediment routing\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SPEXP"]["TestVal"]))

            # Line 26 for parameter RCN
            if ((lidx == 25) and ("RCN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RCN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | RCN : nitrogen in rainfall (ppm)\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RCN"]["TestVal"]))

            # Line 27 for parameter CMN
            if ((lidx == 26) and ("CMN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CMN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | CMN : Rate factor for humus mineralization of active organic nitrogen\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CMN"]["TestVal"]))

            # Line 28 for parameter N_UPDIS
            if ((lidx == 27) and ("N_UPDIS" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "N_UPDIS"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | N_UPDIS : Nitrogen uptake distribution parameter\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "N_UPDIS"]["TestVal"]))

            # Line 30 for parameter NPERCO
            if ((lidx == 29) and ("NPERCO" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "NPERCO"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | NPERCO : Nitrogen percolation coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "NPERCO"]["TestVal"]))

            # Line 31 for parameter PPERCO
            if ((lidx == 30) and ("PPERCO" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "PPERCO"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | PPERCO : Phosphorus percolation coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "PPERCO"]["TestVal"]))

            # Line 32 for parameter PHOSKD
            if ((lidx == 31) and ("PHOSKD" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "PHOSKD"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | PHOSKD : Phosphorus soil partitioning coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "PHOSKD"]["TestVal"]))

            # Line 33 for parameter PSP
            if ((lidx == 32) and ("PSP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "PSP"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | PSP : Phosphorus sorption coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "PSP"]["TestVal"]))

            # Line 34 for parameter PSP
            if ((lidx == 33) and ("RSDCO" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RSDCO"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | RSDCO : Residue decomposition coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RSDCO"]["TestVal"]))

            # Line 36 for parameter PERCOP
            if ((lidx == 35) and ("PERCOP" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "PERCOP"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | PERCOP : Pesticide percolation coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "PERCOP"]["TestVal"]))

            # Line 59 for parameter MSK_CO1
            if ((lidx == 58) and ("MSK_CO1" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "MSK_CO1"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | MSK_CO1 : Calibration coefficient used to control impact of the storage time constant (Km) for normal flow \n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "MSK_CO1"]["TestVal"]))

            # Line 60 for parameter MSK_CO2
            if ((lidx == 59) and ("MSK_CO2" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "MSK_CO2"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | MSK_CO2 : Calibration coefficient used to control impact of the storage time constant (Km) for low flow \n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "MSK_CO2"]["TestVal"]))

            # Line 61 for parameter MSK_X
            if ((lidx == 60) and ("MSK_X" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "MSK_X"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | MSK_X : Weighting factor controlling relative importance of inflow rate and outflow rate in determining water storage in reach segment\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "MSK_X"]["TestVal"]))

            # Line 66 for parameter EVRCH
            if ((lidx == 65) and ("EVRCH" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "EVRCH"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | EVRCH : Reach evaporation adjustment factor\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "EVRCH"]["TestVal"]))

            # Line 68 for parameter ICN
            if ((lidx == 67) and ("ICN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "ICN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | ICN  : Daily curve number calculation method\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "ICN"]["TestVal"]))

            # Line 69 for parameter CNCOEF
            if ((lidx == 68) and ("CNCOEF" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CNCOEF"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | CNCOEF : Plant ET curve number coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CNCOEF"]["TestVal"]))

            # Line 70 for parameter CDN
            if ((lidx == 69) and ("CDN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "CDN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | CDN : Denitrification exponential rate coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "CDN"]["TestVal"]))

            # Line 71 for parameter SDNCO
            if ((lidx == 70) and ("SDNCO" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "SDNCO"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | SDNCO : Denitrification threshold water content\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "SDNCO"]["TestVal"]))

            # Line 81 for parameter DEPIMP_BSN
            if ((lidx == 80) and ("DEPIMP_BSN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "DEPIMP_BSN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | DEPIMP_BSN : Depth to impervious layer for modeling perched water tables [mm]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "DEPIMP_BSN"]["TestVal"]))

            # Line 88 for parameter FIXCO
            if ((lidx == 87) and ("FIXCO" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "FIXCO"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | FIXCO : Nitrogen fixation coefficient\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "FIXCO"]["TestVal"]))

            # Line 89 for parameter NFIXMX
            if ((lidx == 88) and ("NFIXMX" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "NFIXMX"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | NFIXMX : Maximum daily-n fixation [kg/ha]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "NFIXMX"]["TestVal"]))

            # Line 90 for parameter ANION_EXCL_BSN
            if ((lidx == 89) and ("ANION_EXCL_BSN" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "ANION_EXCL_BSN"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | ANION_EXCL_BSN : Fraction of porosity from which anions are excluded\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "ANION_EXCL_BSN"]["TestVal"]))



        # Then write the contents into the same file
        with open(fnp, 'w') as swatFile:
            swatFile.writelines(lif)


    ##########################################################################
    def updateParInCrop(self,
                        parInFile,
                        proj_path,
                        fdname_running):

        """
        Sometimes the crop is named "crop.dat". Other projects
        used "plant.dat".
        I will try both.
        """
        fnpOrig = os.path.join(proj_path, "txtinout",
            "plant.dat")
        if not os.path.isfile(fnpOrig):
            fnpOrig = os.path.join(proj_path, "txtinout",
                "crop.dat")
        try:
            with open(fnpOrig, 'r') as swatFileOrig:
                lifOrig = swatFileOrig.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                                        folder and make sure you have a complete set".format(fnpOrig, e))
            return

        fnp = os.path.join(proj_path, fdname_running,
            "plant.dat")
        if not os.path.isfile(fnp):
            fnp = os.path.join(proj_path, fdname_running,
                "crop.dat")
        try:
            with open(fnp, 'r') as swatFile:
                lif = swatFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                                        folder and make sure you have a complete set".format(fnp, e))
            return

        # Only values in crop and pasture land are updated.
        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()
        if "USLE_C" in varLst:
            if (int(parInFile.loc[parInFile["Symbol"] == "USLE_C"]["selectFlag"]) == 1):
                usleCVal = float(parInFile.loc[parInFile["Symbol"] == "USLE_C"]["TestVal"])
                for lidx in range(len(lif)):
                    # USLE_C need to be modified by fraction
                    # Line 4 for AGRL
                    if (lidx in [3, 8, 13, 93, 58, 278, 138]):
                        lifOrig[lidx] = lifOrig[lidx][:-1].split(" ")
                        while "" in lifOrig[lidx]:
                            lifOrig[lidx].remove("")
                        lifOrig[lidx] = list(map(float, lifOrig[lidx]))

                        lif[lidx] = lif[lidx][:-1].split(" ")
                        while "" in lif[lidx]:
                            lif[lidx].remove("")
                        lif[lidx] = list(map(float, lif[lidx]))
                        lif[lidx][1] = lifOrig[lidx][1] * (1.0 + usleCVal)
                        lif[lidx] = "".join(["{:8.3f}".format(cropVal) for cropVal in lif[lidx]]) + "\n"


        # Then write the contents into the same file
        with open(fnp, 'w') as swatFile:
            swatFile.writelines(lif)


    ##########################################################################
    def updateParInWwq(self,
                       parInFile,
                       proj_path,
                       fdname_running):
        """
        Sometimes the crop is named "crop.dat". Other projects
        used "plant.dat".
        I will try both.
        """
        fnp = os.path.join(proj_path, fdname_running, "basins.wwq")

        try:
            with open(fnp, 'r') as swatFile:
                lif = swatFile.readlines()
        except IOError as e:
            showinfo("Warning", "File {} does not exist: {}. Please double check your TxtInOut \
                                        folder and make sure you have a complete set".format(fnp, e))
            return

        # Only values in crop and pasture land are updated.
        # Get a list of variables selected. Since we can get in this function,
        # at least one variable in the sub file was selected.
        varLst = parInFile["Symbol"].unique()

        for lidx in range(len(lif)):
            # Line 4 for parameter AI0
            if ((lidx == 3) and ("AI0" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "AI0"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | AI0 : Ratio of chlorophyll-a to algal biomass [chla/mg algae]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "AI0"]["TestVal"]))

            # Line 5 for parameter AI1
            if ((lidx == 4) and ("AI1" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "AI1"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | AI1 : Fraction of algal biomass that is nitrogen [mg N/mg alg]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "AI1"]["TestVal"]))

            # Line 6 for parameter AI2
            if ((lidx == 5) and ("AI2" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "AI2"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | AI2 : Fraction of algal biomass that is phosphorus [mg P/mg alg]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "AI2"]["TestVal"]))

            # Line 11 for parameter MUMAX
            if ((lidx == 10) and ("MUMAX" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "MUMAX"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | MUMAX : Maximum specific algal growth rate at 20oC [day-1]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "MUMAX"]["TestVal"]))

            # Line 12 for parameter RHOQ
            if ((lidx == 11) and ("RHOQ" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "RHOQ"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | RHOQ : Algal respiration rate at 20oC [day-1]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "RHOQ"]["TestVal"]))

            # Line 15 for parameter K_N
            if ((lidx == 14) and ("K_N" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "K_N"]["selectFlag"]) == 1):
                    lif[
                        lidx] = """{:16.3f}    | K_N : Michaelis-Menton half-saturation constant for nitrogen [mg N/lL]\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "K_N"]["TestVal"]))

            # Line 20 for parameter P_N
            if ((lidx == 19) and ("P_N" in varLst)):
                if (int(parInFile.loc[parInFile["Symbol"] == "P_N"]["selectFlag"]) == 1):
                    lif[lidx] = """{:16.3f}    | P_N : Algal preference factor for ammonia\n""".format(
                        float(parInFile.loc[parInFile["Symbol"] == "P_N"]["TestVal"]))

        # Then write the contents into the same file
        with open(fnp, 'w') as swatFile:
            swatFile.writelines(lif)

