# -*- coding: utf-8 -*-
"""
Created on Tue May 12 2020

This class is designed to be a collection of functions dealing with
DDS procedure.

@author: Qingyu.Feng
"""

import copy
import time
from datetime import date
import json
import pickle
import calendar
import os
import pandas
import glob
import multiprocessing
from shutil import copyfile
import functools
import subprocess
import datetime
import numpy
import math
# from sklearn.metrics import r2_score, mean_squared_error

# importing date class from datetime module
# from datetime import date
from .global_vars import global_vars
from .mod_swatutils import swat_utils

GlobalVars = global_vars()
SwatUtil = swat_utils()

from tkinter.messagebox import showinfo

from .mod_graphutils import *


def read_observed_data(cali_options,
                       proj_folder,
                       pair_varid_obs_header,
                       obs_data_header):
    """
    Get the outlet, variable structure
    Each outlet might have several variables.
    These need to be separated.
    The reasons for this is:
    The parameter of flow and sediment are different.
    During the DDS procedure, if the objective functions are
    combined by weight, the dds procedure will select
    parameters from the pool of flow+sedi. Then, the
    changes of selecting parameters for each variable
    will be decreased. The fact is that there are more
    parameters for flow than for sediment.
    Another fact was that the improvement of sediment
    depends largely on improvement of flow. When combined,
    the improvement will be slower, even if different
    weights are provided.
    So, the weights are mainly used for lumped method
    to combine objective function. Distributed will mean
    fully distributed DDS.

    :param obs_data_header:
    :param cali_options:
    :param proj_folder:
    :param pair_varid_obs_header:
    :return:
    """
    iprint = cali_options["iprint"]
    sim_start_date = cali_options["simstartdate"]
    sim_end_date = cali_options["simenddate"]
    warmup_year = cali_options["warmupyrs"]

    # Get the list of olt-var, and their corresponding
    # variables and weights
    all_outlet_detail = copy.deepcopy(cali_options["outlet_details"])

    date_header = ["yyyy", "mm", "dd", "Date"]
    for olt_key in all_outlet_detail.keys():
        olt_id = all_outlet_detail[olt_key]["outletid"]
        var_id = all_outlet_detail[olt_key]["variableid"]

        # Monthly
        fn_obs_data = "obs_{}{}.prn".format(iprint, olt_id)
        fnp_obs_data = os.path.join(proj_folder, "observeddata", fn_obs_data)

        dataframe_observed = pandas.read_table(fnp_obs_data, names=obs_data_header, skiprows=1)

        if iprint == "daily":
            dataframe_observed["Date"] = dataframe_observed.apply(year_month_day_to_timestamp, axis=1)
        elif iprint == "monthly":
            dataframe_observed["Date"] = dataframe_observed.apply(year_month_to_timestamp, axis=1)
        elif iprint == "annual":
            dataframe_observed["Date"] = dataframe_observed.apply(year_to_timestamp, axis=1)

        # Check the start and end date by User in the control file and
        # in the observed Data.
        obs_start_date = dataframe_observed.iloc[[0], [0, 1, 2]]
        obs_end_date = dataframe_observed.iloc[[-1], [0, 1, 2]]

        # Check the length of the observed data to make sure it covered the
        # simulation length specified by user.
        sim_start_date_lst = sim_start_date.split("/")
        sim_end_date_lst = sim_end_date.split("/")
        sim_start_date_ts = pandas.Timestamp(
            year=int(sim_start_date_lst[2]) + int(warmup_year),
            month=int(sim_start_date_lst[0]),
            day=int(sim_start_date_lst[1])
        )

        sim_end_date_ts = pandas.Timestamp(
            year=int(sim_end_date_lst[2]),
            month=int(sim_end_date_lst[0]),
            day=int(sim_end_date_lst[1]))

        obs_start_date_ts = pandas.Timestamp(
            day=int(obs_start_date["dd"]),
            month=int(obs_start_date["mm"]),
            year=int(obs_start_date["yyyy"])
        )
        obs_end_date_ts = pandas.Timestamp(
            day=int(obs_end_date["dd"]),
            month=int(obs_end_date["mm"]),
            year=int(obs_end_date["yyyy"])
        )

        if (sim_start_date_ts > obs_end_date_ts) or (obs_start_date_ts > sim_end_date_ts):
            showinfo("Warning", "The observed data period does not match that of simulation for outlet {}".format(
                olt_id))
            return False
        else:
            # Trim obsDF to the user specified start and end date
            dataframe_observed = dataframe_observed.loc[dataframe_observed["Date"] >= sim_start_date_ts]
            dataframe_observed = dataframe_observed.loc[dataframe_observed["Date"] <= sim_end_date_ts]

            # Get the interested columns from the whole data frame
            var_col_names = date_header + [pair_varid_obs_header[var_id]]
            all_outlet_detail[olt_key]["df_obs"] = dataframe_observed.loc[:, var_col_names]

    return all_outlet_detail


##########################################################################
# This three functions were called by pandas.DataFrame.apply function
# to convert the year month and date information into the pandas.
# Timestamp object.
def year_to_timestamp(row_value):
    new_date = pandas.Timestamp(
        year=int(row_value["yyyy"]),
        month=int(row_value["mm"]),
        day=int(row_value["dd"])) + pandas.tseries.offsets.YearEnd(0)
    return new_date

def year_month_to_timestamp(row_value):
    new_date = pandas.Timestamp(
        year=int(row_value["yyyy"]),
        month=int(row_value["mm"]),
        day=int(row_value["dd"])) + pandas.tseries.offsets.MonthEnd(0)
    return new_date


def year_month_day_to_timestamp(row_value):
    new_date = pandas.Timestamp(
        year=int(row_value["yyyy"]),
        month=int(row_value["mm"]),
        day=int(row_value["dd"]))
    return new_date


def get_today_date():
    """
    get the mon, day, year of today for initializing the gui
    :return: year, month, day
    """
    # creating the date object of today's date
    todays_date = date.today()
    return todays_date.year, todays_date.month, todays_date.day


def read_json_file(path_json):
    """
    Read json file into a variable
    :param path_json:
    :return: data_json
    """
    # Read the json file into the proj_data variable for later reference
    with open(path_json, 'r') as proj_json_file:
        data_json = json.load(proj_json_file)

    return data_json


def write_json_file(data_json, path_json):
    """
    Write data into a json file
    :param path_json:
    :param data_json:
    """
    # Read the json file into the proj_data variable for later reference
    with open(path_json, 'w') as proj_json_file:
        json.dump(data_json, proj_json_file)


def write_pickle_file(data_pickle, path_picklefile):
    """
    Write data into a json file
    :param data_pickle:
    :param path_picklefile
    """
    # Read the json file into the proj_data variable for later reference
    with open(path_picklefile, 'wb') as pickle_file:
        pickle.dump(data_pickle, pickle_file, pickle.HIGHEST_PROTOCOL)


def read_pickle_file(path_pickle_file):
    """
    Write data into a json file
    :return data_pickle
    :param path_pickle_file
    """
    # Read the json file into the proj_data variable for later reference
    with open(path_pickle_file, 'rb') as pickle_file:
        data_pickle = pickle.load(pickle_file)

    return data_pickle


def julianday_to_yymmdd(year, julian_day):
    """
    convert julian day in a year into date
    :param year:
    :param julian_day:
    :return:
    """
    month = 1
    while julian_day - calendar.monthrange(year, month)[1] > 0 and month <= 12:
        julian_day = julian_day - calendar.monthrange(year, month)[1]
        month = month + 1

    return month, julian_day


def date_to_julianday(year, month, day):
    """
    convert date of a year into julian day
    :param year:
    :param month:
    :param day:
    :return: julianday
    """
    d0 = date(year, 1, 1)
    d1 = date(year, month, day)
    delta = d1 - d0
    julianday = delta.days + 1

    return julianday


##########################################################################
def getSubGroupsForOutlet(outlet_details,
                        subarea_group_mode,
                          proj_folder):
    """
    group the subarea for each outlet based on watershed graph
    Also, the reach list including all reaches will be generated.
    :param cali_options:
    :param proj_folder:
    :return:
    """

    fn_reach_file = "reach.shp"
    fnp_reach_file = os.path.join(proj_folder, "reachshapefile", fn_reach_file)

    field_names, subarea_attributes = read_shape_attributes(fnp_reach_file)

    # Get a graph of the watershed
    watershed_graph, reach_no_list = get_watershed_graph(field_names, subarea_attributes)

    # Get outlet list
    usr_outlet_list = []
    for olt_var_id in outlet_details.keys():
        outlet_id = outlet_details[olt_var_id]["outletid"]
        if outlet_id not in usr_outlet_list:
            usr_outlet_list.append(outlet_id)

    if subarea_group_mode == "dist":
        # Get Groups of the watershed
        subarea_groups_origin = groupSubForOutlet(usr_outlet_list,
                                                  watershed_graph,
                                                  reach_no_list)
        subarea_groups = dealWithOverlayInSubGroups(subarea_groups_origin)
    elif subarea_group_mode == "lump":
        subarea_groups = {"not_grouped_subareas": reach_no_list}

    return subarea_groups


##########################################################################
def getParmSets(parm_dict,
                basin_file_exts,
                sub_level_file_exts,
                hru_level_file_exts):
    """
    this functiion readin the parameter sets for subareas
    """
    parm_set_full = pandas.DataFrame.from_dict(parm_dict, orient="index")

    # Remove those non selected parameters
    parm_selected = parm_set_full.loc[parm_set_full['selectFlag'] == "1"].copy(deep=True)

    # Convert the column values into float for calculation in following steps.
    parm_selected["InitVal"] = parm_selected["InitVal"].apply(float)
    parm_selected["LowerBound"] = parm_selected["LowerBound"].apply(float)
    parm_selected["UpperBound"] = parm_selected["UpperBound"].apply(float)
    # Add two columns to parameter test and best values
    parm_selected["BestVal"] = parm_selected["InitVal"]
    parm_selected["TestVal"] = parm_selected["InitVal"]
    # Add one column to store whether a parameter is selected in one run
    parm_selected["ModThisRun"] = [0] * len(parm_selected["InitVal"])
    ##########################################################################
    # Generate file extension list and file names ############################
    # Creating a set of parameters that will need to be updated
    # at the basin level and the subarea and hru level.
    # Then, create an individual copy of parameter at the subarea
    # and hru level for each subarea group.
    # The updating of basin level will be based on the overall
    # objective function value, and those at the subarea/hru leve
    # will be conducted based on the subarea group objective
    # function value.
    parm_basin_level = copy.deepcopy(parm_selected)
    parm_basin_level = parm_basin_level.loc[parm_basin_level["File"].isin(basin_file_exts)]

    sub_hru_level_file_ext = sub_level_file_exts + hru_level_file_exts
    parm_sub_level = copy.deepcopy(parm_selected)
    parm_sub_level = parm_sub_level.loc[parm_sub_level["File"].isin(sub_hru_level_file_ext)]

    return parm_basin_level, parm_sub_level



##########################################################################
def initialOutFNameParmObjSublvl(
        cali_mode,
        all_outlet_detail,
        proj_path,
        fdname_outfiles,
        pair_varid_obs_header):
    """
    Initialize the output file names, including subarea parameter values, subarea
    objective function, and parameter select during the runs
    """
    sub_parm_fnames = {}
    sub_obj_fnames = {}
    sub_parm_select_fnames = {}

    path_output = os.path.join(proj_path, fdname_outfiles)

    if cali_mode == "dist":
        # Files recording the autocalibration processes
        # Each observed data element contains a pair of outlet and subarea
        # Initiate the objective function values and out files
        # Here, we will need to get actually the outlet_var list since
        # one outlet might have two variables. Thus, each pair, will have
        # one file.
        # For distributed mode, the objective function in the file is its
        # objectives get during the iteration. However, if there are more than
        # one objective functions selected with weights, the combined
        # objective function will need to be recorded as well.
        # This is actually recorded in the TestOF values.
        # Headers of obf value and param value files.
        for opKeys, outlet_detail in all_outlet_detail.items():
            # Initialize the parameter files
            var_name = pair_varid_obs_header[outlet_detail["variableid"]]
            var_name = var_name.split("(")[0]
            fnParaEachRun = os.path.join(
                path_output,
                "DMPOT_Para_{}{}_{}.out".format(
                    outlet_detail["outletid"],
                    var_name,
                    cali_mode))
            sub_parm_fnames[opKeys] = fnParaEachRun

            # Initialize the parameter selection files
            fnParaSelEachRun = os.path.join(
                path_output,
                "DMPOT_ParaSel_{}{}_{}.out".format(
                    outlet_detail["outletid"],
                    var_name,
                    cali_mode))
            sub_parm_select_fnames[opKeys] = fnParaSelEachRun

            # Initialize the objective value files
            fnObjFunEachRun = os.path.join(
                path_output,
                "DMPOT_ObjFun_{}{}_{}.out".format(
                    outlet_detail["outletid"],
                    var_name,
                    cali_mode))
            sub_obj_fnames[opKeys] = fnObjFunEachRun

    elif cali_mode == "lump":
        # Initiate the objective function values and out files
        # Here, we will need to get actually the outlet_var list since
        # one outlet might have two variables
        # For lumped mode, besides getting its own objective function, there
        # need to be a file summarizing the best objective function.
        # This will be done by adding a column to record this.
        # For lump, there are two layers of weights, the weights of different
        # objective functions, and the weights of each outlet pair.
        # For the lumped mode, an additional file containing the
        # overall objective functions for all different pairs will be created.
        # The parameter file and parameter selection file will be
        # one since there are lumped.
        # Actually, the TestOF value should be all equal to each other for
        # different pairs. Also, the best obf for each pair should be recorded.
        # Thus, the head need to have one more column recording the overall obj
        fnParaEachRun = os.path.join(
            path_output,
            "DMPOT_Para_lump_sub_level.out")

        sub_parm_fnames["not_grouped_subareas"] = fnParaEachRun

        # Only one subparam file need to be initialized
        fnParaSelEachRun = os.path.join(
            path_output,
            "DMPOT_ParaSel_lump_sub_level.out")
        sub_parm_select_fnames["not_grouped_subareas"] = fnParaSelEachRun

        # Files recording the autocalibration processes
        for opKeys, outlet_detail in all_outlet_detail.items():
            # Initialize the parameter files
            var_name = pair_varid_obs_header[outlet_detail["variableid"]]
            var_name = var_name.split("(")[0]

            # Initialize the objective value files
            if outlet_detail["outletid"] != "not_grouped_subareas":
                fnObjFunEachRun = os.path.join(
                    path_output,
                    "DMPOT_ObjFun_{}{}_{}.out".format(
                        outlet_detail["outletid"],
                        var_name,
                        cali_mode))
                sub_obj_fnames[opKeys] = fnObjFunEachRun

    return sub_parm_fnames, sub_parm_select_fnames, sub_obj_fnames


##########################################################################
def initialOutFNameParmObjBsnlvl(
        proj_path,
        fdname_outfiles,
        cali_mode):
    """
    Initialize the output file names for basin level
    :param parm_basin_level:
    :param proj_path:
    :param cali_mode:
    :return:
    """
    # Initialize the basin level parameter file as a record
    # First Deal with basin level parameter
    path_output = os.path.join(proj_path, fdname_outfiles)
    bsn_parm_value_fn = os.path.join(path_output, "DMPOT_Para_Bsn_{}.out".format(cali_mode))
    bsn_parm_sel_fn = os.path.join(path_output, "DMPOT_ParaSel_Bsn_{}.out".format(cali_mode))
    bsn_obj_fn = os.path.join(path_output, "DMPOT_ObjFun_Bsn_{}.out".format(cali_mode))

    return bsn_parm_value_fn, bsn_parm_sel_fn, bsn_obj_fn


##########################################################################
def writeOutFileHeadersParmObjSublvl(cali_mode,
                                all_outlet_detail,
                                parm_sub_level_symbol,
                                fdname_outfiles,
                                pair_varid_obs_header,
                                sub_parm_value_outfn,
                                sub_parm_select_outfn,
                                sub_objfun_outfn
                                ):
    """
    Initialize the output file names, including subarea parameter values, subarea
    objective function, and parameter select during the runs
    """
    # path_output = os.path.join(proj_path, fdname_outfiles)
    dist_obj_val_hdr_sub = "RunNO,Outlet,Var,NSE,R2,MSE,PBIAS,RMSE,RSR,TestOF,BestOF,probVal\n"
    dist_par_val_hdr_sub = "RunNO,Outlet,Var," + ",".join(parm_sub_level_symbol.to_list()) + "\n"
    lump_obj_val_hdr_basin = "RunNO,Outlet,TestOF,BestOF,probVal\n"

    if cali_mode == "dist":
        for opKeys, outlet_detail in all_outlet_detail.items():

            # Get the corresponding parameter set for the variables of this pair
            var_id = outlet_detail["variableid"]
            # var_name = pair_varid_obs_header[var_id].split("(")[0]
            if os.path.isfile(sub_objfun_outfn[opKeys]):
                os.remove(sub_objfun_outfn[opKeys])
            with open(sub_objfun_outfn[opKeys], 'w') as obfFile:
                obfFile.writelines(dist_obj_val_hdr_sub)

            if os.path.isfile(sub_parm_value_outfn[opKeys]):
                os.remove(sub_parm_value_outfn[opKeys])
            with open(sub_parm_value_outfn[opKeys], 'w') as parvFile:
                parvFile.writelines(dist_par_val_hdr_sub)

            if os.path.isfile(sub_parm_select_outfn[opKeys]):
                os.remove(sub_parm_select_outfn[opKeys])
            with open(sub_parm_select_outfn[opKeys], 'w') as parselFile:
                parselFile.writelines(dist_par_val_hdr_sub)

    elif cali_mode == "lump":

        if os.path.isfile(sub_parm_value_outfn["not_grouped_subareas"]):
            os.remove(sub_parm_value_outfn["not_grouped_subareas"])
        with open(sub_parm_value_outfn["not_grouped_subareas"], 'w') as parvFile:
            parvFile.writelines(dist_par_val_hdr_sub)

        if os.path.isfile(sub_parm_select_outfn["not_grouped_subareas"]):
            os.remove(sub_parm_select_outfn["not_grouped_subareas"])
        with open(sub_parm_select_outfn["not_grouped_subareas"], 'w') as parselFile:
            parselFile.writelines(dist_par_val_hdr_sub)

        for opKeys, outlet_detail in all_outlet_detail.items():
            if opKeys != "not_grouped_subareas":
                # Get the corresponding parameter set for the variables of this pair
                var_id = outlet_detail["variableid"]
                # var_name = pair_varid_obs_header[var_id].split("(")[0]
                if os.path.isfile(sub_objfun_outfn[opKeys]):
                    os.remove(sub_objfun_outfn[opKeys])
                with open(sub_objfun_outfn[opKeys], 'w') as obfFile:
                    obfFile.writelines(dist_obj_val_hdr_sub)



##########################################################################
def writeOutFileHeadersParmObjBsnlvl(
        parm_basin_level_symbol,
        bsn_parm_value_fn,
        bsn_parm_sel_fn,
        bsn_obj_fn):
    """
    Initialize the output file names for basin level
    :param parm_basin_level:
    :param proj_path:
    :return:
    """
    # Initialize the basin level parameter file as a record
    # First Deal with basin level parameter
    parm_val_hdr = "RunNO," + ",".join(parm_basin_level_symbol.to_list()) + "\n"
    lump_obj_val_hdr_basin = "RunNO,Outlet,TestOF,BestOF,probVal\n"
    if os.path.isfile(bsn_parm_value_fn):
        os.remove(bsn_parm_value_fn)
    with open(bsn_parm_value_fn, 'w') as bsnParmFile:
        bsnParmFile.writelines(parm_val_hdr)

    if os.path.isfile(bsn_parm_sel_fn):
        os.remove(bsn_parm_sel_fn)
    with open(bsn_parm_sel_fn, 'w') as bsnParmSFile:
        bsnParmSFile.writelines(parm_val_hdr)

    if os.path.isfile(bsn_obj_fn):
        os.remove(bsn_obj_fn)
    with open(bsn_obj_fn, 'w') as bsnParmSFile:
        bsnParmSFile.writelines(lump_obj_val_hdr_basin)


##########################################################################
def initParmset(all_outlet_detail,
                parm_sub_level,
                pair_varid_obs_header):
    """
    Add the corresponding parameter set into the outlet_detail dictionary for
    updating.
    :param all_outlet_detail:
    :param parm_sub_level:
    :param pair_varid_obs_header:
    :return:
    """
    # For whether the distributed and lumped mode, the initialization of parameter
    # sets is based on keys. Key "not_grouped_subareas" always has the whole
    # parameter set since it has no variables of observation associated.
    for olt_var_key, outlet_details in all_outlet_detail.items():
        if olt_var_key != "not_grouped_subareas":
            # Get the corresponding parameter set for the variables of this pair
            var_id = outlet_details["variableid"]
            var_name = pair_varid_obs_header[var_id].split("(")[0]
            # Get the corresponding variables selected
            # Check whether the selected parameters corresponds to the variables
            # 1, for flow
            if var_id == "1":
                outlet_details["parm_sub"] = parm_sub_level.loc[
                    parm_sub_level['ForVariable'] == "Flow"].copy(deep=True)
            # 2 for sediment
            elif var_id in "2":
                outlet_details["parm_sub"] = parm_sub_level.loc[
                    parm_sub_level['ForVariable'] == "Sediment"].copy(deep=True)
            # 3, 5, 6, 7, 12 for nitrogen
            elif var_id in ["3", "5", "6", "7", "12"]:
                outlet_details["parm_sub"] = parm_sub_level.loc[
                    parm_sub_level['ForVariable'] == "Nitrogen"].copy(deep=True)
            # 4, 8, 9, 10, 11, 13 for phosphorus
            elif var_id in ["4", "8", "9", "10", "11", "13"]:
                outlet_details["parm_sub"] = parm_sub_level.loc[
                    parm_sub_level['ForVariable'] == "Phosphorus"].copy(deep=True)
        elif olt_var_key == "not_grouped_subareas":
            outlet_details["parm_sub"] = parm_sub_level.copy(deep=True)

    return all_outlet_detail


##########################################################################
def initFilenameList(proj_path,
                     subarea_groups):
    """
    Add the file list to each variable for modification, there will be
    two levels, sub_level_files, hru_level_files.
    :param proj_path:
    :param subarea_groups: to get the list of subarea nos
    :return:
    """
    # Create the subarea and hru file names
    sub_level_filenames = {}
    hru_level_filenames = {}
    path_working_dir = os.path.join(proj_path, "txtinout")

    for sub_group_key in subarea_groups.keys():
        # Geneate sub level file name list for modifying
        sub_level_filenames[sub_group_key] = list(map(buildSWATSubFn, subarea_groups[sub_group_key]))

        # Generate hru level file name list for modifying
        hru_filename_list = []
        for sub_idx in sub_level_filenames[sub_group_key]:
            hru_filename_list = hru_filename_list + buildSWATHruFn(sub_idx, path_working_dir)
        hru_level_filenames[sub_group_key] = hru_filename_list

    return sub_level_filenames, hru_level_filenames


##########################################################################
def buildSWATSubFn(sub_gis_no):
    """
    This function takes the subarea no from GIS and convert
    them to the SWAT subarea name convention.
    """

    if (len(sub_gis_no)) < 2:
        sub_zeros = '0000'
    elif (len(sub_gis_no) >= 2) and (len(sub_gis_no) < 3):
        sub_zeros = '000'
    elif (len(sub_gis_no) >= 3) and (len(sub_gis_no) < 4):
        sub_zeros = '00'
    elif (len(sub_gis_no) >= 4) and (len(sub_gis_no) < 5):
        sub_zeros = '0'
    elif len(sub_gis_no) >= 5:
        sub_zeros = ''

    sub_filename = "{}{}0000".format(sub_zeros, sub_gis_no)

    return sub_filename


##########################################################################
def buildSWATHruFn(fnSwatSub, runningDir):
    """
    This function takes the .sub file name, read the file,
    get the total number of hrus in the subarea, and create
    a list of hru files for each subarea.
    """
    fnSWATHruLst = []
    fnpSwatSub = os.path.join(runningDir,
                              "{}.sub".format(fnSwatSub))
    try:
        with open(fnpSwatSub, 'r', encoding="ISO-8859-1") as f:
            lif = f.readlines()
    except IOError as e:
        showinfo("Warning",
                 """File {} does not exist: {}. The
                    sub GIS no is obtained from the reach.shp 
                    please make sure you are using the corresponding 
                    shapefile and the files in the \"txtinout\" folder.
                    """.format(fnpSwatSub, e))
        return

    totalHruNo = int(lif[52].split("|")[0])
    subPrefix = os.path.split(fnpSwatSub)[1][:5]
    hruZeros = "000"

    for hruIdx in range(1, totalHruNo + 1):
        # Determint the number of 0 to be added before hru no in the
        # hru file name.
        if (hruIdx < 10):
            hruZeros = "000"
        elif ((hruIdx >= 10) and (hruIdx < 100)):
            hruZeros = "00"
        elif ((hruIdx >= 100) and (hruIdx < 1000)):
            hruZeros = "0"
        elif (hruIdx > 1000):
            hruZeros = ""

        fnSWATHru = "{}{}{}".format(subPrefix, hruZeros, hruIdx)
        fnSWATHruLst.append(fnSWATHru)

    return fnSWATHruLst


##########################################################################
def current_time():

    now = datetime.datetime.now(GlobalVars.time_zone)
    strtime = now.strftime('%Y-%m-%d %H:%M:%S')

    return strtime


##########################################################################
def get_osplatform():

    platforms = {
        'linux1' : 'Linux',
        'linux2' : 'Linux',
        'darwin' : 'OS X',
        'win32' : 'Windows'
    }
    if sys.platform not in platforms:
        return sys.platform

    return platforms[sys.platform]


##########################################################################
def runSWATModel(os_platform,
                 proj_path,
                 running_folder,
                 path_src_swat_exe,
                 pipe_process_to_gui):
    """
    This function change the directory to the apex run folder,
    run apex, and change back.
    TODO: Add the swat2012 linux into the package folder
    and copy it to the working directory.
    """
    workingdir = os.path.join(proj_path, running_folder)

    # Copy the swat exe to the working Dir
    fname_swat_exe = os.path.split(path_src_swat_exe)[1]
    path_dest_swat_exe = os.path.join(workingdir,
                    fname_swat_exe)
    try:
        copyfile(path_src_swat_exe, path_dest_swat_exe)
    except:
        showinfo("Warning", "Could not copy SWAT executable to the working directory!")
        return

    os.chdir(workingdir)

    if os_platform == "linux":
        proc_command = "./{}".format(fname_swat_exe)
    elif os_platform == "Windows":
        proc_command = "{}".format(fname_swat_exe)

    ## call date command ##
    # I tried Popen and run. Run does not work since it need to
    # wait for the termination of run_networked.
    try:
        p = subprocess.Popen(proc_command,
                           shell=True,
                           stderr=subprocess.PIPE,
                           stdout = subprocess.PIPE,
                           universal_newlines=True)

        # # Change back to the fdworking folder
        # print('process created with pid: {}'.format(p.pid))
        ## But do not wait till netstat finish, start displaying output immediately ##
        # So, this is while the process is true, keep sending output
        while True:
            out = p.stdout.readline()
            if out == '' and p.poll() != None:
                break
            if out != '':
                pipe_process_to_gui.send("{}".format(out))
                # Print actuall cass the sys.stdout.write function.
                # sys.stdout.write(out)
                # sys.stdout.flush()

        p.wait()
        if p.returncode == 0:
            sendinfo = "Process: finished running swat"
            pipe_process_to_gui.send("{}".format(sendinfo))

        os.chdir(proj_path)

    except:
        sendinfo = "SWAT run failed, please check"
        pipe_process_to_gui.send("{}".format(sendinfo))


##########################################################################
def getRch2DF(fnRch, iPrintForCio, totalRchNum):
    # Read output.rch into pandas dataframe
    # Original header
    # hedr = ["RCH","GIS", "MON","AREAkm2",
    #         "FLOW_OUTcms", " SED_OUTtons", "ORGN_OUTkg",
    #         "ORGP_OUTkg", "NO3_OUTkg", "NH4_OUTkg",
    #         "NO2_OUTkg", "MINP_OUTkg", "SOLPST_OUTmg",
    #         "SORPST_OUTmg"]

    # Corresponding heads used in the observed data
    # facilitating the extraction of output variables.
    hedr = ["REACH", "RCH", "GIS", "MON", "AREAkm2",
            "sf(m3/s)", "sed(t/ha)", "orgn(kg/ha)",
            "orgp(kg/ha)", "no3n(kg/ha)", "nh4n(kg/ha)",
            "no2n(kg/ha)", "minp(kg/ha)", "solpst(mg/ha)",
            "sorpst(mg/ha)"]

    # ffRchDataLnRdr = ff.FortranRecordReader('(A5,1X,I5,1X,I8,1X,I3,I3,I5,3X,11E12.4)')
    # fidRch = open(fnRch, "r")
    # lifRch = fidRch.readlines()
    # fidRch.close()
    # del(lifRch[:9])

    # Version 1: normal serial for loop
    # for idx in range(len(lifRch)):
    #     # print(lifRch[idx])
    #     lifRch[idx] = ffRchDataLnRdr.read(lifRch[idx])[1:]

    # Version 2: use pandas read_fwf
    # rchDF = pandas.read_fwf(fnRch, colspecs='infer', skiprows=8)

    # Based on the value of iPrintForCio, the format are different
    # When iPrintForCio == 0, for month and iPrintForCio == 2 for annual,
    # The output.rch will include lines for annual sum and year average for
    # each rch.
    # When iPrintForCio == 1 for daily, these does not exist
    colWidth = [5, 6, 9, 6] + [12] * 11
    if (iPrintForCio == "monthly") or (iPrintForCio == "annual"):
        rchDF = pandas.read_fwf(fnRch, widths=colWidth, skiprows=9, names=hedr, skipfooter=totalRchNum)
        rchDF = rchDF.loc[rchDF["MON"] < 13]
    else:
        rchDF = pandas.read_fwf(fnRch, widths=colWidth, skiprows=9, names=hedr)
        rchDF = rchDF.loc[rchDF["MON"] < 400.0]

    # Remove the lines that

    return rchDF


##########################################################################
def buildObsSimPair(all_outlet_detail,
                     dataframe_outrch_whole,
                     pair_varid_obs_header,
                    cali_options):
    """
    This function read the data from simDF and add corresponding columns
    into the obsDict.
    """
    sim_start_date_str = cali_options["simstartdate"].split("/")
    sim_end_date_str = cali_options["simenddate"].split("/")

    # Construct daily, monthly and annual time series.
    sim_real_start_date = pandas.Timestamp(
            year=int(sim_start_date_str[2]) + int(cali_options["warmupyrs"]),
            month=int(sim_start_date_str[0]),
            day=int(sim_start_date_str[1]))

    sim_end_date = pandas.Timestamp(
            year=int(sim_end_date_str[2]),
            month=int(sim_end_date_str[0]),
            day=int(sim_end_date_str[1]))

    sim_mon_range = pandas.date_range(sim_real_start_date,
                                        sim_end_date,
                                        freq='M')
    sim_daily_range = pandas.date_range(sim_real_start_date,
                                        sim_end_date,
                                        freq='D')
    sim_year_range = pandas.date_range(sim_real_start_date,
                                        sim_end_date,
                                        freq='Y')

    for outlet_key, outlet_detail in all_outlet_detail.items():
        if not outlet_detail["outletid"] == "not_grouped_subareas":
            outlet_id = int(outlet_detail["outletid"])
            variable_id = outlet_detail["variableid"]
            variable_header = pair_varid_obs_header[variable_id]
            outlet_rch_header = ["RCH", "GIS", "MON", "AREAkm2"] + [variable_header]
            outlet_rch_rows = dataframe_outrch_whole.loc[
                dataframe_outrch_whole["RCH"] == outlet_id][outlet_rch_header]

            # Add a time series for better matching with observed data
            if cali_options["iprint"] == "monthly":
                outlet_rch_rows["Date"] = sim_mon_range
            elif cali_options["iprint"] == "daily":
                outlet_rch_rows["Date"] = sim_daily_range
            elif cali_options["iprint"] == "annual":
                outlet_rch_rows["Date"] = sim_year_range
            # Combine the two pair based on dates
            outlet_detail["df_obs_sim"] = outlet_detail["df_obs"].merge(
                outlet_rch_rows, how="left", left_on="Date", right_on="Date", copy=True)

    return all_outlet_detail


##########################################################################
def calAllStatEachOlt(all_outlet_detail,
                      pair_varid_obs_header):
    """
    This function calculate the average objective function values over
    the objective function for all variables across all time frequencies.
    Users might specify different objective function values for
    different variables. This tool offer this feature.
    While calculating, the selected objective function for each
    variable will be calculated.
    """
    for outlet_key, outlet_detail in all_outlet_detail.items():
        # In the code, the objective function values for each outlet will
        # be calculated, and the "Other" group will be dealt as a special calse.
        # A var to store the value of statistics of all non other sub groups.
        # In order to calculate the average value of the average OBJ and
        # provide reference for the other groups.
        if not outlet_detail["outletid"] == "not_grouped_subareas":
            variable_id = outlet_detail["variableid"]
            variable_header = pair_varid_obs_header[variable_id]
            obsTS_orig = list(outlet_detail["df_obs_sim"]["{}_x".format(variable_header)])
            simTS_orig = list(outlet_detail["df_obs_sim"]["{}_y".format(variable_header)])

            # Updated Nov 25, 2022 by Qingyu Feng
            # Missing values in obs files are marked by -99 and will be removed when
            # statistics is calculated
            obsTS = []
            simTS = []

            for obsidx in range(len(obsTS_orig)):
                obs_val = obsTS_orig[obsidx]
                if not int(obs_val) == -99:
                    obsTS.append(obs_val)
                    simTS.append(simTS_orig[obsidx])

            obsTS = list(map(float, obsTS))
            obsTSMean = sum(obsTS) / len(obsTS)
            simTS = list(map(float, simTS))
            simTSMean = sum(simTS) / len(simTS)
            obs_array = numpy.array(obsTS)
            obs_std = numpy.std(obs_array)

            # Sum of errors above
            sumErrObSm = 0.0
            sumSqErrObSm = 0.0
            sumSqErrObs = 0.0
            sumSqErrSim = 0.0
            sumProdErrObSm = 0.0

            PBIAS = 100.0
            NSE = -99.0
            RMSE = 100.0
            R2 = 0.01
            MSE = 100.0
            RSR = 100.0

            for tsidx in range(len(obsTS)):
                # IPEATPlus Error: error between OBS(i) and SIM(i)
                errObSm = 0.0
                # IPEATPlus error2: square of error between OBS(i) and SIM(i)
                sqErrObSm = 0.0
                # IPEATPlus errorI2: square of the error between OBS(i) and OBS(mean)
                sqErrObs = 0.0
                # IPEATPlus errorO2: square of the error between SIM(i) and SIM(mean)
                sqErrSim = 0.0
                # IPEATPlus errorR2: product of OBS(i) error -mean and SIM(i) error - mean
                prodErrObSm = 0.0

                errObSm = simTS[tsidx] - obsTS[tsidx]
                sqErrObSm = errObSm ** 2
                sqErrObs = (obsTS[tsidx] - obsTSMean) ** 2
                sqErrSim = (simTS[tsidx] - simTSMean) ** 2
                prodErrObSm = (obsTS[tsidx] - obsTSMean) * (simTS[tsidx] - simTSMean)

                sumErrObSm = sumErrObSm + errObSm
                sumSqErrObSm = sumSqErrObSm + sqErrObSm
                sumSqErrObs = sumSqErrObs + sqErrObs
                sumSqErrSim = sumSqErrSim + sqErrSim
                sumProdErrObSm = sumProdErrObSm + prodErrObSm

            # Added by Qingyu Feng Mar 26, 2021
            # This modification was done to prevent potential errors of
            # division by zero. It was found that simulated flow were all 0s
            # and this will cause error. It is very rare but still happened.
            # Calculate R2
            # R2 = sum((obs-obsmean)(sim-simMean)**2)/sum((obs-obsmean)**2)*sum((sim-simMean)**2)
            # R2 ranges from 0 to 1
            if (sumSqErrObs != 0.0) and (sumSqErrSim != 0):
                R2 = (sumProdErrObSm ** 2) / (sumSqErrObs * sumSqErrSim)
            elif (sumSqErrObs == 0.0) and (sumSqErrSim == 0) and pandas.isnull(R2):
                R2 = 0.01

            # Pbias = 100 * sum(obs-sim)/sum(obs) by Danial Moriasi et al., 2007
            # This is also the equation used in
            # https://www.rdocumentation.org/packages/hydroGOF/versions/0.4-0/topics/pbias
            # Pbias = 100 * sum(sim-obs)/sum(obs)
            # PBias ranges from 0 to infinity
            if obsTSMean == 0.0:
                PBIAS = 100.0
            else:
                PBIAS = 10 * sumErrObSm / sum(obsTS)
                # Deal with the display issue
                if PBIAS > 100.0:
                    PBIAS = 100.0
                elif (PBIAS < -100.0) or pandas.isnull(PBIAS):
                    PBIAS = -100.0

            # NSE = 1 - sum((obs-sim) ^ 2)/sum((obs-obsmean) ^ 2)
            # NSE ranges from minus infinity to 1
            if sumSqErrObs == 0.0:
                NSE = -99.0
            else:
                NSE = 1 - (sumSqErrObSm / sumSqErrObs)
                # minor adjustments for printing outputs
                if NSE <= -99.0 or pandas.isnull(NSE):
                    NSE = -99.0

            # RMSE = sqrt(sum(obs-sim) ^ 2)
            # RSR = RMSE/obs_std
            if len(obsTS) == 0:
                RMSE = 100.0
                MSE = 100.0
            else:
                RMSE = math.sqrt(sumSqErrObSm / len(obsTS))
                MSE = sumSqErrObSm / len(obsTS)
                RSR = RMSE/obs_std
                # Deal with the display issue
                if RMSE > 100.0 or pandas.isnull(RMSE):
                    RMSE = 100.0

                if RSR > 100.0 or pandas.isnull(RSR):
                    RSR = 100.0

                # Deal with the display issue
                if MSE > 100.0 or pandas.isnull(MSE):
                    MSE = 100.0

            # Added by Qingyu Feng Nov 26, 2022
            # The sklearn is not used because r2 calculated by sklearn is
            # not the normal r2.
            # r2_sklearn = r2_score(obsTS, simTS)
            # mse_sklearn = mean_squared_error(obsTS, simTS, squared=True)
            # rmse_sklearn = mean_squared_error(obsTS, simTS, squared=False)

            outlet_detail["pbias_value"] = PBIAS
            outlet_detail["nse_value"] = NSE
            outlet_detail["rmse_value"] = RMSE
            outlet_detail["r2_value"] = R2
            outlet_detail["mse_value"] = MSE
            outlet_detail["rsr_value"] = RSR

    return all_outlet_detail


##########################################################################
def calOltBsnFunValue(all_outlet_detail,
                      basin_test_objfun_val):
    """
    This function calculates the objective function value for basin
    based on objective function values of each outlet.
    It will be used for both not_grouped_subareas in the distributed
    mode and the overall parameter in the lumped mode.
    """

    basin_test_objfun_val = 0.0
    sum_oltvar_weights = 0.0
    # First calculate the objectives for user required outlets.
    for outlet_key1, outlet_detail1 in all_outlet_detail.items():
        # In the code, the objective function values for each outlet will
        # be calculated, and the "Other" group will be dealt as a special calse.
        # A var to store the value of statistics of all non other sub groups.
        # In order to calculate the average value of the average OBJ and
        # provide reference for the other groups.
        if not outlet_detail1["outletid"] == "not_grouped_subareas":
            sum_oltvar_weights = sum_oltvar_weights + float(outlet_detail1["varweight"])

    # First calculate the objectives for user required outlets.
    for outlet_key, outlet_detail in all_outlet_detail.items():
        # In the code, the objective function values for each outlet will
        # be calculated, and the "Other" group will be dealt as a special calse.
        # A var to store the value of statistics of all non other sub groups.
        # In order to calculate the average value of the average OBJ and
        # provide reference for the other groups.
        if not outlet_detail["outletid"] == "not_grouped_subareas":
            # print(float(outlet_detail["varweight"]), float(outlet_detail["varweight"])/sum_oltvar_weights, )
            basin_test_objfun_val = basin_test_objfun_val + float(outlet_detail["test_obj_dist"]
                            ) * (float(outlet_detail["varweight"])/sum_oltvar_weights)

    return basin_test_objfun_val



##########################################################################
def calOltObjFunValue(all_outlet_detail):
    """
    This function calculates the objective function value for each outlet
    based on the user specified and weights.
    """
    # First calculate the objectives for user required outlets.
    for outlet_key, outlet_detail in all_outlet_detail.items():
        # In the code, the objective function values for each outlet will
        # be calculated, and the "Other" group will be dealt as a special calse.
        # A var to store the value of statistics of all non other sub groups.
        # In order to calculate the average value of the average OBJ and
        # provide reference for the other groups.
        if not outlet_detail["outletid"] == "not_grouped_subareas":
            # Determine the stat value used as objective function
            obj_outlet = 0.0
            # The weight does not need to be 0 to 1, they are just relative.
            # So, they need to be standardized before being used.
            all_weights = {"r2_weight": float(outlet_detail["r2_weight"]),
                           "nse_weight": float(outlet_detail["nse_weight"]),
                            "pbias_weight": float(outlet_detail["pbias_weight"]),
                            "mse_weight": float(outlet_detail["mse_weight"]),
                            "rmse_weight": float(outlet_detail["rmse_weight"])}

            # Updated by Qingyu Feng Dec 7:
            # The old ways of calculating standardized weight was wrong.
            # I will use the weight/sum as the actual weights.
            sum_all_weights = 0.0
            # Only calculate those selected

            # A statistic to mark the necessity to standardize statistics
            # if only 1 statistic is selected, the original value
            # will be used as objective function.
            # If more than 1 statistic is selected, the values will be
            # standardized.
            no_statistic = 0

            if outlet_detail["r2_select"] == "1":
                sum_all_weights = sum_all_weights + all_weights["r2_weight"]
                no_statistic = no_statistic + 1
                # obj_outlet + float(outlet_detail["r2_value"]) * std_weights["r2_weight"]
            if outlet_detail["nse_select"] == "1":
                sum_all_weights = sum_all_weights + all_weights["nse_weight"]
                no_statistic = no_statistic + 1
            if outlet_detail["pbias_select"] == "1":
                sum_all_weights = sum_all_weights + all_weights["pbias_weight"]
                no_statistic = no_statistic + 1
            if outlet_detail["mse_select"] == "1":
                sum_all_weights = sum_all_weights + all_weights["mse_weight"]
                no_statistic = no_statistic + 1
            if outlet_detail["rmse_select"] == "1":
                sum_all_weights = sum_all_weights + all_weights["rmse_weight"]
                no_statistic = no_statistic + 1
            # Updated by Qingyu Feng Dec 7

            # std_weights = copy.deepcopy(all_weights)
            # if not weight_min == weight_max:
            #     weight_range = weight_max - weight_min
            #
            #     # X’ = (X - Xmin) / (Xmax - Xmin)
            #     for wkey, wvalue in all_weights.items():
            #         # Standardize the weight to get relative weights
            #         new_weight = (all_weights[wkey] - weight_min)/weight_range
            #         std_weights[wkey] = new_weight

            # The NSE values will be 1 - nse

            # R2 range: 0 to 1
            # PBIAS, MSE, RMSE range: 0 to inf.
            # NSE Range -inf to 1
            # In order to reduce the difference in these
            # statistics, they need to be standardized if more than one
            # variable is selected.

            one_minus_nse = 1.0 - float(outlet_detail["nse_value"])
            one_minus_r2 = 1.0 - float(outlet_detail["r2_value"])

            if outlet_detail["r2_select"] == "1":
                if no_statistic == 1:
                    obj_outlet = one_minus_r2
                elif no_statistic > 1:
                    # R2 do not need to be standardized as it ranges from
                    # 0 to 1
                    obj_outlet = obj_outlet + one_minus_r2 * (all_weights["r2_weight"]/sum_all_weights)
                    # obj_outlet + float(outlet_detail["r2_value"]) * std_weights["r2_weight"]

                    print("Outlet ID: {} R2: {}, {}, {}, {}".format(outlet_detail["outletid"],
                                                                    float(outlet_detail["r2_value"]),
                                                                    one_minus_r2,
                                                                    all_weights["r2_weight"] / sum_all_weights,
                                                                    all_weights["r2_weight"]))

            if outlet_detail["nse_select"] == "1":
                if no_statistic == 1:
                    obj_outlet = one_minus_nse
                elif no_statistic > 1:
                    # NSE not need to be standardized as it ranges from
                    # -inf to 1. We restricted it to be ranged from -99 to 1
                    # X’ = (X-Xmin) / (Xmax-Xmin)
                    # nse_standardized = (X - -99) / (1 - -99)
                    # nse_standardized_minus99_ = 0 / 100 = 0
                    # nse_standardized_1 = 100 / 100 = 1
                    # nse increased from -99 to 1,  nse_standardized increased from 0 to 1
                    # if nse = 0.2: nse_standardized = 0.992
                    # if nse = 0.3: nse_standardized = 0.993
                    # To maximize nse, it need to be 1-nse_standardized to minimize it.
                    nse_sandardized = (float(outlet_detail["nse_value"]) + 99.0) / (1.0 + 99.0)
                    one_minus_nse_sandardized = 1.0 - nse_sandardized
                    obj_outlet = obj_outlet + one_minus_nse_sandardized * (
                            all_weights["nse_weight"]/sum_all_weights)

                    print("Outlet ID: {} NSE: {}, {}, {}, {}".format(outlet_detail["outletid"],
                                                                     float(outlet_detail["nse_value"]),
                                                                     nse_sandardized,
                                                                     all_weights["nse_weight"],
                                                                     all_weights["nse_weight"] / sum_all_weights))

            if outlet_detail["pbias_select"] == "1":
                if no_statistic == 1:
                    obj_outlet = abs(float(outlet_detail["pbias_value"]))
                elif no_statistic > 1:
                    # PBias not need to be standardized as it ranges from
                    # 0 to inf. We restricted it to be ranged from 0 to 100
                    # pbias_standardized = (X - 0) / (100 - 0)
                    # pbias_standardized_100 = 100 / 100 = 1
                    # pbias_standardized_0 = 0 / 100 = 0
                    # pbias increased from 0 to 100,  pbias_standardized increased from 0 to 1
                    # if pbias = 2: pbias_standardized = 0.02
                    # if pbias = 3: pbias_standardized = 0.03
                    # To minimize pbias, it need to be pbias_standardized to minimize it.
                    pbias_sandardized = abs(float(outlet_detail["pbias_value"])) / (100.0 - 0.0)
                    obj_outlet = obj_outlet + pbias_sandardized * (
                            all_weights["pbias_weight"]/sum_all_weights)

                    print("Outlet ID: {} PBIAS: {}, {}, {}, {}".format(outlet_detail["outletid"],
                                                           float(outlet_detail["pbias_value"]),
                                                           pbias_sandardized,
                                                           all_weights["pbias_weight"],
                                                           all_weights["pbias_weight"] / sum_all_weights))

            if outlet_detail["mse_select"] == "1":
                if no_statistic == 1:
                    obj_outlet = float(outlet_detail["mse_value"])
                elif no_statistic > 1:
                    # mse not need to be standardized as it ranges from
                    # 0 to inf. We restricted it to be ranged from 0 to 100
                    # mse_standardized = (X - 0) / (100 - 0)
                    # mse_standardized_100 = 100 / 100 = 1
                    # mse_standardized_0 = 0 / 100 = 0
                    # mse increased from 0 to 100, mse_standardized increased from 0 to 1
                    # if mse = 2: mse_standardized = 0.02
                    # if mse = 3: mse_standardized = 0.03
                    # To minimize mse, it need to be mse_standardized to minimize it.
                    mse_sandardized = float(outlet_detail["mse_value"]) / (100.0 - 0.0)
                    obj_outlet = obj_outlet + mse_sandardized * (
                            all_weights["mse_weight"]/sum_all_weights)

                    print("Outlet ID: {} MSE: {}, {}, {}, {}".format(outlet_detail["outletid"],
                                                         float(outlet_detail["mse_value"]),
                                                         mse_sandardized,
                                                         all_weights["mse_weight"],
                                                         all_weights["mse_weight"] / sum_all_weights))


            if outlet_detail["rmse_select"] == "1":
                if no_statistic == 1:
                    obj_outlet = float(outlet_detail["rmse_value"])
                elif no_statistic > 1:
                    # rmse not need to be standardized as it ranges from
                    # 0 to inf. We restricted it to be ranged from 0 to 100
                    # rmse_standardized = (X - 0) / (100 - 0)
                    # rmse_standardized_100 = 100 / 100 = 1
                    # rmse_standardized_0 = 0 / 100 = 0
                    # rmse increased from 0 to 100, rmse_standardized increased from 0 to 1
                    # if rmse = 2: rmse_standardized = 0.02
                    # if rmse = 3: rmse_standardized = 0.03
                    # To minimize rmse, it need to be rmse_standardized to minimize it.
                    rmse_sandardized = float(outlet_detail["rmse_value"]) / (100.0 - 0.0)
                    obj_outlet = obj_outlet + rmse_sandardized * (
                            all_weights["rmse_weight"]/sum_all_weights)

                    print("Outlet ID: {} RMSE: {}, {}, {}, {}".format(outlet_detail["outletid"],
                                                                  float(outlet_detail["rmse_value"]),
                                                                  rmse_sandardized,
                                                                  all_weights["rmse_weight"],
                                                                  all_weights["rmse_weight"] / sum_all_weights))

            print(sum_all_weights)
            print("Outlet ID: {} RSR: {}".format(outlet_detail["outletid"],
                                                 float(outlet_detail["rsr_value"])))
            print("Outlet ID: {} obj: {}".format(outlet_detail["outletid"], obj_outlet))

            outlet_detail["test_obj_dist"] = obj_outlet

    return all_outlet_detail


##########################################################################
def updateFileCio(cali_options,
                  proj_path,
                  running_folder,
                  reach_var_list):
    """
    This function modify the file.cio file based on the user input.
    These include:
    1. IPRINT need to specified for output.rch file
    2. start and end date
    3. number of skip years.
    4. output variable in the output.rch file to meet the requirement of
    different variables specified in for calibration.
    """

    # Determin NBYR, IYR, IDFA, and IDAL
    sim_start_date_str = cali_options["simstartdate"].split("/")

    sim_start_date_str = [int(val) for val in sim_start_date_str]

    sim_end_date_str = cali_options["simenddate"].split("/")
    sim_end_date_str = [int(val) for val in sim_end_date_str]
    usrStartJD = datetime.date(sim_start_date_str[2],
                               sim_start_date_str[0],
                               sim_start_date_str[1]).timetuple().tm_yday

    usrEndJD = datetime.date(sim_end_date_str[2],
                               sim_end_date_str[0],
                               sim_end_date_str[1]).timetuple().tm_yday

    firstJDStartYr = datetime.date(sim_start_date_str[2],
                                   1, 1).timetuple().tm_yday
    lastJDEndYr = datetime.date(sim_end_date_str[2],
                                1, 1).timetuple().tm_yday

    NBYR = sim_end_date_str[2] - sim_start_date_str[2] + 1
    IYR = sim_start_date_str[2]
    IDAF = usrStartJD - firstJDStartYr + 1
    IDAL = usrEndJD - lastJDEndYr + 1

    # Readin file.cio, modify and write new values.
    fname_file_cio = os.path.join(proj_path, running_folder, "file.cio")

    try:
        with open(fname_file_cio, 'r') as swatFile:
            lif = swatFile.readlines()
    except IOError as e:
        print("""File {} does not exist: {}. Please double check your TxtInOut \
            folder and make sure you have a complete set""".format(fname_file_cio, e))


    for lidx in range(len(lif)):
        # Line 8 for parameter NBYR
        if (lidx == 7):
            lif[lidx] = """{:16d}    | NBYR : Number of years simulated\n""".format(
                NBYR)

        # Line 9 for parameter IYR
        if (lidx == 8):
            lif[lidx] = """{:16d}    | IYR : Beginning year of simulation\n""".format(
                IYR)

        # Line 10 for parameter IDAF
        if (lidx == 9):
            lif[lidx] = """{:16d}    | IDAF : Beginning julian day of simulation\n""".format(
                IDAF)

        # Line 11 for parameter IDAL
        if (lidx == 10):
            lif[lidx] = """{:16d}    | IDAL : Ending julian day of simulation\n""".format(
                IDAL)

        # Line 59 for parameter IPRINT
        if cali_options["iprint"] == "daily":
            iprint = 1
        elif cali_options["iprint"] == "monthly":
            iprint = 0
        elif cali_options["iprint"] == "annual":
            iprint = 2

        if (lidx == 58):
            lif[lidx] = """{:16d}    | IPRINT : print code (month, day, year)\n""".format(
                iprint)

        # Line 60 for parameter NYSKIP
        if (lidx == 59):
            lif[lidx] = """{:16d}    | NYSKIP : number of years to skip output printing\n""".format(
                int(cali_options["warmupyrs"]))

        # Line 65 for parameter out variable in Rch
        if (lidx == 64):
            # Construct out variable lines 4 spacex * 20 var
            lineForWrite = reach_var_list + [0] * (20 - len(reach_var_list))
            lineForWrite = "".join(["{:4d}".format(varRch) for varRch in lineForWrite])
            lif[lidx] = """{}\n""".format(lineForWrite)

        # Line 67 for parameter out variable in subbasin
        if (lidx == 66):
            # Construct out variable lines 4 spacex * 20 var
            lif[lidx] = """   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0\n"""

        # Line 69 for parameter out variable in HRU
        if (lidx == 68):
            # Construct out variable lines 4 spacex * 20 var
            lif[lidx] = """   1   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0\n"""

        # Line 71 for parameter out variable in HRU
        if (lidx == 70):
            # Construct out variable lines 4 spacex * 20 var
            lif[lidx] = """   1   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0\n"""

        # Line 79 for parameter IA_B
        if (lidx == 78):
            lif[lidx] = """{:16d}    | IA_B : Code for binary output of files (.rch, .sub, .hru files only)\n""".format(
                1)

        # Line 85 for parameter ICALEN, 1 for y/m/d
        if (lidx == 84):
            lif[
                lidx] = """{:16d}    | ICALEN: Code for printing out calendar or julian dates to .rch, .sub and .hru files\n""".format(
                0)

    # Then write the contents into the same file
    with open(fname_file_cio, 'w') as swatFile:
        swatFile.writelines(lif)


##########################################################################
def addSubareaGroups(cali_mode,
                    all_outlet_detail,
                    subarea_groups):
    """
    This function add the grouped subarea list to the
    outlet details based on calibration model.
    If the user selected using the distributed mode, the subarea group will be
    added to the corresponding outlet.
    If the user selected to use the lumped mode, the subarea groups of
    no grouping will be added.
    """
    first_key = list(all_outlet_detail.keys())[0]
    if cali_mode == "dist":
        # Get Groups of the watershed
        for ovid, outlet_detail in all_outlet_detail.items():
            outletid = outlet_detail["outletid"]
            outlet_detail["subarea_list"] = subarea_groups[outletid]
        if "not_grouped_subareas" in subarea_groups.keys():
            all_outlet_detail["not_grouped_subareas"] = copy.deepcopy(
                all_outlet_detail[first_key])
            all_outlet_detail["not_grouped_subareas"][
                "subarea_list"] = subarea_groups["not_grouped_subareas"]
            all_outlet_detail["not_grouped_subareas"]["outletid"] = "not_grouped_subareas"
    # In the lump mode, the outlet id do not get its subarea list since they were not
    # generated in the generateSubareaGroup step.
    elif cali_mode == "lump":
        all_outlet_detail["not_grouped_subareas"] = copy.deepcopy(all_outlet_detail[first_key])
        all_outlet_detail["not_grouped_subareas"][
            "subarea_list"] = subarea_groups["not_grouped_subareas"]
        all_outlet_detail["not_grouped_subareas"]["outletid"] = "not_grouped_subareas"

    return all_outlet_detail


##########################################################################
def generateRandomParmValue(parDF,
                            ranNum):
    """
    This function calculates the random values for initial runs.
    """
    # print("Random value for ranNum in updating parameters:　{}".format(ranNum))
    # ranNum = [random.random() for i in range(len(parDF.index))]
    parDF["ModThisRun"] = [0] * len(parDF["TestVal"])
    parDF["TestVal"] = parDF["LowerBound"] + ranNum[0] * (parDF["UpperBound"] - parDF["LowerBound"])
    parDF["ModThisRun"] = [1] * len(parDF["TestVal"])

    return parDF


##########################################################################
def modifyParInFileSub(proj_path,
                        fdname_running,
                       sub_level_fname_for_groups,
                       hru_level_fname_for_groups,
                       parm_sub_group,
                       outlet_subgroup_id,
                       pipe_process_to_gui
                       ):
    """
    This function modify parameter values in corresponding swat input files.
    """
    file_extension_list = parm_sub_group["File"].unique()

    for file_ext in file_extension_list:
        # Get the list of parameters in a certain file
        selected_parms_in_file = parm_sub_group.loc[parm_sub_group["File"] == file_ext]

        # Update subarea level files
        # subLvlFlExtLst = [".sub", ".rte", ".swq"]
        if file_ext == ".sub":
            pip_info_send = """Process: Updating .sub files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            for fname_swat_sublevel in sub_level_fname_for_groups[outlet_subgroup_id]:
                SwatUtil.updateParInSub(
                    fname_swat_sublevel,
                    selected_parms_in_file,
                    proj_path,
                    fdname_running
                )
        elif file_ext == ".rte":
            pip_info_send = """Process: Updating .rte files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            for fname_swat_sublevel in sub_level_fname_for_groups[outlet_subgroup_id]:
                SwatUtil.updateParInRte(
                    fname_swat_sublevel,
                    selected_parms_in_file,
                    proj_path,
                    fdname_running
                )
        elif file_ext == ".swq":
            pip_info_send = """Process: Updating .swq files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            for fname_swat_sublevel in sub_level_fname_for_groups[outlet_subgroup_id]:
                SwatUtil.updateParInSwq(
                    fname_swat_sublevel,
                    selected_parms_in_file,
                    proj_path,
                    fdname_running
                )

        # TODO: Add parameters for reservoir
        # elif file_ext == ".res":
        #     for fname_swat_sublevel in sub_level_fname_for_groups[outlet_subgroup_id]:
        #         SwatUtil.updateParInRes(fname_swat_sublevel, selected_parms_in_file, proj_path)

        # Start processing HRU level files
        # hruLvlFlExtLst = [".gw", ".hru", ".mgt", ".sol", ".chm"]
        elif file_ext == ".gw":
            pip_info_send = """Process: Updating .gw files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            for fname_swat_sublevel in hru_level_fname_for_groups[outlet_subgroup_id]:

                SwatUtil.updateParInGw(
                    fname_swat_sublevel,
                    selected_parms_in_file,
                    proj_path,
                    fdname_running
                )
        elif file_ext == ".hru":
            pip_info_send = """Process: Updating .hru files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            for fname_swat_sublevel in hru_level_fname_for_groups[outlet_subgroup_id]:
                SwatUtil.updateParInHru(
                    fname_swat_sublevel,
                    selected_parms_in_file,
                    proj_path,
                    fdname_running
                )
        elif file_ext == ".mgt":
            pip_info_send = """Process: Updating .mgt files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            for fname_swat_sublevel in hru_level_fname_for_groups[outlet_subgroup_id]:
                SwatUtil.updateParInMgt(
                    fname_swat_sublevel,
                    selected_parms_in_file,
                    proj_path,
                    fdname_running,
                    GlobalVars.row_crop_list)
        elif file_ext == ".chm":
            pip_info_send = """Process: Updating .chm files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            for fname_swat_sublevel in hru_level_fname_for_groups[outlet_subgroup_id]:
                SwatUtil.updateParInChm(
                    fname_swat_sublevel,
                    selected_parms_in_file,
                    proj_path,
                    fdname_running
                )
        elif file_ext == ".sol":
            pip_info_send = """Process: Updating .sol files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            for fname_swat_sublevel in hru_level_fname_for_groups[outlet_subgroup_id]:
                SwatUtil.updateParInSol(
                    fname_swat_sublevel,
                    selected_parms_in_file,
                    proj_path,
                    fdname_running
                )

        # End of for loop updating subarea and hru level parameters parameters


##########################################################################
def modifyParInFileBsn(parm_basin_level,
                       proj_path,
                       fdname_running,
                       pipe_process_to_gui):
    """
    This function modify parameter values in files at the basin level.
    """
    # They use different file names.
    file_extension_list = parm_basin_level["File"].unique()

    for file_ext in file_extension_list:
        # Get the list of parameters in a certain file
        selected_parms_in_file = parm_basin_level.loc[parm_basin_level["File"] == file_ext]

        if file_ext == ".bsn":
            pip_info_send = """Process: Updating .bsn files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            SwatUtil.updateParInBsn(
                selected_parms_in_file,
                proj_path,
                fdname_running
            )
        elif file_ext == "crop.dat":
            pip_info_send = """Process: Updating plant.dat files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            SwatUtil.updateParInCrop(
                selected_parms_in_file,
                proj_path,
                fdname_running
            )
        elif file_ext == ".wwq":
            pip_info_send = """Process: Updating .wwq files"""
            pipe_process_to_gui.send("{}".format(pip_info_send))
            SwatUtil.updateParInWwq(
                selected_parms_in_file,
                proj_path,
                fdname_running
            )


##########################################################################
def updateBestParmSubAndBasin(
        runIdx,
        all_outlet_detail,
        basin_obj_func_values,
        cali_mode,
        pair_varid_obs_header,
        parm_basin_level,
        sub_parm_value_outfn,
        sub_objfun_outfn,
        sub_parm_select_outfn,
        bsn_parm_value_fn,
        bsn_parm_sel_fn,
        bsn_obj_fn,
        probability_value,
        pipe_process_to_gui):
    """
    This function update the best to test parameters based on the objective function
    values.
    """
    # For each outlet_variable combination, the difference between the lump and
    # dist mode is the way how parameter is updated and which objective function is used.
    # Besides, the way how not_grouped_subareas is processed in different ways.
    for ovid, outlet_detail in all_outlet_detail.items():
        variable_id = outlet_detail["variableid"]
        variable_header = pair_varid_obs_header[variable_id]

        if outlet_detail["outletid"] != "not_grouped_subareas":
            # Display the objective function values
            pip_info_send = """Current NSE value and weight for outlet {} var {} are {:.3f}""".format(
                outlet_detail["outletid"],
                variable_header,
                float(outlet_detail["nse_value"]))
            pipe_process_to_gui.send("{}".format(pip_info_send))

            pip_info_send = """Current R2 value and weight for outlet {} var {} are {:.3f}""".format(
                outlet_detail["outletid"],
                variable_header,
                float(outlet_detail["r2_value"]))
            pipe_process_to_gui.send("{}".format(pip_info_send))

            pip_info_send = """Current PBIAS value and weight for outlet {} var {} are {:.3f}""".format(
                outlet_detail["outletid"],
                variable_header,
                float(outlet_detail["pbias_value"]))
            pipe_process_to_gui.send("{}".format(pip_info_send))

            pip_info_send = """Current MSE value and weight for outlet {} var {} are {:.3f}""".format(
                outlet_detail["outletid"],
                variable_header,
                float(outlet_detail["mse_value"]))
            pipe_process_to_gui.send("{}".format(pip_info_send))

            pip_info_send = """Current RMSE value and weight for outlet {} var {} are {:.3f}""".format(
                outlet_detail["outletid"],
                variable_header,
                float(outlet_detail["rmse_value"]))
            pipe_process_to_gui.send("{}".format(pip_info_send))

            pip_info_send = """Current RSR value and weight for outlet {} var {} are {:.3f}""".format(
                outlet_detail["outletid"],
                variable_header,
                float(outlet_detail["rsr_value"]))
            pipe_process_to_gui.send("{}".format(pip_info_send))

            pip_info_send = """Current and best objective function value for outlet {} var {} are {:.6f}, {:.6f}""".format(
                outlet_detail["outletid"],
                variable_header,
                float(outlet_detail["test_obj_dist"]),
                float(outlet_detail["best_obj_dist"]))
            pipe_process_to_gui.send("{}".format(pip_info_send))

            # Update objective function values
            # Grouped subareas use its own stat
            # This will need to be updated under both mode
            if outlet_detail["test_obj_dist"] < float(outlet_detail["best_obj_dist"]):
                outlet_detail["best_obj_dist"] = outlet_detail["test_obj_dist"]

                # Update parameter values
                # Only dist mode update parameter values for each outlet
                # Grouped subareas update parameter values based on its own obf function values
                # Then update the subarea level and basin level parameters
                if cali_mode == "dist":
                    outlet_detail["parm_sub"]["BestVal"] = outlet_detail["parm_sub"]["TestVal"]

            # Write parameter values to file
            # Dist mode update and write parameter values for each subarea group
            # Write objective function values to file
            if cali_mode == "dist":
                # After updating the parameter values, write them into the file
                # Write the parameter values and objective functions into
                # corresponding files for recording.
                # As a record, all parameters tried will be recorded
                tested_parm_values_sub = ["{:.4f}".format(parVl)
                      for parVl in outlet_detail["parm_sub"]["TestVal"]]
                lfw_parm_values = "{},{},{},".format(runIdx, outlet_detail["outletid"],
                     variable_header) + ",".join(tested_parm_values_sub) + "\n"
                with open(sub_parm_value_outfn[ovid], 'a') as parmValFile:
                    parmValFile.writelines(lfw_parm_values)

                tested_parm_select_sub = ["{:.3f}".format(parVl) for parVl in
                    outlet_detail["parm_sub"]["ModThisRun"]]
                lfw_parm_select = "{},{},".format(runIdx, outlet_detail["outletid"]) + ",".join(
                    tested_parm_select_sub) + "\n"
                with open(sub_parm_select_outfn[ovid], 'a') as parmSelFile:
                    parmSelFile.writelines(lfw_parm_select)

            # Write the objective function values into files
            # These will be written under both dist and lump mode
            # Need to write these variables into a file
            # lfwAllStat = "RunNo,OutLet,NSE,R2,MSE,PBIAS,RMSE,TestOF,BestOF,probVal,TimeThisRun\n"
            # print("type: nse_value, ", type(outlet_detail["nse_value"]), outlet_detail["nse_value"])
            # print("type: r2_value, ", type(outlet_detail["r2_value"]), outlet_detail["r2_value"])
            # print("type: mse_value, ", type(outlet_detail["mse_value"]), outlet_detail["mse_value"])
            # print("type: pbias_value, ", type(outlet_detail["pbias_value"]), outlet_detail["pbias_value"])
            # print("type: rmse_value, ", type(outlet_detail["rmse_value"]), outlet_detail["rmse_value"])
            # print("type: test_obj_dist, ", type(outlet_detail["test_obj_dist"]), outlet_detail["test_obj_dist"])
            # print("type: best_obj_dist, ", type(outlet_detail["best_obj_dist"]), outlet_detail["best_obj_dist"])

            lfw_stat_objfun = """{},{},{},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f}\n""".format(
                runIdx, outlet_detail["outletid"], variable_header,
                outlet_detail["nse_value"],
                outlet_detail["r2_value"],
                outlet_detail["mse_value"],
                outlet_detail["pbias_value"],
                outlet_detail["rmse_value"],
                outlet_detail["rsr_value"],
                outlet_detail["test_obj_dist"],
                float(outlet_detail["best_obj_dist"]),
                probability_value
            )
            with open(sub_objfun_outfn[ovid], 'a') as obfFile:
                obfFile.writelines(lfw_stat_objfun)

        elif outlet_detail["outletid"] == "not_grouped_subareas":
            # Display the objective function values
            pip_info_send = """Current and best sum values of objective functions are {:.5f}, {:.5f}""".format(
                basin_obj_func_values["obj_basin_test"],
                float(basin_obj_func_values["obj_basin_best"]))
            pipe_process_to_gui.send("{}".format(pip_info_send))

            # Update objective function values
            if basin_obj_func_values["obj_basin_test"] < float(basin_obj_func_values["obj_basin_best"]):
                # Do not update the objective function valut for the basin level.
                # The current and best comparison will need to be used for
                # updating basin level parameters.
                # basin_obj_func_values["obj_basin_best"] = basin_obj_func_values["obj_basin_test"]

                # Update parameter values
                # Not grouped subareas update parameter values based on sum of obf function values
                # This is updated for both lump and dist mode
                outlet_detail["parm_sub"]["BestVal"] = outlet_detail["parm_sub"]["TestVal"]

            # Write parameter values to file
            # This is written every iteration under both mode
            # After updating the parameter values, write them into the file
            # Write the parameter values and objective functions into
            # corresponding files for recording.
            # As a record, all parameters tried will be recorded
            tested_parm_values_sub = ["{:.3f}".format(parVl)
                                      for parVl in outlet_detail["parm_sub"]["TestVal"]]
            lfw_parm_values = "{},{},{},".format(runIdx, outlet_detail["outletid"],
                                                 variable_header) + ",".join(tested_parm_values_sub) + "\n"
            with open(sub_parm_value_outfn[ovid], 'a') as parmValFile:
                parmValFile.writelines(lfw_parm_values)

            tested_parm_select_sub = ["{:.3f}".format(parVl) for parVl in
                                      outlet_detail["parm_sub"]["ModThisRun"]]
            lfw_parm_select = "{},{},".format(runIdx, outlet_detail["outletid"]) + ",".join(
                tested_parm_select_sub) + "\n"
            with open(sub_parm_select_outfn[ovid], 'a') as parmSelFile:
                parmSelFile.writelines(lfw_parm_select)

    # Update the basin objective function values after updating the parameter at the basin level
    if basin_obj_func_values["obj_basin_test"] < float(basin_obj_func_values["obj_basin_best"]):
        parm_basin_level["BestVal"] = parm_basin_level["TestVal"]
        basin_obj_func_values["obj_basin_best"] = basin_obj_func_values["obj_basin_test"]

    # For the basin level, there will only be parameter values and select.
    # the objective function values will be the same as those in the lumped model.
    tested_parm_values_basin = ["{:.3f}".format(parVl)
                              for parVl in parm_basin_level["TestVal"]]
    lfw_parm_values_basin = "{},".format(runIdx) + ",".join(tested_parm_values_basin) + "\n"
    with open(bsn_parm_value_fn, 'a') as parmValFile:
        parmValFile.writelines(lfw_parm_values_basin)

    tested_parm_select_basin = ["{}".format(parVl) for parVl in parm_basin_level["ModThisRun"]]
    lfw_parm_select = "{},".format(runIdx) + ",".join(
        tested_parm_select_basin) + "\n"
    with open(bsn_parm_sel_fn, 'a') as parmSelFile:
        parmSelFile.writelines(lfw_parm_select)

    # Write the objective function values into files
    # Need to write these variables into a file
    # lfwAllStat = "RunNo,OutLet,TestOF,BestOF,probVal\n"
    lfw_stat_objfun = """{},{},{:.5f},{:.5f},{:.5f}\n""".format(
        runIdx, "basin_sum",
        float(basin_obj_func_values["obj_basin_test"]),
        float(basin_obj_func_values["obj_basin_best"]),
        probability_value
    )
    with open(bsn_obj_fn, 'a') as obfFile:
        obfFile.writelines(lfw_stat_objfun)

    return all_outlet_detail, basin_obj_func_values, parm_basin_level

##########################################################################
def generateDDSParVal(parDF,
                      probVal,
                      perturbFactor):
    """
    This function update parameter values with DDS procedure.
    This is conducted individually for each group
    """

    # Counter of how many DV seleceted for perturbation
    dvn_select = 0.0
    # Initialize a parameter value for updating
    parUpdated = 0.0
    # Initialize a random variable for updating
    # Uniformly distributed random number for para selection
    uniRand = 0.0001

    # Added by Qingyu Feng April 6, 2021
    # One very important part is to replace the Test Value
    # with the best value. The logic here is we allways want to
    # try based on the best parameter values. If not,
    # DDS will try always like the first time and without improvement.
    parDF["TestVal"] = parDF["BestVal"]
    # Reset the modThisRun to 0 everytime a new modification is going
    # to be made since we are recording the status of each parameter
    # in each run.
    parDF["ModThisRun"] = [0] * len(parDF["TestVal"])
    # Added by Qingyu Feng April 6, 2021

    for parIdx in parDF.index:
        uniRand = numpy.random.uniform(0.0, 1.0, 1)
        # print("Random value for uniRand: {}".format(uniRand))
        if (uniRand < probVal):
            dvn_select = dvn_select + 1
            parUpdated = updateParValDDS(parDF.loc[parIdx, :],
                                         perturbFactor)
            parDF.loc[parIdx, "TestVal"] = parUpdated
            parDF.loc[parIdx, "ModThisRun"] = 1

    # After updating, deal with a special case for each group
    # This special case is very important. This is because
    # after about 1/3 of total runs, the program will fall
    # in local cycle and can not update the value. Thus, we pick
    # up one paramter randomly to be updated.
    if dvn_select == 0:
        uniRandIdx = numpy.random.randint(1, len(parDF.index), 1)
        # print("Random value for uniRandIdx: {}".format(uniRandIdx))
        parUpdated = updateParValDDS(parDF.loc[parDF.index[uniRandIdx], :],
                                     perturbFactor)
        # Update the value in dataframe
        parDF.loc[parDF.index[uniRandIdx], "TestVal"] = parUpdated
        parDF.loc[parDF.index[uniRandIdx], "ModThisRun"] = 1

    return parDF


##########################################################################
def updateParValDDS(parRow, perturbFactor):
    """
    Purpose is to generate a neighboring decision variable
    value for a single decision variable value being
    perturbed by the DDS optimization algorithm.
    New DV (Decision Variable) value respects the
    upper and lower DV bounds.
    Coded by Bryan Tolson, Nov 2005.

    I/O variable definitions:
    x_cur - current decision variable (DV) value
    x_min - min DV value
    x_max - max DV value
    r  - the neighborhood perturbation factor
    new_value - new DV variable value
    (within specified min and max)

    Qingyu Feng 20201008
    The code was originally in fortran and is translated into
    python here. The input variables are provided as a
    row of dataframe.
    """

    # Get a range of parameter value
    parValRange = float(parRow["UpperBound"]) - float(parRow["LowerBound"])

    # Generate a standard normal random variate (zvalue)
    # Below returns a standard Gaussian random number based
    # upon Numerical recipes gasdev and
    # Marsagalia-Bray Algorithm

    ranVal = 0.0001
    work1 = 0.0
    work2 = 0.0
    work3 = 2.0

    while ((work3 >= 1.0) or (work3 == 0.0)):
        ranVal1 = numpy.random.uniform(0, 1)
        ranVal2 = numpy.random.uniform(0, 1)
        work1 = 2.0 * float(ranVal1) - 1.0
        work2 = 2.0 * float(ranVal2) - 1.0
        work3 = work1 * work1 + work2 * work2

    work3Base = (-2.0 * math.log(work3)) / work3
    work3final = pow(work3Base, 0.5)

    # pick one of two deviates at random
    # (don't worry about trying to use both):
    ranVal3 = numpy.random.uniform(0, 1)
    # print("Random value for updating values:{}, {}, {}".format(ranVal1, ranVal2, ranVal3))
    zvalue = 0.000
    if (ranVal3 < 0.5):
        zvalue = work3final * work1
    else:
        zvalue = work3final * work2

    # done standard normal random variate generation

    # Calculate new decision variable value
    parValUpdated = float(parRow["TestVal"]) + zvalue * perturbFactor * parValRange

    # Check new value is within DV bounds.
    # If not, bounds are reflecting.
    if (parValUpdated < float(parRow["LowerBound"])):
        parValUpdated = float(parRow["LowerBound"]) + (float(parRow["LowerBound"]) - parValUpdated)
        if (parValUpdated > float(parRow["UpperBound"])):
            parValUpdated = float(parRow["LowerBound"])
    elif (parValUpdated > float(parRow["UpperBound"])):
        parValUpdated = float(parRow["UpperBound"]) - (parValUpdated - float(parRow["UpperBound"]))
        if (parValUpdated < float(parRow["LowerBound"])):
            parValUpdated = float(parRow["UpperBound"])

    return parValUpdated


##########################################################################
def writePairToFile(all_outlet_detail, 
                    fd_ts_eachrun,
                    run_index,
                    pair_varid_obs_header
                    ):
    """
    Write the pairs into corresponding files
    """
    for ovid, outlet_detail in all_outlet_detail.items():
        if not outlet_detail["outletid"] == "not_grouped_subareas":
            variable_id = outlet_detail["variableid"]
            variable_header = pair_varid_obs_header[variable_id].split("(")[0]
            
            fnp_sim_this_run = os.path.join(fd_ts_eachrun, 
                                            "obssimpair_{}_{}_{}.csv".format(
                                            outlet_detail["outletid"],
                                            variable_header,
                                            run_index
                                            ))
            if os.path.isfile(fnp_sim_this_run):
                os.remove(fnp_sim_this_run)

            outlet_detail["df_obs_sim"].to_csv(fnp_sim_this_run)



##########################################################################
def getPreviousRunNo(sub_objfun_outfn,
                     all_outlet_detail,
                     current_cali_mode):
    """
    get the number of lines in objective function output files
    """

    finished_run_lines = 0
    # make a copy of string
    current_cali_mode = str(current_cali_mode)

    for ovid, outlet_detail in all_outlet_detail.items():
        if not outlet_detail["outletid"] == "not_grouped_subareas":
            if not os.path.isfile(sub_objfun_outfn[ovid]):
                showinfo("Warning",
                         "No previsous runs found. Will start from No 1.")
                finished_run_lines = 1
            else:

                # Get the previous mode, if not the same as previous, set to 1
                previous_cali_mode = sub_objfun_outfn[ovid].split("_")[-1].split(".")[0]
                if current_cali_mode == previous_cali_mode:
                    with open(sub_objfun_outfn[ovid], "r") as objfile:
                        lif = objfile.readlines()

                    if len(lif) <= 1:
                        # If only one header line exists, start from 1
                        finished_run_lines = 1
                    else:
                        # Else, the new number will be removed header (-1) ,
                        # but next run (+1)
                        finished_run_lines = len(lif)
                elif current_cali_mode != previous_cali_mode:
                    showinfo("Warning",
                             "Different calibration mode selected. Will start from No 1.")
                    finished_run_lines = 1
            break

    return finished_run_lines, previous_cali_mode

##########################################################################
def getPreviousRunParmsObjValues(
        all_outlet_detail,
        parm_basin_level,
        sub_parm_value_outfn,
        sub_objfun_outfn,
        bsn_parm_value_fn,
        bsn_obj_fn,
        basin_obj_func_values,
        start_run_no,
        cali_mode):
    """
    Get previous run parameter and objective function values
    :param all_outlet_detail:
    :param parm_basin_level:
    :param sub_parm_value_outfn:
    :param sub_objfun_outfn:
    :param bsn_parm_value_fn:
    :param bsn_obj_fn:
    :param basin_obj_func_values:
    :param start_run_no:
    :param cali_mode:
    :return:
    """
    continue_success = True
    # For the dist mode, the objective functions have one file for each
    # outlet group, and 1 for not grouped if exists.
    # the parameter values have one for each outlet, one for not grouped,
    # and one for basin.
    # This function need to update values for both parameter
    # values, and objective function values.
    for ovid, outlet_detail in all_outlet_detail.items():
        outlet_subgroup_id = outlet_detail["outletid"]
        outlet_variable_name = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]

        # Read the objective function values and parameter values.
        # Parameter values exists for grouped subareas when only under dist mode
        # Objective function values exists for
        if outlet_detail["outletid"] != "not_grouped_subareas":

            # Read the objective function values
            if not os.path.isfile(sub_objfun_outfn[ovid]):
                showinfo("Warning",
                         "File {} in existing folder is not found. Please double check your settings".format(
                             sub_objfun_outfn[ovid])
                         )
                continue_success = False
                return all_outlet_detail, parm_basin_level, continue_success, basin_obj_func_values
            else:
                previous_obj_dataframe = pandas.read_csv(
                    sub_objfun_outfn[ovid], header=0, index_col=0)
                outlet_detail["r2_value"] = previous_obj_dataframe.loc[start_run_no - 1, "R2"]
                outlet_detail["nse_value"] = previous_obj_dataframe.loc[start_run_no - 1, "NSE"]
                outlet_detail["pbias_value"] = previous_obj_dataframe.loc[start_run_no - 1, "PBIAS"]
                outlet_detail["mse_value"] = previous_obj_dataframe.loc[start_run_no - 1, "MSE"]
                outlet_detail["rmse_value"] = previous_obj_dataframe.loc[start_run_no - 1, "RMSE"]
                outlet_detail["rsr_value"] = previous_obj_dataframe.loc[start_run_no - 1, "RSR"]
                outlet_detail["test_obj_dist"] = previous_obj_dataframe.loc[start_run_no - 1, "TestOF"]
                outlet_detail["best_obj_dist"] = previous_obj_dataframe.loc[start_run_no - 1, "BestOF"]
                if cali_mode == "dist":
                    # Read the parameter file, get the values, and
                    # update the initial parameter and objective value.
                    # For each variable
                    previous_parm_dataframe = pandas.read_csv(
                        sub_parm_value_outfn[ovid], header=0, index_col=0)
                    for parm_symbol in outlet_detail["parm_sub"]["Symbol"]:
                        outlet_detail["parm_sub"].loc[
                            outlet_detail["parm_sub"]["Symbol"] == parm_symbol,
                            "BestVal"] = previous_parm_dataframe.loc[
                                start_run_no-1, parm_symbol]
                        outlet_detail["parm_sub"].loc[
                            outlet_detail["parm_sub"]["Symbol"] == parm_symbol,
                            "TestVal"] = previous_parm_dataframe.loc[
                            start_run_no - 1, parm_symbol]

        elif outlet_detail["outletid"] == "not_grouped_subareas":
            # Read the objective function values
            if not os.path.isfile(sub_parm_value_outfn[ovid]):
                showinfo("Warning",
                         "File {} in existing folder is not found. Please double check your settings".format(
                             sub_parm_value_outfn[ovid])
                         )
                continue_success = False
                return all_outlet_detail, parm_basin_level, continue_success, basin_obj_func_values
            else:
                # For not_grouped_subareas, it exists only for lumped or when exists in dist mode.
                # The file for objective function is not created.
                # But the parameter values all exists.
                previous_parm_dataframe = pandas.read_csv(
                    sub_parm_value_outfn[ovid], header=0, index_col=0)
                for parm_symbol in outlet_detail["parm_sub"]["Symbol"]:
                    outlet_detail["parm_sub"].loc[
                        outlet_detail["parm_sub"]["Symbol"] == parm_symbol,
                        "BestVal"] = previous_parm_dataframe.loc[
                        start_run_no - 1, parm_symbol]
                    outlet_detail["parm_sub"].loc[
                        outlet_detail["parm_sub"]["Symbol"] == parm_symbol,
                        "TestVal"] = previous_parm_dataframe.loc[
                        start_run_no - 1, parm_symbol]
                continue_success = True

    if not os.path.isfile(bsn_obj_fn):
        showinfo("Warning",
                 "File {} in existing folder is not found. Please double check your settings".format(
                     bsn_obj_fn)
                 )
        continue_success = False
        return all_outlet_detail, parm_basin_level, continue_success, basin_obj_func_values
    else:
        # basin parameter and objective function values always exists, read and update the values.
        previous_obj_dataframe_bsn = pandas.read_csv(
            bsn_obj_fn, header=0, index_col=0)
        basin_obj_func_values["test_obj_dist"] = previous_obj_dataframe_bsn.loc[start_run_no - 1, "TestOF"]
        basin_obj_func_values["best_obj_dist"] = previous_obj_dataframe_bsn.loc[start_run_no - 1, "BestOF"]
        continue_success = True

    if not os.path.isfile(bsn_parm_value_fn):
        showinfo("Warning",
                 "File {} in existing folder is not found. Please double check your settings".format(
                     bsn_parm_value_fn)
                 )
        continue_success = False
        return all_outlet_detail, parm_basin_level, continue_success, basin_obj_func_values
    else:
        previous_parm_dataframe_bsn = pandas.read_csv(
            bsn_parm_value_fn, header=0, index_col=0)
        for parm_symbol in parm_basin_level["Symbol"]:
            parm_basin_level.loc[
                parm_basin_level["Symbol"] == parm_symbol,
                "BestVal"] = previous_parm_dataframe_bsn.loc[
                start_run_no - 1, parm_symbol]
            parm_basin_level.loc[
                parm_basin_level["Symbol"] == parm_symbol,
                "TestVal"] = previous_parm_dataframe_bsn.loc[
                start_run_no - 1, parm_symbol]
        continue_success = True

    return all_outlet_detail, parm_basin_level, continue_success, basin_obj_func_values


##########################################################################
def copyTxtInOutContents(path_txtinout, path_best_run):
    """
    Copy contents in the txtinout folder into the best run folder
    """

    files_in_txtinout = glob.glob("{}/*".format(path_txtinout))

    for file_src in files_in_txtinout:
        file_name = os.path.basename(file_src)
        file_dest = os.path.join(path_best_run, file_name)
        if os.path.isfile(file_dest):
            os.remove(file_dest)
        copyfile(file_src, file_dest)


##########################################################################
def getUsrBestParmSet(all_outlet_detail,
            parm_basin_level,
            cali_options,
            proj_path,
            fdname_outfiles,
            pair_varid_obs_header):
    """
    Extract the best parameter values from the calibrated parameter files
    and update the parameter set for corresponding groups
    """
    path_calibration_output = os.path.join(proj_path, fdname_outfiles)
    if cali_options["cali_mode"] == "dist":
        for olt_key, outlet_detail in all_outlet_detail.items():
            var_name = pair_varid_obs_header[all_outlet_detail[olt_key]["variableid"]]
            var_name = var_name.split("(")[0]
            sub_parm_value_outfn = os.path.join(path_calibration_output,
                                         "DMPOT_Para_{}{}_{}.out".format(
                                             outlet_detail["outletid"],
                                             var_name,
                                             "dist"))
            # Read in the parameter from the calibrated file
            parm_sub_level_whole = pandas.read_csv(
                sub_parm_value_outfn, sep=",")
            parm_sub_level_whole = parm_sub_level_whole.set_index("RunNO")
            parm_sub_level_bestrun = parm_sub_level_whole.loc[
                int(cali_options["best_run_no"]), ]
            # Update the parm_sub for each outlet
            for symbol in outlet_detail["parm_sub"]["Symbol"]:
                outlet_detail["parm_sub"].loc[
                    outlet_detail["parm_sub"]["Symbol"] == symbol,
                    "TestVal"] = parm_sub_level_bestrun[symbol]

    elif cali_options["cali_mode"] == "lump":
        sub_parm_value_outfn = os.path.join(path_calibration_output,
                                     "DMPOT_Para_lump_sub_level.out")

        # Read in the parameter from the calibrated file
        parm_sub_level_whole = pandas.read_csv(
            sub_parm_value_outfn, sep=",")
        parm_sub_level_whole = parm_sub_level_whole.set_index("RunNO")
        parm_sub_level_bestrun = parm_sub_level_whole.loc[
            int(cali_options["best_run_no"]),]
        # Update the parm_sub for each outlet
        for symbol in all_outlet_detail["not_grouped_subareas"]["parm_sub"]["Symbol"]:
            all_outlet_detail["not_grouped_subareas"]["parm_sub"].loc[
                all_outlet_detail["not_grouped_subareas"]["parm_sub"]["Symbol"] == symbol,
                "TestVal"] = parm_sub_level_bestrun[symbol]

    # Get basin level parameter list
    bsn_parm_value_fn = os.path.join(path_calibration_output, "DMPOT_Para_Bsn_{}.out".format(
        cali_options["cali_mode"]))

    parm_basin_level_whole = pandas.read_csv(bsn_parm_value_fn, sep = ",")
    parm_basin_level_whole = parm_basin_level_whole.set_index("RunNO")
    parm_basin_level_bestrun = parm_basin_level_whole.loc[int(cali_options["best_run_no"]), ]

    for symbol in parm_basin_level["Symbol"]:
        parm_basin_level.loc[
            parm_basin_level["Symbol"] == symbol,
            "TestVal"] = parm_basin_level_bestrun[symbol]

    return all_outlet_detail, parm_basin_level_bestrun


