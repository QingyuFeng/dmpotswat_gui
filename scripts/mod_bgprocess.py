import copy
import os
import numpy
import glob
import multiprocessing
from shutil import copyfile
import geopandas as gpd
from osgeo import ogr

from .global_vars import global_vars
from .mod_dmpotutil import *
from .mod_sautil import *
from .mod_plotutil import *

GlobalVars = global_vars()


##########################################################################
def runDefaultSWAT(cali_options,
                   proj_path,
                   pipe_process_to_gui):
    """
    run default and get stat for default swat model
    :return:
    """
    # Create a folder to store the calibration and validation
    fdname_running = "workingdir"

    path_workingdir = os.path.join(proj_path, fdname_running)
    path_txtinout = os.path.join(proj_path, "txtinout")

    if not os.path.isdir(path_workingdir):
        os.mkdir(path_workingdir)

    # Copy the txtinout contents into the purpose folder.
    pip_info_send = """Process: copying txtinout content into the workingdir"""
    pipe_process_to_gui.send("{}".format(pip_info_send))
    copyTxtInOutContents(path_txtinout, path_workingdir)

    # Update file.cio to match user specified simulation details
    updateFileCio(cali_options,
                  proj_path,
                  fdname_running,
                  GlobalVars.reach_var_list)
    # Run the swat model
    # Intiate the function with an individual Process, which do not share memory
    # with the main interface like using Thread.
    # Then get the commandline output into the pipe for display
    runSWATModel(GlobalVars.os_platform,
                proj_path,
                "workingdir",
                GlobalVars.path_src_swat_exe,
                pipe_process_to_gui)

    # Get observed data
    # This function added the key "df_obs" to the outlet_detail dict
    # outlet_detail = {key_number: {outlet_var: xxx, df_obs}}.

    # Get reach file contents into dataframe for calculating statistics
    pip_info_send = """Process: Reading RCH output for calculation of objective functions"""
    pipe_process_to_gui.send("{}".format(pip_info_send))
    path_output_rch = os.path.join(proj_path, fdname_running, "output.rch")
    try:
        dataframe_outrch_whole = getRch2DF(path_output_rch,
                                           cali_options["iprint"],
                                           len(cali_options["all_outlets_reach"]))
    except IOError as e:
        showinfo("Warning",
                 """File {} does not exist: {}. Please double check your TxtInOut \
                folder and make sure you have a complete set""".format(path_output_rch, e))

    all_outlet_detail = read_observed_data(
        cali_options,
        proj_path,
        GlobalVars.pair_varid_obs_header,
        GlobalVars.obs_data_header)

    # Then construct series of observed and simulated pairs for stat calculation
    all_outlet_detail = buildObsSimPair(
        all_outlet_detail,
        dataframe_outrch_whole,
        GlobalVars.pair_varid_obs_header,
        cali_options)

    all_outlet_detail = calAllStatEachOlt(
        all_outlet_detail,
        GlobalVars.pair_varid_obs_header)

    pip_info_send = """Confirmation: Finished reading observed data"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    all_outlet_detail = calOltObjFunValue(all_outlet_detail)

    basin_obj_func_values = {
        "obj_basin_test": 10000.0,
        "obj_basin_best": 10000.0}

    basin_obj_func_values["obj_basin_test"] = calOltBsnFunValue(
        all_outlet_detail,
        basin_obj_func_values["obj_basin_test"])

    # Display the output in gui
    for outlet_key, outlet_detail in all_outlet_detail.items():
        pip_info_send = """Output: Objective function for outlet no {} is {:.4f}!""".format(
            outlet_detail["outletid"], outlet_detail["test_obj_dist"]
        )
        pipe_process_to_gui.send("{}".format(pip_info_send))
        pip_info_send = """Output: R2 for outlet no {} is {:.4f}!""".format(
            outlet_detail["outletid"], outlet_detail["r2_value"])

        pipe_process_to_gui.send("{}".format(pip_info_send))
        pip_info_send = """Output: NSE for outlet no {} is {:.4f}!""".format(
            outlet_detail["outletid"], outlet_detail["nse_value"])
        pipe_process_to_gui.send("{}".format(pip_info_send))

        pip_info_send = """Output: Pbias for outlet no {} is {:.4f}!""".format(
            outlet_detail["outletid"], outlet_detail["pbias_value"])
        pipe_process_to_gui.send("{}".format(pip_info_send))

        pip_info_send = """Output: MSE for outlet no {} is {:.4f}!""".format(
            outlet_detail["outletid"], outlet_detail["mse_value"])
        pipe_process_to_gui.send("{}".format(pip_info_send))

        pip_info_send = """Output: RMSE for outlet no {} is {:.4f}!""".format(
            outlet_detail["outletid"], outlet_detail["rmse_value"])
        pipe_process_to_gui.send("{}".format(pip_info_send))

        pip_info_send = """Output: RSR for outlet no {} is {:.4f}!""".format(
            outlet_detail["outletid"], outlet_detail["rsr_value"])
        pipe_process_to_gui.send("{}".format(pip_info_send))

        pip_info_send = """Confirmation: finished evaluating default swat model!"""
        pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """bgrundone"""
    pipe_process_to_gui.send("{}".format(pip_info_send))


##########################################################################
def runSWATBestParmSet(pipe_process_to_gui,
                       cali_options,
                       proj_path,
                       proj_parm
                    ):
    """
    run swat model with the best parameter set
    and get stat for default swat model
    :return:
    """
    # Create a folder to store the calibration and validation
    fdname_running = "txtinout_best_{}".format(cali_options["bestrun_purpose"])
    path_best_run = os.path.join(proj_path, fdname_running)
    if not os.path.isdir(path_best_run):
        os.mkdir(path_best_run)

    path_txtinout = os.path.join(proj_path, "txtinout")

    fdname_best_outfiles = "outfiles_best_{}".format(cali_options["bestrun_purpose"])
    path_best_outfiles = os.path.join(proj_path, fdname_best_outfiles)
    if not os.path.isdir(path_best_outfiles):
        os.mkdir(path_best_outfiles)

    # Create a folder to store the simulated values for plotting purpose
    fd_ts_eachrun = os.path.join(proj_path, fdname_best_outfiles, "timeseries")
    if not os.path.isdir(fd_ts_eachrun):
        os.mkdir(fd_ts_eachrun)

    pip_info_send = """Process: copying files from the {}""".format(path_txtinout)
    pipe_process_to_gui.send("{}".format(pip_info_send))
    pip_info_send = """Process: to the {}""".format(path_best_run)
    pipe_process_to_gui.send("{}".format(pip_info_send))
    # Copy the txtinout contents into the purpose folder.
    copyTxtInOutContents(path_txtinout, path_best_run)

    # Update file.cio to match user specified simulation details
    updateFileCio(cali_options,
                  proj_path,
                  fdname_running,
                  GlobalVars.reach_var_list)
    pip_info_send = """Process: Finished updating file.cio"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # get Subarea_groups based on calibration mode.
    # subarea_groups:
    # : Dictionary
    # : outlet: [list of subareas for this outlet]
    # If the user selected distributed mode, the groups will be
    # generated for each outlet. A new key named "not_grouped_subareas"
    # might be added if some subareas are excluded in groups for all outlets.
    subarea_groups = getSubGroupsForOutlet(
        cali_options["outlet_details"],
        cali_options["cali_mode"],
        proj_path)
    pip_info_send = """Process: Finished grouping subareas for each outlet !\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Get parameter lists
    parm_basin_level, parm_sub_level = getParmSets(
        proj_parm,
        GlobalVars.basin_file_exts,
        GlobalVars.sub_level_file_exts,
        GlobalVars.hru_level_file_exts)
    pip_info_send = """Process: Finished creating parameter database !\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    all_outlet_detail = read_observed_data(
        cali_options,
        proj_path,
        GlobalVars.pair_varid_obs_header,
        GlobalVars.obs_data_header)

    # Also add the subarea lists to corresponding outlet var pairs.
    all_outlet_detail = addSubareaGroups(
        cali_options["cali_mode"],
        all_outlet_detail,
        subarea_groups)

    # Add parameter set for each outlet variable pairs.
    all_outlet_detail = initParmset(
        all_outlet_detail,
        parm_sub_level,
        GlobalVars.pair_varid_obs_header)

    sub_level_fname_for_groups, hru_level_fname_for_groups = initFilenameList(
        proj_path,
        subarea_groups)
    pip_info_send = """Process: Finished Initiating objective function value"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    all_outlet_detail, parm_basin_level_best = getUsrBestParmSet(
        all_outlet_detail,
        parm_basin_level,
        cali_options,
        proj_path,
        "outfiles_dds",
        GlobalVars.pair_varid_obs_header
    )

    basin_obj_func_values = {
        "obj_basin_test": 10000.0,
        "obj_basin_best": 10000.0}

    # Subarea level
    sub_parm_value_outfn_best, sub_parm_select_outfn_best, sub_objfun_outfn_best = initialOutFNameParmObjSublvl(
        cali_options["cali_mode"],
        all_outlet_detail,
        proj_path,
        fdname_best_outfiles,
        GlobalVars.pair_varid_obs_header)

    # Basin level
    bsn_parm_value_outfn_best, bsn_parm_sel_outfn_best, bsn_obj_fn_best = initialOutFNameParmObjBsnlvl(
        proj_path,
        fdname_best_outfiles,
        cali_options["cali_mode"])

    writeOutFileHeadersParmObjBsnlvl(
        parm_basin_level["Symbol"],
        bsn_parm_value_outfn_best,
        bsn_parm_sel_outfn_best,
        bsn_obj_fn_best
    )

    writeOutFileHeadersParmObjSublvl(
        cali_options["cali_mode"],
        all_outlet_detail,
        parm_sub_level["Symbol"],
        "outfiles_dds",
        GlobalVars.pair_varid_obs_header,
        sub_parm_value_outfn_best,
        sub_parm_select_outfn_best,
        sub_objfun_outfn_best
    )

    pip_info_send = """Process: Finished initializing output files\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Modify the input files with best parameters
    # For the parameter sets of each subarea group, the parameter is
    # stored in a dataframe and contain only subarea/hru level parameters
    # They will be updated one by one.
    if cali_options["cali_mode"] == "dist":
        for ovid, outlet_detail in all_outlet_detail.items():
            outlet_subgroup_id = outlet_detail["outletid"]
            outlet_variable_name = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]

            # Update parameter values in file
            pip_info_send = """Process: Updating parameters for outlet {} {}""".format(
                outlet_subgroup_id, outlet_variable_name)
            pipe_process_to_gui.send("{}".format(pip_info_send))

            modifyParInFileSub(proj_path,
                               fdname_running,
                               sub_level_fname_for_groups,
                               hru_level_fname_for_groups,
                               outlet_detail["parm_sub"],
                               outlet_subgroup_id,
                               pipe_process_to_gui)
            pip_info_send = """Process: Finished updating files for outlet {}""".format(
                outlet_subgroup_id)
            pipe_process_to_gui.send("{}".format(pip_info_send))
    # For the lump mode, only updating the not_grouped_subareas since
    # the list for other outlet is not added. Only one set of subarea
    # parameter sets will be used: all_outlet_detail["not_grouped_subareas"]
    elif cali_options["cali_mode"] == "lump":
        # Update parameter values in file
        pip_info_send = """Process: Updating all parameters"""
        pipe_process_to_gui.send("{}".format(pip_info_send))
        modifyParInFileSub(proj_path,
                           fdname_running,
                           sub_level_fname_for_groups,
                           hru_level_fname_for_groups,
                           all_outlet_detail["not_grouped_subareas"]["parm_sub"],
                           "not_grouped_subareas",
                           pipe_process_to_gui)
        pip_info_send = """Process: Finished updating files"""
        pipe_process_to_gui.send("{}".format(pip_info_send))

    if len(parm_basin_level.index) > 0:
        # After modifying parameter values in file,
        modifyParInFileBsn(parm_basin_level,
                           proj_path,
                           fdname_running,
                           pipe_process_to_gui)
    pip_info_send = """Process: Finished modifying swat input files !\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Run the swat model
    # Intiate the function with an individual Process, which do not share memory
    # with the main interface like using Thread.
    # Then get the commandline output into the pipe for display
    runSWATModel(GlobalVars.os_platform,
                 proj_path,
                 fdname_running,
                 GlobalVars.path_src_swat_exe,
                 pipe_process_to_gui)

    # Get reach file contents into dataframe for calculating statistics
    path_output_rch = os.path.join(proj_path, fdname_running, "output.rch")
    try:
        dataframe_outrch_whole = getRch2DF(path_output_rch,
                                           cali_options["iprint"],
                                           len(cali_options["all_outlets_reach"]))
    except IOError as e:
        showinfo("Warning",
                 """File {} does not exist: {}. Please double check your TxtInOut \
                folder and make sure you have a complete set""".format(path_output_rch, e))
        return
    # Then construct series of observed and simulated pairs for stat calculation
    all_outlet_detail = buildObsSimPair(
        all_outlet_detail,
        dataframe_outrch_whole,
        GlobalVars.pair_varid_obs_header,
        cali_options)

    # Write the output pair into a file
    writePairToFile(all_outlet_detail,
                    fd_ts_eachrun,
                    cali_options["best_run_no"],
                    GlobalVars.pair_varid_obs_header)

    all_outlet_detail = calAllStatEachOlt(
        all_outlet_detail,
        GlobalVars.pair_varid_obs_header)

    all_outlet_detail = calOltObjFunValue(all_outlet_detail)

    basin_obj_func_values["obj_basin_test"] = calOltBsnFunValue(
        all_outlet_detail,
        basin_obj_func_values["obj_basin_test"])

    all_outlet_detail, basin_obj_func_values, parm_basin_level = updateBestParmSubAndBasin(
        "best_run",
        all_outlet_detail,
        basin_obj_func_values,
        cali_options["cali_mode"],
        GlobalVars.pair_varid_obs_header,
        parm_basin_level,
        sub_parm_value_outfn_best,
        sub_objfun_outfn_best,
        sub_parm_select_outfn_best,
        bsn_parm_value_outfn_best,
        bsn_parm_sel_outfn_best,
        bsn_obj_fn_best,
        1.0,
        pipe_process_to_gui)

    pip_info_send = """Confirmation: DDS procedure finished"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """Confirmation: Calibration completed"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """bgrundone"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

##########################################################################
def runPlotBestParmOut(pipe_process_to_gui,
                cali_options,
                proj_path
                ):
    """
    Side process for generating user specified plots
    :param all_outlet_detail:
    :param proj_path:
    :param cali_mode:
    :param total_dds_iterations:
    :return:
    """
    pip_info_send = """Process: Start creating plots for best run"""
    pipe_process_to_gui.send("{}".format(pip_info_send))
    fdname_best_outfiles = "outfiles_best_{}".format(cali_options["bestrun_purpose"])
    for outlet_key, outlet_detail in cali_options["outlet_details"].items():
        if not outlet_detail["outletid"] == "not_grouped_subareas":

            # Check whether the best run time series exists before. If not,
            # create a warning:
            # Read the output csv files for specified run no
            outlet_id = int(outlet_detail["outletid"])
            variable_id = outlet_detail["variableid"]
            variable_header = GlobalVars.pair_varid_obs_header[variable_id]

            cali_mode_text = ""

            if cali_options["cali_mode"] == "dist":
                cali_mode_text = "Distributed"
            elif cali_options["cali_mode"] == "lump":
                cali_mode_text = "Lumped"

            # Read the output csv files for specified run no
            fd_ts_eachrun = os.path.join(proj_path, fdname_best_outfiles, "timeseries")
            fnp_sim_this_run = os.path.join(fd_ts_eachrun,
                                            "obssimpair_{}_{}_{}.csv".format(
                                                outlet_detail["outletid"],
                                                variable_header.split("(")[0],
                                                cali_options["best_run_no"]
                                            ))

            if not os.path.isfile(fnp_sim_this_run):
                pip_info_send = """Process: The best simulation was not found. Please run the model first before generating figures"""
                pipe_process_to_gui.send("{}".format(pip_info_send))

                pip_info_send = """bgrundone"""
                pipe_process_to_gui.send("{}".format(pip_info_send))

            else:

                outlet_detail["plot_time_series"] = "true"
                outlet_detail["plot_duration_curve"] = "true"

                generatingPlots(proj_path,
                        outlet_detail,
                        cali_options["cali_mode"],
                        cali_options["best_run_no"],
                        GlobalVars.pair_varid_obs_header,
                        cali_options["bestrun_purpose"],
                        fdname_best_outfiles,
                        pipe_process_to_gui)



##########################################################################
def runCreateSubwatershedShapefile(
                   cali_options,
                   proj_path):
    """
    run create the shapefiles of subwatersheds for selected outlets
    :return:
    """
    # Create a folder to store the calibration and validation
    fdname_reachshapefiles = os.path.join(proj_path, "reachshapefile")
    fname_reachshapefiles = "reach.shp"
    path_reachshapefiles = os.path.join(fdname_reachshapefiles,
                                        fname_reachshapefiles)

    if not os.path.isfile(path_reachshapefiles):
        showinfo("Warning", """The \"reach.shp\" file was not found in the
                               reachshapefile folder. Please double
                               check to proceed!""")
        return

    fdname_subwsshapefiles = os.path.join(fdname_reachshapefiles, "sub_shapefiles")
    if not os.path.isdir(fdname_subwsshapefiles):
        os.mkdir(fdname_subwsshapefiles)

    # get Subarea_groups based on calibration mode.
    # subarea_groups:
    # : Dictionary
    # : outlet: [list of subareas for this outlet]
    # If the user selected distributed mode, the groups will be
    # generated for each outlet. A new key named "not_grouped_subareas"
    # might be added if some subareas are excluded in groups for all outlets.
    subarea_groups = getSubGroupsForOutlet(
        cali_options["outlet_details"],
        cali_options["cali_mode"],
        proj_path)

    # read file
    reach_shapefile = gpd.read_file(path_reachshapefiles)

    # select rows
    for outlet_key, subgroups in subarea_groups.items():

        # Define output shapefile names
        path_subwsshapefiles = os.path.join(
            fdname_subwsshapefiles,
            "reach_for_{}.shp".format(outlet_key))

        # Delete files if they exist
        if os.path.isfile(path_subwsshapefiles):
            existfile = ogr.Open(path_subwsshapefiles)
            layer = existfile.GetLayerByIndex(0)
            count = layer.GetFeatureCount()
            for feature in range(count):
                layer.DeleteFeature(feature)

        # Convert string to int in the subgroups
        subgroups_int = map(int, subgroups)
        sub_watershed_sel = reach_shapefile.loc[reach_shapefile['GRID_CODE'].isin(subgroups_int), :]

        # select columns
        # sub_watershed_sel_col = sub_watershed_sel.loc[:,
        #                    ['county_name', 'attribute1', 'attribute2', 'attribute3', 'attribute4']]

        # write to file
        sub_watershed_sel.to_file(path_subwsshapefiles)

    showinfo("Confirmation", """Sub-watershed shapefiles for all outlets have been
        created and stored under the \"reachshapefiles\" folder""")


##########################################################################
def runCalibration(pipe_process_to_gui,
                   cali_options,
                   proj_path,
                   proj_parm,
                   cali_dds):
    """
    run default and get stat for default swat model
    To run the model, the original code need to be transferred here.
    And the output will be copied into the List box.
    These include:
    1. read observed dataset
    :return:
    """
    # Create a folder to store the calibration and validation
    fdname_running = "workingdir"
    path_workingdir = os.path.join(proj_path, fdname_running)
    path_txtinout = os.path.join(proj_path, "txtinout")

    if not os.path.isdir(path_workingdir):
        os.mkdir(path_workingdir)

    pip_info_send = """Process: Copying files in the txtinout folder to the workingdir folder !\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Copy the txtinout contents into the purpose folder.
    copyTxtInOutContents(path_txtinout, path_workingdir)

    # get Subarea_groups based on calibration mode.
    # subarea_groups:
    # : Dictionary
    # : outlet: [list of subareas for this outlet]
    # If the user selected distributed mode, the groups will be
    # generated for each outlet. A new key named "not_grouped_subareas"
    # might be added if some subareas are excluded in groups for all outlets.
    subarea_groups = getSubGroupsForOutlet(
        cali_options["outlet_details"],
        cali_options["cali_mode"],
        proj_path)
    pip_info_send = """Process: Finished grouping subareas for each outlet !\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Get parameter lists
    parm_basin_level, parm_sub_level = getParmSets(
        proj_parm,
        GlobalVars.basin_file_exts,
        GlobalVars.sub_level_file_exts,
        GlobalVars.hru_level_file_exts)
    pip_info_send = """Process: Finished creating parameter database !\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Get observed data
    # This function added the key "df_obs" to the outlet_detail dict
    # outlet_detail = {key_number: {outlet_var: xxx, df_obs}}.
    all_outlet_detail = read_observed_data(
        cali_options,
        proj_path,
        GlobalVars.pair_varid_obs_header,
        GlobalVars.obs_data_header)

    # Also add the subarea lists to corresponding outlet var pairs.
    all_outlet_detail = addSubareaGroups(
        cali_options["cali_mode"],
        all_outlet_detail,
        subarea_groups)

    # Add parameter set for each outlet variable pairs.
    all_outlet_detail = initParmset(
        all_outlet_detail,
        parm_sub_level,
        GlobalVars.pair_varid_obs_header)

    sub_level_fname_for_groups, hru_level_fname_for_groups = initFilenameList(
        proj_path,
        subarea_groups)
    pip_info_send = """Process: Finished Initiating objective function value"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Update file.cio to match user specified simulation details
    updateFileCio(cali_options,
                  proj_path,
                  fdname_running,
                  GlobalVars.reach_var_list)

    pip_info_send = """Process: Finished updating the file.cio file"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """Process: DDS procedure started"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """Process: Total iteration no: {}""".format(
        cali_dds["totalsimno"])
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Two situations:
    # User select to use random parameter initParmIdx == random
    # User select to use default parameter initParmIdx == initial

    # Initial a counter to record the runs of random
    # counter_initial_runno: counter of run nos for initial runs
    basin_obj_func_values = {
        "obj_basin_test": 10000.0,
        "obj_basin_best": 10000.0}

    # Get the number of previous runs if restart mode = Continue:
    # initialize output folders
    path_output = os.path.join(proj_path, "outfiles_dds")
    if not os.path.isdir(path_output):
        os.mkdir(path_output)

    # Initializing output files
    # Subarea level
    sub_parm_value_outfn, sub_parm_select_outfn, sub_objfun_outfn = initialOutFNameParmObjSublvl(
        cali_options["cali_mode"],
        all_outlet_detail,
        proj_path,
        "outfiles_dds",
        GlobalVars.pair_varid_obs_header)

    # Basin level
    bsn_parm_value_fn, bsn_parm_sel_fn, bsn_obj_fn = initialOutFNameParmObjBsnlvl(
        proj_path,
        "outfiles_dds",
        cali_options["cali_mode"])

    pip_info_send = """Process: Finished initializing output files\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Deal with the different ways of several initial runs.
    if cali_dds["initparaidx"] == "random":
        initial_run_times = math.ceil(0.005 * int(cali_dds["totalsimno"]))
    elif cali_dds["initparaidx"] == "initial":
        initial_run_times = 1

    # Create a folder to store the simulated values for plotting purpose
    fd_ts_eachrun = os.path.join(proj_path, "outfiles_dds", "timeseries")
    if not os.path.isdir(fd_ts_eachrun):
        os.mkdir(fd_ts_eachrun)

    start_run_no = 1
    write_outfile_headers = True
    if cali_dds["restartmech"] == "continue":
        start_run_no, previous_cali_mode = getPreviousRunNo(
            sub_objfun_outfn,
            all_outlet_detail,
            cali_options["cali_mode"])

        # Read previous run parameter and objective function values
        # This will be performed when the user select to use the same
        # calibration mode, and the previous run no is larger
        # than the random initial values
        # One variable to mark whether continue succeed
        continue_success = False
        if (previous_cali_mode == cali_options["cali_mode"] and
                start_run_no > initial_run_times):

            pip_info_send = """Process: Getting values of best parameter set from previous run\n"""
            pipe_process_to_gui.send("{}".format(pip_info_send))

            all_outlet_detail, parm_basin_level, continue_success, basin_obj_func_values = getPreviousRunParmsObjValues(
                all_outlet_detail,
                parm_basin_level,
                sub_parm_value_outfn,
                sub_objfun_outfn,
                bsn_parm_value_fn,
                bsn_obj_fn,
                basin_obj_func_values,
                start_run_no,
                cali_options["cali_mode"])

            write_outfile_headers = False

            if not continue_success:
                # When continue failed, stop the program
                return
        else:
            pip_info_send = """Process: Previous run mode is different or Start no is less than Initial run no {}, start from 1\n""".format(initial_run_times)
            pipe_process_to_gui.send("{}".format(pip_info_send))
            start_run_no = 1
            write_outfile_headers = True

    else:
        # If user selected to run new, write the headers of out files
        write_outfile_headers = True

    if write_outfile_headers:
        # Write outfile headers, including for both subarea level and basin level
        writeOutFileHeadersParmObjBsnlvl(
            parm_basin_level["Symbol"],
            bsn_parm_value_fn,
            bsn_parm_sel_fn,
            bsn_obj_fn
        )

        writeOutFileHeadersParmObjSublvl(
            cali_options["cali_mode"],
            all_outlet_detail,
            parm_sub_level["Symbol"],
            "outfiles_dds",
            GlobalVars.pair_varid_obs_header,
            sub_parm_value_outfn,
            sub_parm_select_outfn,
            sub_objfun_outfn
        )

    for runIdx in range(start_run_no, int(cali_dds["totalsimno"]) + 1):
        pip_info_send = """Process: >>>>>DDS Iteration no: {}<<<<<<<<""".format(runIdx)
        pipe_process_to_gui.send("{}".format(pip_info_send))

        if runIdx <= initial_run_times:
            # Define prob value to be 1.0
            probVal = 1.0
            # Modify parameters randomly
            if cali_dds["initparaidx"] == "random":
                pip_info_send = """Process: Updating parameters randomly"""
                pipe_process_to_gui.send("{}".format(pip_info_send))
                # Generate random values for parameter updating
                # For the parameter sets of each subarea group, the parameter is
                # stored in a dataframe and contain only subarea/hru level parameters
                # They will be updated one by one.
                if cali_options["cali_mode"] == "dist":
                    for ovid, outlet_detail in all_outlet_detail.items():
                        outlet_subgroup_id = outlet_detail["outletid"]
                        outlet_variable_name = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]
                        # Update parameter completely random.
                        total_number_sel_parm = outlet_detail["parm_sub"].shape[0]
                        random_value_array = numpy.random.rand(1, total_number_sel_parm)
                        outlet_detail["parm_sub"] = generateRandomParmValue(
                            outlet_detail["parm_sub"],
                            random_value_array)
                        # Update parameter values in file
                        pip_info_send = """Process: Updating parameters for outlet {} {}""".format(
                            outlet_subgroup_id, outlet_variable_name)
                        pipe_process_to_gui.send("{}".format(pip_info_send))

                        modifyParInFileSub(proj_path,
                                           fdname_running,
                                           sub_level_fname_for_groups,
                                           hru_level_fname_for_groups,
                                           outlet_detail["parm_sub"],
                                           outlet_subgroup_id,
                                           pipe_process_to_gui)
                        pip_info_send = """Process: Finished updating files for outlet {}""".format(
                            outlet_subgroup_id)
                        pipe_process_to_gui.send("{}".format(pip_info_send))
                # For the lump mode, only updating the not_grouped_subareas since
                # the list for other outlet is not added. Only one set of subarea
                # parameter sets will be used: all_outlet_detail["not_grouped_subareas"]
                elif cali_options["cali_mode"] == "lump":
                    total_number_sel_parm = all_outlet_detail["not_grouped_subareas"]["parm_sub"].shape[0]
                    random_value_array = numpy.random.rand(1, total_number_sel_parm)
                    all_outlet_detail["not_grouped_subareas"]["parm_sub"] = generateRandomParmValue(
                        all_outlet_detail["not_grouped_subareas"]["parm_sub"],
                        random_value_array)
                    # Update parameter values in file
                    pip_info_send = """Process: Updating all parameters"""
                    pipe_process_to_gui.send("{}".format(pip_info_send))

                    modifyParInFileSub(proj_path,
                                       fdname_running,
                                       sub_level_fname_for_groups,
                                       hru_level_fname_for_groups,
                                       all_outlet_detail["not_grouped_subareas"]["parm_sub"],
                                       "not_grouped_subareas",
                                       pipe_process_to_gui)
                    pip_info_send = """Process: Finished updating files"""
                    pipe_process_to_gui.send("{}".format(pip_info_send))

                if len(parm_basin_level.index) > 0:
                    totalNoSelParBsn = parm_basin_level.shape[0]
                    ranNumBsn = numpy.random.rand(1, totalNoSelParBsn)
                    parm_basin_level = generateRandomParmValue(parm_basin_level, ranNumBsn)
                    # After modifying parameter values in file,
                    modifyParInFileBsn(parm_basin_level,
                                       proj_path,
                                       fdname_running,
                                       pipe_process_to_gui)
                pip_info_send = """Process: Finished modifying swat input files !\n"""
                pipe_process_to_gui.send("{}".format(pip_info_send))

            elif (cali_dds["initparaidx"] == "initial"):
                pip_info_send = """Process: Updating parameters using initial values"""
                pipe_process_to_gui.send("{}".format(pip_info_send))
                if cali_options["cali_mode"] == "dist":
                    for ovid, outlet_detail in all_outlet_detail.items():
                        outlet_subgroup_id = outlet_detail["outletid"]
                        outlet_variable_name = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]
                        # Update parameter values in file
                        pip_info_send = """Process: Updating parameters for outlet {} {}""".format(
                            outlet_subgroup_id, outlet_variable_name)
                        pipe_process_to_gui.send("{}".format(pip_info_send))

                        # The test value was set to equal to the initial value.
                        # Thus, the modification will directly use the test value
                        modifyParInFileSub(proj_path,
                                           fdname_running,
                                           sub_level_fname_for_groups,
                                           hru_level_fname_for_groups,
                                           outlet_detail["parm_sub"],
                                           outlet_subgroup_id,
                                           pipe_process_to_gui)
                        pip_info_send = """Process: Finished updating files for outlet {}""".format(
                            outlet_subgroup_id)
                        pipe_process_to_gui.send("{}".format(pip_info_send))
                # For the lump mode, only updating the not_grouped_subareas since
                # the list for other outlet is not added. Only one set of subarea
                # parameter sets will be used: all_outlet_detail["not_grouped_subareas"]
                elif cali_options["cali_mode"] == "lump":
                    # Update parameter values in file
                    pip_info_send = """Process: Updating all parameters"""
                    pipe_process_to_gui.send("{}".format(pip_info_send))

                    modifyParInFileSub(proj_path,
                                       fdname_running,
                                       sub_level_fname_for_groups,
                                       hru_level_fname_for_groups,
                                       all_outlet_detail["not_grouped_subareas"]["parm_sub"],
                                       "not_grouped_subareas",
                                       pipe_process_to_gui)
                    pip_info_send = """Process: Finished updating files for outlet {}""".format(
                        outlet_subgroup_id)
                    pipe_process_to_gui.send("{}".format(pip_info_send))

                if len(parm_basin_level.index) > 0:
                    totalNoSelParBsn = parm_basin_level.shape[0]
                    ranNumBsn = numpy.random.rand(1, totalNoSelParBsn)

                    parm_basin_level = generateRandomParmValue(parm_basin_level, ranNumBsn)
                    # After modifying parameter values in file,
                    modifyParInFileBsn(parm_basin_level,
                                       proj_path,
                                       fdname_running,
                                       pipe_process_to_gui)
                pip_info_send = """Process: Finished modifying swat input files !\n"""
                pipe_process_to_gui.send("{}".format(pip_info_send))

        elif runIdx > initial_run_times:
            pip_info_send = """Process: Updating parameters using DDS"""
            pipe_process_to_gui.send("{}".format(pip_info_send))

            # Calculate the probability value of each run over total runs
            probVal = 1.0 - (numpy.log(runIdx) / numpy.log(int(cali_dds["totalsimno"])))

            # Generate random values for parameter updating
            # For the parameter sets of each subarea group, the parameter is
            # stored in a dataframe and contain only subarea/hru level parameters
            # They will be updated one by one.
            if cali_options["cali_mode"] == "dist":
                for ovid, outlet_detail in all_outlet_detail.items():
                    outlet_subgroup_id = outlet_detail["outletid"]
                    outlet_variable_name = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]
                    # Update parameter using DDS.

                    outlet_detail["parm_sub"] = generateDDSParVal(
                        outlet_detail["parm_sub"],
                        probVal,
                        float(cali_dds["pertubfactor"]))

                    # Update parameter values in file
                    pip_info_send = """Process: Updating parameters for outlet {} {}""".format(
                        outlet_subgroup_id, outlet_variable_name)
                    pipe_process_to_gui.send("{}".format(pip_info_send))

                    modifyParInFileSub(proj_path,
                                       fdname_running,
                                       sub_level_fname_for_groups,
                                       hru_level_fname_for_groups,
                                       outlet_detail["parm_sub"],
                                       outlet_subgroup_id,
                                       pipe_process_to_gui)
                    pip_info_send = """Process: Finished updating files for outlet {}""".format(
                        outlet_subgroup_id)
                    pipe_process_to_gui.send("{}".format(pip_info_send))
            # For the lump mode, only updating the not_grouped_subareas since
            # the list for other outlet is not added. Only one set of subarea
            # parameter sets will be used: all_outlet_detail["not_grouped_subareas"]
            elif cali_options["cali_mode"] == "lump":
                all_outlet_detail["not_grouped_subareas"]["parm_sub"] = generateDDSParVal(
                    all_outlet_detail["not_grouped_subareas"]["parm_sub"],
                    probVal,
                    float(cali_dds["pertubfactor"]))

                # Update parameter values in file
                pip_info_send = """Process: Updating all parameters"""
                pipe_process_to_gui.send("{}".format(pip_info_send))
                modifyParInFileSub(proj_path,
                                   fdname_running,
                                   sub_level_fname_for_groups,
                                   hru_level_fname_for_groups,
                                   all_outlet_detail["not_grouped_subareas"]["parm_sub"],
                                   "not_grouped_subareas",
                                   pipe_process_to_gui)
                pip_info_send = """Process: Finished updating files"""
                pipe_process_to_gui.send("{}".format(pip_info_send))

            if len(parm_basin_level.index) > 0:
                parm_basin_level = generateDDSParVal(
                    parm_basin_level,
                    probVal,
                    float(cali_dds["pertubfactor"]))

                # After modifying parameter values in file,
                modifyParInFileBsn(parm_basin_level,
                                   proj_path,
                                   fdname_running,
                                   pipe_process_to_gui)
            pip_info_send = """Process: Finished modifying swat input files !\n"""
            pipe_process_to_gui.send("{}".format(pip_info_send))

        # After modifying the parameters, run the swat model,
        # calculate statistics, and update best parameter values.
        # Run swat model after modifying the parameters
        # Run the swat model
        # Intiate the function with an individual Process, which do not share memory
        # with the main interface like using Thread.
        # Then get the commandline output into the pipe for display
        runSWATModel(GlobalVars.os_platform,
                     proj_path,
                     "workingdir",
                     GlobalVars.path_src_swat_exe,
                     pipe_process_to_gui)

        # Get reach file contents into dataframe for calculating statistics
        pip_info_send = """Process: Reading RCH output for calculation of objective functions"""
        pipe_process_to_gui.send("{}".format(pip_info_send))

        path_output_rch = os.path.join(proj_path, fdname_running, "output.rch")
        try:
            dataframe_outrch_whole = getRch2DF(path_output_rch,
                                               cali_options["iprint"],
                                               len(cali_options["all_outlets_reach"]))
        except IOError as e:
            showinfo("Warning",
                     """File {} does not exist: {}. Please double check your TxtInOut \
                    folder and make sure you have a complete set""".format(path_output_rch, e))
            return
        # Then construct series of observed and simulated pairs for stat calculation
        all_outlet_detail = buildObsSimPair(
            all_outlet_detail,
            dataframe_outrch_whole,
            GlobalVars.pair_varid_obs_header,
            cali_options)

        # Write the output pair into a file
        writePairToFile(all_outlet_detail,
                        fd_ts_eachrun,
                        runIdx,
                        GlobalVars.pair_varid_obs_header)

        all_outlet_detail = calAllStatEachOlt(
            all_outlet_detail,
            GlobalVars.pair_varid_obs_header)

        all_outlet_detail = calOltObjFunValue(all_outlet_detail)

        basin_obj_func_values["obj_basin_test"] = calOltBsnFunValue(
            all_outlet_detail,
            basin_obj_func_values["obj_basin_test"])

        all_outlet_detail, basin_obj_func_values, parm_basin_level = updateBestParmSubAndBasin(
            runIdx,
            all_outlet_detail,
            basin_obj_func_values,
            cali_options["cali_mode"],
            GlobalVars.pair_varid_obs_header,
            parm_basin_level,
            sub_parm_value_outfn,
            sub_objfun_outfn,
            sub_parm_select_outfn,
            bsn_parm_value_fn,
            bsn_parm_sel_fn,
            bsn_obj_fn,
            probVal,
            pipe_process_to_gui)

    pip_info_send = """Confirmation: DDS procedure finished"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """Confirmation: Calibration completed"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """bgrundone"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

##########################################################################
def runSensitivityAnalysis(pipe_process_to_gui,
                           sa_method_parm,
                           cali_options,
                           proj_path,
                           proj_parm
                           ):
    """
    This function is the main function for the sensitivity analysis.
    It includes the whole procedures, which include the following steps:
    1. get parameter sets
    2. preparing output file names
    3. generate parameter set
    4. modify parameters and run the model
    5. calculate the sensitivity analysis index for corresponding mode.
    :return:
    """
    pip_info_send = """Process: Sensitivity Analysis procedure start"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Create a folder to store the calibration and validation
    fdname_running = "workingdir"
    path_workingdir = os.path.join(proj_path, fdname_running)
    path_txtinout = os.path.join(proj_path, "txtinout")

    if not os.path.isdir(path_workingdir):
        os.mkdir(path_workingdir)

    pip_info_send = """Process: Copying files in the txtinout folder to the workingdir folder !\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Copy the txtinout contents into the purpose folder.
    copyTxtInOutContents(path_txtinout, path_workingdir)

    # get Subarea_groups based on calibration mode.
    # subarea_groups:
    # : Dictionary
    # : outlet: [list of subareas for this outlet]
    # If the user selected distributed mode, the groups will be
    # generated for each outlet. A new key named "not_grouped_subareas"
    # might be added if some subareas are excluded in groups for all outlets.

    # Here, the lump mode is used since all parameters will
    # be changed in the same way using the sampled values by
    # sa method
    subarea_groups = getSubGroupsForOutlet(
        cali_options["outlet_details"],
        "lump",
        proj_path)
    pip_info_send = """Process: Finished grouping subareas for each outlet !\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Get parameter lists
    parm_basin_level, parm_sub_level = getParmSets(
        proj_parm,
        GlobalVars.basin_file_exts,
        GlobalVars.sub_level_file_exts,
        GlobalVars.hru_level_file_exts)
    pip_info_send = """Process: Finished creating parameter database !\n"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Get observed data
    # This function added the key "df_obs" to the outlet_detail dict
    # outlet_detail = {key_number: {outlet_var: xxx, df_obs}}.
    all_outlet_detail = read_observed_data(
        cali_options,
        proj_path,
        GlobalVars.pair_varid_obs_header,
        GlobalVars.obs_data_header)

    # Also add the subarea lists to corresponding outlet var pairs.
    all_outlet_detail = addSubareaGroups(
        "lump",
        all_outlet_detail,
        subarea_groups)

    # Add parameter set for each outlet variable pairs.
    all_outlet_detail = initParmset(
        all_outlet_detail,
        parm_sub_level,
        GlobalVars.pair_varid_obs_header)

    sub_level_fname_for_groups, hru_level_fname_for_groups = initFilenameList(
        proj_path,
        subarea_groups)
    pip_info_send = """Process: Finished Initiating objective function value"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Update file.cio to match user specified simulation details
    updateFileCio(cali_options,
                  proj_path,
                  fdname_running,
                  GlobalVars.reach_var_list)

    pip_info_send = """Process: Finished updating the file.cio file"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """Process: Finished generating samples"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """Process: Sensitivity analysis procedure started"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    # Initial a counter to record the runs of random
    # counter_initial_runno: counter of run nos for initial runs
    basin_obj_func_values = {
        "obj_basin_test": 10000.0,
        "obj_basin_best": 10000.0}

    # Initialize output files for each outlet
    path_output = os.path.join(proj_path, "outfiles_sa")
    if not os.path.isdir(path_output):
        os.mkdir(path_output)

    # Create a folder to store the simulated values for plotting purpose
    fd_ts_eachrun = os.path.join(path_output, "timeseries")
    if not os.path.isdir(fd_ts_eachrun):
        os.mkdir(fd_ts_eachrun)

    # Initializing output files
    # Subarea level
    # Force Modify cali_options to be ""
    sub_parm_value_outfn, sub_parm_select_outfn, sub_objfun_outfn = initialOutFNameParmObjSublvl(
        "lump",
        all_outlet_detail,
        proj_path,
        "outfiles_sa",
        GlobalVars.pair_varid_obs_header)

    # Basin level
    bsn_parm_value_fn, bsn_parm_sel_fn, bsn_obj_fn = initialOutFNameParmObjBsnlvl(
        proj_path,
        "outfiles_sa",
        "lump")

    writeSAObjFunFileStatHdrs(all_outlet_detail,
                              sub_objfun_outfn,
                              bsn_obj_fn
                              )

    # Generate parameter set for
    fnp_parm_samples, sa_parm_sample_df, sa_parm_sample_array, sa_parm_problem = geneParmSamplesForSA(
        parm_basin_level,
        parm_sub_level,
        sa_method_parm,
        proj_path)

    pip_info_send = """Process: Total iterations : {}""".format(
        len(sa_parm_sample_df))
    pipe_process_to_gui.send("{}".format(pip_info_send))

    parm_sub_level_for_modify = copy.deepcopy(parm_sub_level)
    parm_basin_level_for_modify = copy.deepcopy(parm_basin_level)

    for sa_runidx in range(len(sa_parm_sample_df.index)):
        pip_info_send = """Process: Running Sensitivity analysis iteration {}""".format(
            sa_runidx + 1
        )
        pipe_process_to_gui.send("{}".format(pip_info_send))

        if len(parm_sub_level.index) > 0:
            parm_sub_level_for_modify = updateParmInDf(parm_sub_level_for_modify,
                                                       sa_parm_sample_df.loc[sa_runidx + 1, :])

            modifyParInFileSub(proj_path,
                               fdname_running,
                               sub_level_fname_for_groups,
                               hru_level_fname_for_groups,
                               parm_sub_level_for_modify,
                               "not_grouped_subareas",
                               pipe_process_to_gui)

        if len(parm_basin_level.index) > 0:
            parm_basin_level_for_modify = updateParmInDf(parm_basin_level_for_modify,
                                                         sa_parm_sample_df.loc[sa_runidx + 1, :])
            modifyParInFileBsn(parm_basin_level_for_modify,
                               proj_path,
                               fdname_running,
                               pipe_process_to_gui)

        # After modifying the parameters, run the swat model,
        # calculate statistics, and update best parameter values.
        # Run swat model after modifying the parameters
        # Run the swat model
        # Intiate the function with an individual Process, which do not share memory
        # with the main interface like using Thread.
        # Then get the commandline output into the pipe for display
        runSWATModel(GlobalVars.os_platform,
                     proj_path,
                     "workingdir",
                     GlobalVars.path_src_swat_exe,
                     pipe_process_to_gui)

        # Get reach file contents into dataframe for calculating statistics
        path_output_rch = os.path.join(proj_path, "workingdir", "output.rch")
        try:
            dataframe_outrch_whole = getRch2DF(path_output_rch,
                                               cali_options["iprint"],
                                               len(cali_options["all_outlets_reach"]))
        except IOError as e:
            showinfo("Warning",
                     """File {} does not exist: {}. Please double check your TxtInOut \
                    folder and make sure you have a complete set""".format(path_output_rch, e))

        # Then construct series of observed and simulated pairs for stat calculation
        all_outlet_detail = buildObsSimPair(
            all_outlet_detail,
            dataframe_outrch_whole,
            GlobalVars.pair_varid_obs_header,
            cali_options)

        # Write the output pair into a file
        writePairToFile(all_outlet_detail,
                        fd_ts_eachrun,
                        sa_runidx,
                        GlobalVars.pair_varid_obs_header)

        # calculate all statistics of all outlets
        all_outlet_detail = calAllStatEachOlt(
            all_outlet_detail,
            GlobalVars.pair_varid_obs_header)

        # calculate objective function values of all outlets
        all_outlet_detail = calOltObjFunValue(all_outlet_detail)

        basin_obj_func_values["obj_basin_test"] = calOltBsnFunValue(
            all_outlet_detail,
            basin_obj_func_values["obj_basin_test"])

        writeObjFunValtoFile(
            sa_runidx,
            all_outlet_detail,
            basin_obj_func_values,
            GlobalVars.pair_varid_obs_header,
            sub_objfun_outfn,
            bsn_obj_fn,
            pipe_process_to_gui)


    # After evalutaing the model with samples, run the analysis to get the sensitivity analysis
    # index for each outlet.
    calculateSAIndex(sa_parm_sample_array,
                     sa_parm_problem,
                     all_outlet_detail,
                     proj_path,
                     sa_method_parm,
                     sub_objfun_outfn)

    pip_info_send = """Process: Sensitivity Analysis procedure finished"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """bgrundone"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

##########################################################################
def runCalibrationPlots(pipe_process_to_gui,
                all_outlet_detail,
                proj_path,
                cali_mode,
                total_dds_iterations
                ):
    """
    Side process for generating user specified plots
    :param all_outlet_detail:
    :param proj_path:
    :param cali_mode:
    :param total_dds_iterations:
    :return:
    """
    pip_info_send = """Process: Start creating plots"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    for outlet_key, outlet_detail in all_outlet_detail.items():
        if not outlet_detail["outletid"] == "not_grouped_subareas":

            # Check whether the run index is out of the range of total iteration number
            if int(outlet_detail["plot_runno"]) > int(total_dds_iterations):
                showinfo("Warning",
                         """The run no you entered for outlet {} is larger than the total iterantions \
                        Please enter a number smaller than the number.""".format(outlet_detail["outletid"]))
                return
            else:

                generatingPlots(proj_path,
                                outlet_detail,
                                cali_mode,
                                outlet_detail["plot_runno"],
                                GlobalVars.pair_varid_obs_header,
                                "{}".format(int(outlet_detail["plot_runno"])),
                                "outfiles_dds",
                                pipe_process_to_gui)

    pip_info_send = """Process: Finished creating plots"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """bgrundone"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

def runUncertaintyPlot(pipe_process_to_gui,
                       all_outlet_detail,
                       proj_path,
                       cali_options,
                       total_sim_no
                       ):
    """
    Side process for generating uncertainty plots
    :param all_outlet_detail:
    :param proj_path:
    :param cali_mode:
    :param total_dds_iterations:
    :return:
    """
    # Get the run numbers that have objective functions larger than 0.5
    fdname_out_calibration = "outfiles_dds"
    fdname_observed = "observeddata"
    path_out_calibration = os.path.join(proj_path, fdname_out_calibration)
    path_ts_eachrun = os.path.join(path_out_calibration, "timeseries")

    all_outlet_detail = read_observed_data(
        cali_options,
        proj_path,
        GlobalVars.pair_varid_obs_header,
        GlobalVars.obs_data_header)

    pip_info_send = """Process: Getting Simulated values for each outlet"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    ts_obs_sim_all_runs = {}

    for olt_key, outlet_detail in all_outlet_detail.items():
        outlet_id = all_outlet_detail[olt_key]["outletid"]
        var_name_full = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]
        var_name = var_name_full.split("(")[0]

        # Get time series values
        for run_index in range(1, int(total_sim_no) + 1):
            fnp_sim_this_run = os.path.join(path_ts_eachrun,
                                            "obssimpair_{}_{}_{}.csv".format(
                                                outlet_detail["outletid"],
                                                var_name,
                                                run_index
                                            ))
            # Read in the parameter from the calibrated file
            timeseries_sub_whole = pandas.read_csv(
                fnp_sim_this_run, sep=",")

            mean_sim_run = timeseries_sub_whole["{}_y".format(var_name_full)].mean()
            if pandas.isna(mean_sim_run):
                continue

            # Get the observed and date in the frist run
            if run_index == 1:
                # Create an array to store simulated runs for all runs
                ts_obs_sim_all_runs[olt_key] = dict()
                ts_obs_sim_all_runs[olt_key]["Date"] = timeseries_sub_whole["Date"]
                ts_obs_sim_all_runs[olt_key]["Obs"] = timeseries_sub_whole["{}_x".format(var_name_full)]
                ts_obs_sim_all_runs[olt_key]["Sim"] = timeseries_sub_whole["{}_y".format(var_name_full)]
            # Stack the following arrays to the Simed_array
            elif run_index > 1:
                ts_obs_sim_all_runs[olt_key]["Sim"] = numpy.vstack(
                    (ts_obs_sim_all_runs[olt_key]["Sim"]
                     , timeseries_sub_whole["{}_y".format(var_name_full)])
                )

        # Making plots
        pip_info_send = """Process: Creating uncertainty plots for outlet {} with 95 percentile""".format(outlet_id)
        pipe_process_to_gui.send("{}".format(pip_info_send))

        generatingUncertaintyPlots(
            outlet_detail["outletid"],
            var_name,
            proj_path,
            ts_obs_sim_all_runs[olt_key],
            cali_options["best_run_no"]
        )
    # Making plots
    pip_info_send = """Confirmation: Finished creating uncertainty plots with 95 percentile"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

    pip_info_send = """bgrundone"""
    pipe_process_to_gui.send("{}".format(pip_info_send))

#
# # The following will be wrapped into a class for individual
# # process and communicating with the gui.
#
# class backgroundProcesses():
#
#     def __init__(self, pip: multiprocessing.Pipe()[0]) -> None:
#         self.pipe_process_to_gui = pip
#
#     ##########################################################################
#     def runDefaultSWAT(self,
#                        cali_options,
#                        proj_path):
#         """
#         run default and get stat for default swat model
#         :return:
#         """
#         # Create a folder to store the calibration and validation
#         fdname_running = "workingdir"
#         path_best_run = os.path.join(proj_path, fdname_running)
#         path_txtinout = os.path.join(proj_path, "txtinout")
#
#         if not os.path.isdir(path_best_run):
#             os.mkdir(path_best_run)
#
#         # Copy the txtinout contents into the purpose folder.
#         copyTxtInOutContents(path_txtinout, path_best_run)
#
#         # Update file.cio to match user specified simulation details
#         updateFileCio(cali_options,
#                       proj_path,
#                       fdname_running,
#                       GlobalVars.reach_var_list)
#         # Run the swat model
#         # Intiate the function with an individual Process, which do not share memory
#         # with the main interface like using Thread.
#         # Then get the commandline output into the pipe for display
#         runSWATModel(GlobalVars.os_platform,
#                     proj_path,
#                      "workingdir",
#                     GlobalVars.path_src_swat_exe,
#                     self.pipe_process_to_gui)
#
#         # Get observed data
#         # This function added the key "df_obs" to the outlet_detail dict
#         # outlet_detail = {key_number: {outlet_var: xxx, df_obs}}.
#
#         # Get reach file contents into dataframe for calculating statistics
#         path_output_rch = os.path.join(proj_path, "workingdir", "output.rch")
#         try:
#             dataframe_outrch_whole = getRch2DF(path_output_rch,
#                                                cali_options["iprint"],
#                                                len(cali_options["all_outlets_reach"]))
#         except IOError as e:
#             showinfo("Warning",
#                      """File {} does not exist: {}. Please double check your TxtInOut \
#                     folder and make sure you have a complete set""".format(path_output_rch, e))
#
#         all_outlet_detail = read_observed_data(
#             cali_options,
#             proj_path,
#             GlobalVars.pair_varid_obs_header,
#             GlobalVars.obs_data_header)
#
#         # Then construct series of observed and simulated pairs for stat calculation
#         all_outlet_detail = buildObsSimPair(
#             all_outlet_detail,
#             dataframe_outrch_whole,
#             GlobalVars.pair_varid_obs_header,
#             cali_options)
#
#         all_outlet_detail = calAllStatEachOlt(
#             all_outlet_detail,
#             GlobalVars.pair_varid_obs_header)
#
#         pip_info_send = """Confirmation: Finished reading observed data"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         all_outlet_detail = calOltObjFunValue(all_outlet_detail)
#
#         basin_obj_func_values = {
#             "obj_basin_test": 1000,
#             "obj_basin_best": 1000}
#
#         basin_obj_func_values["obj_basin_test"] = calOltBsnFunValue(
#             all_outlet_detail,
#             basin_obj_func_values["obj_basin_test"])
#
#         # Display the output in gui
#         for outlet_key, outlet_detail in all_outlet_detail.items():
#             pip_info_send = """Output: Objective function for outlet no {} is {:.2f}!""".format(
#                 outlet_detail["outletid"], outlet_detail["test_obj_dist"]
#             )
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#             pip_info_send = """Output: R2 for outlet no {} is {:.2f}!""".format(
#                 outlet_detail["outletid"], outlet_detail["r2_value"])
#
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#             pip_info_send = """Output: NSE for outlet no {} is {:.2f}!""".format(
#                 outlet_detail["outletid"], outlet_detail["nse_value"])
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#             pip_info_send = """Output: Pbias for outlet no {} is {:.2f}!""".format(
#                 outlet_detail["outletid"], outlet_detail["pbias_value"])
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#             pip_info_send = """Output: RMSE for outlet no {} is {:.2f}!""".format(
#                 outlet_detail["outletid"], outlet_detail["rmse_value"])
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#             pip_info_send = """Output: MSE for outlet no {} is {:.2f}!""".format(
#                 outlet_detail["outletid"], outlet_detail["mse_value"])
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#
#
#     ##########################################################################
#     def runSWATBestParmSet(self,
#                        cali_options,
#                        proj_path,
#                        proj_parm,
#                        cali_dds):
#         """
#         run swat model with the best parameter set
#         and get stat for default swat model
#         :return:
#         """
#         # Create a folder to store the calibration and validation
#         fdname_running = "best_run_{}".format(cali_options["bestrun_purpose"])
#         fdname_best_outfiles = "outfiles_best_run"
#
#         path_best_outfiles = os.path.join(proj_path, fdname_best_outfiles)
#         path_best_run = os.path.join(proj_path, fdname_running)
#         path_txtinout = os.path.join(proj_path, "txtinout")
#
#         # Create a folder to store the simulated values for plotting purpose
#         fd_ts_eachrun = os.path.join(proj_path, fdname_best_outfiles, "timeseries")
#         if not os.path.isdir(fd_ts_eachrun):
#             os.mkdir(fd_ts_eachrun)
#
#         if not os.path.isdir(path_best_run):
#             os.mkdir(path_best_run)
#
#         if not os.path.isdir(path_best_outfiles):
#             os.mkdir(path_best_outfiles)
#
#         pip_info_send = """Process: copying files from the {}""".format(path_txtinout)
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#         pip_info_send = """Process: to the {}""".format(path_best_run)
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Copy the txtinout contents into the purpose folder.
#         # copyTxtInOutContents(path_txtinout, path_best_run)
#
#         # Update file.cio to match user specified simulation details
#         updateFileCio(cali_options,
#                       proj_path,
#                       fdname_running,
#                       GlobalVars.reach_var_list)
#         pip_info_send = """Process: Finished updating file.cio"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # get Subarea_groups based on calibration mode.
#         # subarea_groups:
#         # : Dictionary
#         # : outlet: [list of subareas for this outlet]
#         # If the user selected distributed mode, the groups will be
#         # generated for each outlet. A new key named "not_grouped_subareas"
#         # might be added if some subareas are excluded in groups for all outlets.
#         subarea_groups = getSubGroupsForOutlet(
#             cali_options["outlet_details"],
#             cali_options["cali_mode"],
#             proj_path)
#         pip_info_send = """Process: Finished grouping subareas for each outlet !\n"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Get parameter lists
#         parm_basin_level, parm_sub_level = getParmSets(
#             proj_parm,
#             GlobalVars.basin_file_exts,
#             GlobalVars.sub_level_file_exts,
#             GlobalVars.hru_level_file_exts)
#         pip_info_send = """Process: Finished creating parameter database !\n"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         all_outlet_detail = read_observed_data(
#             cali_options,
#             proj_path,
#             GlobalVars.pair_varid_obs_header,
#             GlobalVars.obs_data_header)
#
#         # Also add the subarea lists to corresponding outlet var pairs.
#         all_outlet_detail = addSubareaGroups(
#             cali_options["cali_mode"],
#             all_outlet_detail,
#             subarea_groups)
#
#         # Subarea level
#         sub_parm_value_outfn_best, sub_objfun_outfn_best, sub_parm_select_outfn_best = initialOutFileParmObjSublvl(
#             cali_options,
#             all_outlet_detail,
#             parm_sub_level["Symbol"],
#             proj_path,
#             fdname_best_outfiles,
#             GlobalVars.pair_varid_obs_header)
#         # Basin level
#         bsn_parm_value_outfn_best, bsn_parm_sel_outfn_best = initOutFileParmObjBsnlvl(
#             parm_basin_level,
#             proj_path,
#             fdname_best_outfiles,
#             cali_options["cali_mode"])
#
#         pip_info_send = """Process: Finished initializing output files\n"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Add parameter set for each outlet variable pairs.
#         all_outlet_detail = initParmset(
#             all_outlet_detail,
#             parm_sub_level,
#             GlobalVars.pair_varid_obs_header)
#
#         sub_level_fname_for_groups, hru_level_fname_for_groups = initFilenameList(
#             proj_path,
#             subarea_groups)
#         pip_info_send = """Process: Finished Initiating objective function value"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         all_outlet_detail, parm_basin_level_best = getUsrBestParmSet(
#             all_outlet_detail,
#             parm_basin_level,
#             cali_options,
#             proj_path,
#             "outfiles_calibration",
#             GlobalVars.pair_varid_obs_header
#         )
#
#         pip_info_send = """Process: Finished updating files with best parameter"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         basin_obj_func_values = {
#             "obj_basin_test": 1000,
#             "obj_basin_best": 1000}
#
#         # Modify the input files with best parameters
#         # For the parameter sets of each subarea group, the parameter is
#         # stored in a dataframe and contain only subarea/hru level parameters
#         # They will be updated one by one.
#         if cali_options["cali_mode"] == "dist":
#             for ovid, outlet_detail in all_outlet_detail.items():
#                 outlet_subgroup_id = outlet_detail["outletid"]
#                 outlet_variable_name = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]
#
#                 # Update parameter values in file
#                 pip_info_send = """Process: Updating parameters for outlet {} {}""".format(
#                     outlet_subgroup_id, outlet_variable_name)
#                 self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                 modifyParInFileSub(proj_path,
#                                    sub_level_fname_for_groups,
#                                    hru_level_fname_for_groups,
#                                    outlet_detail["parm_sub"],
#                                    outlet_subgroup_id,
#                                    self.pipe_process_to_gui)
#                 pip_info_send = """Process: Finished updating files for outlet {}""".format(
#                     outlet_subgroup_id)
#                 self.pipe_process_to_gui.send("{}".format(pip_info_send))
#         # For the lump mode, only updating the not_grouped_subareas since
#         # the list for other outlet is not added. Only one set of subarea
#         # parameter sets will be used: all_outlet_detail["not_grouped_subareas"]
#         elif cali_options["cali_mode"] == "lump":
#             # Update parameter values in file
#             pip_info_send = """Process: Updating all parameters"""
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#             modifyParInFileSub(proj_path,
#                                sub_level_fname_for_groups,
#                                hru_level_fname_for_groups,
#                                all_outlet_detail["not_grouped_subareas"]["parm_sub"],
#                                "not_grouped_subareas",
#                                self.pipe_process_to_gui)
#             pip_info_send = """Process: Finished updating files"""
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         if len(parm_basin_level.index) > 0:
#             # After modifying parameter values in file,
#             modifyParInFileBsn(parm_basin_level,
#                                proj_path,
#                                self.pipe_process_to_gui)
#         pip_info_send = """Process: Finished modifying swat input files !\n"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Run the swat model
#         # Intiate the function with an individual Process, which do not share memory
#         # with the main interface like using Thread.
#         # Then get the commandline output into the pipe for display
#         runSWATModel(GlobalVars.os_platform,
#                     proj_path,
#                     fdname_running,
#                     GlobalVars.path_src_swat_exe,
#                     self.pipe_process_to_gui)
#
#         # Get reach file contents into dataframe for calculating statistics
#         path_output_rch = os.path.join(proj_path, "workingdir", "output.rch")
#         try:
#             dataframe_outrch_whole = getRch2DF(path_output_rch,
#                                                cali_options["iprint"],
#                                                len(cali_options["all_outlets_reach"]))
#         except IOError as e:
#             showinfo("Warning",
#                      """File {} does not exist: {}. Please double check your TxtInOut \
#                     folder and make sure you have a complete set""".format(path_output_rch, e))
#             return
#         # Then construct series of observed and simulated pairs for stat calculation
#         all_outlet_detail = buildObsSimPair(
#             all_outlet_detail,
#             dataframe_outrch_whole,
#             GlobalVars.pair_varid_obs_header,
#             cali_options)
#
#         # Write the output pair into a file
#         writePairToFile(all_outlet_detail,
#                         fd_ts_eachrun,
#                         "best_run",
#                         GlobalVars.pair_varid_obs_header)
#
#         all_outlet_detail = calAllStatEachOlt(
#             all_outlet_detail,
#             GlobalVars.pair_varid_obs_header)
#
#         all_outlet_detail = calOltObjFunValue(all_outlet_detail)
#
#         basin_obj_func_values["obj_basin_test"] = calOltBsnFunValue(
#             all_outlet_detail,
#             basin_obj_func_values["obj_basin_test"])
#
#         all_outlet_detail, basin_obj_func_values, parm_basin_level = updateBestParmSubAndBasin(
#                 "best_run",
#                 all_outlet_detail,
#                 basin_obj_func_values,
#                 cali_options["cali_mode"],
#                 GlobalVars.pair_varid_obs_header,
#                 parm_basin_level,
#                 sub_parm_value_outfn_best,
#                 sub_objfun_outfn_best,
#                 sub_parm_select_outfn_best,
#                 bsn_parm_value_outfn_best,
#                 bsn_parm_sel_outfn_best,
#                 1.0,
#                 self.pipe_process_to_gui)
#
#         pip_info_send = """Confirmation: DDS procedure finished"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         pip_info_send = """Confirmation: Calibration completed"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#
#
#
#     ##########################################################################
#     def runCalibration(self,
#                        cali_options,
#                        proj_path,
#                        proj_parm,
#                        cali_dds):
#         """
#         run default and get stat for default swat model
#         To run the model, the original code need to be transferred here.
#         And the output will be copied into the List box.
#         These include:
#         1. read observed dataset
#         :return:
#         """
#         # Create a folder to store the calibration and validation
#         fdname_running = "workingdir"
#         path_workingdir = os.path.join(proj_path, fdname_running)
#         path_txtinout = os.path.join(proj_path, "txtinout")
#
#         if not os.path.isdir(path_workingdir):
#             os.mkdir(path_workingdir)
#
#         # Copy the txtinout contents into the purpose folder.
#         copyTxtInOutContents(path_txtinout, path_workingdir)
#
#         # get Subarea_groups based on calibration mode.
#         # subarea_groups:
#         # : Dictionary
#         # : outlet: [list of subareas for this outlet]
#         # If the user selected distributed mode, the groups will be
#         # generated for each outlet. A new key named "not_grouped_subareas"
#         # might be added if some subareas are excluded in groups for all outlets.
#         subarea_groups = getSubGroupsForOutlet(
#             cali_options["outlet_details"],
#             cali_options["cali_mode"],
#             proj_path)
#         pip_info_send = """Process: Finished grouping subareas for each outlet !\n"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Get parameter lists
#         parm_basin_level, parm_sub_level = getParmSets(
#             proj_parm,
#             GlobalVars.basin_file_exts,
#             GlobalVars.sub_level_file_exts,
#             GlobalVars.hru_level_file_exts)
#         pip_info_send = """Process: Finished creating parameter database !\n"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Get observed data
#         # This function added the key "df_obs" to the outlet_detail dict
#         # outlet_detail = {key_number: {outlet_var: xxx, df_obs}}.
#         all_outlet_detail = read_observed_data(
#             cali_options,
#             proj_path,
#             GlobalVars.pair_varid_obs_header,
#             GlobalVars.obs_data_header)
#
#         # Also add the subarea lists to corresponding outlet var pairs.
#         all_outlet_detail = addSubareaGroups(
#             cali_options["cali_mode"],
#             all_outlet_detail,
#             subarea_groups)
#         # Initializing output files
#         # Subarea level
#         sub_parm_value_outfn, sub_objfun_outfn, sub_parm_select_outfn = initialOutFileParmObjSublvl(
#             cali_options,
#             all_outlet_detail,
#             parm_sub_level["Symbol"],
#             proj_path,
#             "outfiles_calibration",
#             GlobalVars.pair_varid_obs_header)
#         # Basin level
#         bsn_parm_value_outfn, bsn_parm_sel_outfn = initOutFileParmObjBsnlvl(
#             parm_basin_level,
#             proj_path,
#             "outfiles_calibration",
#             cali_options["cali_mode"])
#
#         pip_info_send = """Process: Finished initializing output files\n"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Add parameter set for each outlet variable pairs.
#         all_outlet_detail = initParmset(
#             all_outlet_detail,
#             parm_sub_level,
#             GlobalVars.pair_varid_obs_header)
#
#         sub_level_fname_for_groups, hru_level_fname_for_groups = initFilenameList(
#             proj_path,
#             subarea_groups)
#         pip_info_send = """Process: Finished Initiating objective function value"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Update file.cio to match user specified simulation details
#         updateFileCio(cali_options,
#                       proj_path,
#                       fdname_running,
#                       GlobalVars.reach_var_list)
#
#         pip_info_send = """Process: Finished updating the file.cio file"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         pip_info_send = """Process: DDS procedure started"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         pip_info_send = """Process: Total iteration no: {}""".format(
#             cali_dds["totalsimno"])
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Two situations:
#         # User select to use random parameter initParmIdx == random
#         # User select to use default parameter initParmIdx == initial
#
#         # Initial a counter to record the runs of random
#         # counter_initial_runno: counter of run nos for initial runs
#         basin_obj_func_values = {
#             "obj_basin_test": 1000,
#             "obj_basin_best": 1000}
#
#         # Deal with the different ways of several initial runs.
#         if cali_dds["initparaidx"] == "random":
#             initial_run_times = math.ceil(0.005 * int(cali_dds["totalsimno"]))
#         elif cali_dds["initparaidx"] == "initial":
#             initial_run_times = 1
#
#         # Create a folder to store the simulated values for plotting purpose
#         fd_ts_eachrun = os.path.join(proj_path, "outfiles_calibration", "timeseries")
#         if not os.path.isdir(fd_ts_eachrun):
#             os.mkdir(fd_ts_eachrun)
#
#         # Get the number of previous runs if restart mode = Continue
#         start_run_no = 1
#         if cali_dds["restartmech"] == "continue":
#             start_run_no = getPreviousRunNo(
#                 sub_objfun_outfn,
#                 all_outlet_detail)
#
#         for runIdx in range(start_run_no, int(cali_dds["totalsimno"]) + 1):
#             pip_info_send = """Process: >>>>>DDS Iteration no: {}<<<<<<<<""".format(runIdx)
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#             if runIdx <= initial_run_times:
#                 # Define prob value to be 1.0
#                 probVal = 1.0
#                 # Modify parameters randomly
#                 if cali_dds["initparaidx"] == "random":
#                     pip_info_send = """Process: Updating parameters randomly"""
#                     self.pipe_process_to_gui.send("{}".format(pip_info_send))
#                     # Generate random values for parameter updating
#                     # For the parameter sets of each subarea group, the parameter is
#                     # stored in a dataframe and contain only subarea/hru level parameters
#                     # They will be updated one by one.
#                     if cali_options["cali_mode"] == "dist":
#                         for ovid, outlet_detail in all_outlet_detail.items():
#                             outlet_subgroup_id = outlet_detail["outletid"]
#                             outlet_variable_name = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]
#                             # Update parameter completely random.
#                             total_number_sel_parm = outlet_detail["parm_sub"].shape[0]
#                             random_value_array = numpy.random.rand(1, total_number_sel_parm)
#                             outlet_detail["parm_sub"] = generateRandomParmValue(
#                                 outlet_detail["parm_sub"],
#                                 random_value_array)
#                             # Update parameter values in file
#                             pip_info_send = """Process: Updating parameters for outlet {} {}""".format(
#                                 outlet_subgroup_id, outlet_variable_name)
#                             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                             modifyParInFileSub(proj_path,
#                                                sub_level_fname_for_groups,
#                                                hru_level_fname_for_groups,
#                                                outlet_detail["parm_sub"],
#                                                outlet_subgroup_id,
#                                                self.pipe_process_to_gui)
#                             pip_info_send = """Process: Finished updating files for outlet {}""".format(
#                                 outlet_subgroup_id)
#                             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#                     # For the lump mode, only updating the not_grouped_subareas since
#                     # the list for other outlet is not added. Only one set of subarea
#                     # parameter sets will be used: all_outlet_detail["not_grouped_subareas"]
#                     elif cali_options["cali_mode"] == "lump":
#                         total_number_sel_parm = all_outlet_detail["not_grouped_subareas"]["parm_sub"].shape[0]
#                         random_value_array = numpy.random.rand(1, total_number_sel_parm)
#                         all_outlet_detail["not_grouped_subareas"]["parm_sub"] = generateRandomParmValue(
#                             all_outlet_detail["not_grouped_subareas"]["parm_sub"],
#                             random_value_array)
#                         # Update parameter values in file
#                         pip_info_send = """Process: Updating all parameters"""
#                         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                         modifyParInFileSub(proj_path,
#                                sub_level_fname_for_groups,
#                                hru_level_fname_for_groups,
#                                all_outlet_detail["not_grouped_subareas"]["parm_sub"],
#                                "not_grouped_subareas",
#                                self.pipe_process_to_gui)
#                         pip_info_send = """Process: Finished updating files"""
#                         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                     if len(parm_basin_level.index) > 0:
#                         totalNoSelParBsn = parm_basin_level.shape[0]
#                         ranNumBsn = numpy.random.rand(1, totalNoSelParBsn)
#                         parm_basin_level = generateRandomParmValue(parm_basin_level, ranNumBsn)
#                         # After modifying parameter values in file,
#                         modifyParInFileBsn(parm_basin_level,
#                                            proj_path,
#                                            self.pipe_process_to_gui)
#                     pip_info_send = """Process: Finished modifying swat input files !\n"""
#                     self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                 elif (cali_dds["initparaidx"] == "initial"):
#                     pip_info_send = """Process: Updating parameters using initial values"""
#                     self.pipe_process_to_gui.send("{}".format(pip_info_send))
#                     if cali_options["cali_mode"] == "dist":
#                         for ovid, outlet_detail in all_outlet_detail.items():
#                             outlet_subgroup_id = outlet_detail["outletid"]
#                             outlet_variable_name = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]
#                             # Update parameter values in file
#                             pip_info_send = """Process: Updating parameters for outlet {} {}""".format(
#                                 outlet_subgroup_id, outlet_variable_name)
#                             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                             # The test value was set to equal to the initial value.
#                             # Thus, the modification will directly use the test value
#                             modifyParInFileSub(proj_path,
#                                                sub_level_fname_for_groups,
#                                                hru_level_fname_for_groups,
#                                                outlet_detail["parm_sub"],
#                                                outlet_subgroup_id,
#                                                self.pipe_process_to_gui)
#                             pip_info_send = """Process: Finished updating files for outlet {}""".format(
#                                 outlet_subgroup_id)
#                             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#                     # For the lump mode, only updating the not_grouped_subareas since
#                     # the list for other outlet is not added. Only one set of subarea
#                     # parameter sets will be used: all_outlet_detail["not_grouped_subareas"]
#                     elif cali_options["cali_mode"] == "lump":
#                         # Update parameter values in file
#                         pip_info_send = """Process: Updating all parameters"""
#                         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                         modifyParInFileSub(proj_path,
#                                            sub_level_fname_for_groups,
#                                            hru_level_fname_for_groups,
#                                            all_outlet_detail["not_grouped_subareas"]["parm_sub"],
#                                            "not_grouped_subareas",
#                                            self.pipe_process_to_gui)
#                         pip_info_send = """Process: Finished updating files for outlet {}""".format(
#                             outlet_subgroup_id)
#                         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                     if len(parm_basin_level.index) > 0:
#                         totalNoSelParBsn = parm_basin_level.shape[0]
#                         ranNumBsn = numpy.random.rand(1, totalNoSelParBsn)
#
#                         parm_basin_level = generateRandomParmValue(parm_basin_level, ranNumBsn)
#                         # After modifying parameter values in file,
#                         modifyParInFileBsn(parm_basin_level,
#                                            proj_path,
#                                            self.pipe_process_to_gui)
#                     pip_info_send = """Process: Finished modifying swat input files !\n"""
#                     self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#             elif runIdx > initial_run_times:
#                 pip_info_send = """Process: Updating parameters using DDS"""
#                 self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                 # Calculate the probability value of each run over total runs
#                 probVal = 1.0 - (numpy.log(runIdx) / numpy.log(int(cali_dds["totalsimno"])))
#
#                 # Generate random values for parameter updating
#                 # For the parameter sets of each subarea group, the parameter is
#                 # stored in a dataframe and contain only subarea/hru level parameters
#                 # They will be updated one by one.
#                 if cali_options["cali_mode"] == "dist":
#                     for ovid, outlet_detail in all_outlet_detail.items():
#                         outlet_subgroup_id = outlet_detail["outletid"]
#                         outlet_variable_name = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]
#                         # Update parameter using DDS.
#                         outlet_detail["parm_sub"] = generateDDSParVal(
#                             outlet_detail["parm_sub"],
#                             probVal,
#                             float(cali_dds["pertubfactor"]))
#
#                         # Update parameter values in file
#                         pip_info_send = """Process: Updating parameters for outlet {} {}""".format(
#                             outlet_subgroup_id, outlet_variable_name)
#                         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                         modifyParInFileSub(proj_path,
#                                            sub_level_fname_for_groups,
#                                            hru_level_fname_for_groups,
#                                            outlet_detail["parm_sub"],
#                                            outlet_subgroup_id,
#                                            self.pipe_process_to_gui)
#                         pip_info_send = """Process: Finished updating files for outlet {}""".format(
#                             outlet_subgroup_id)
#                         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#                 # For the lump mode, only updating the not_grouped_subareas since
#                 # the list for other outlet is not added. Only one set of subarea
#                 # parameter sets will be used: all_outlet_detail["not_grouped_subareas"]
#                 elif cali_options["cali_mode"] == "lump":
#                     all_outlet_detail["not_grouped_subareas"]["parm_sub"] = generateDDSParVal(
#                         all_outlet_detail["not_grouped_subareas"]["parm_sub"],
#                         probVal,
#                         float(cali_dds["pertubfactor"]))
#
#                     # Update parameter values in file
#                     pip_info_send = """Process: Updating all parameters"""
#                     self.pipe_process_to_gui.send("{}".format(pip_info_send))
#                     modifyParInFileSub(proj_path,
#                                        sub_level_fname_for_groups,
#                                        hru_level_fname_for_groups,
#                                        all_outlet_detail["not_grouped_subareas"]["parm_sub"],
#                                        "not_grouped_subareas",
#                                        self.pipe_process_to_gui)
#                     pip_info_send = """Process: Finished updating files"""
#                     self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#                 if len(parm_basin_level.index) > 0:
#                     parm_basin_level = generateDDSParVal(
#                         parm_basin_level,
#                         probVal,
#                         float(cali_dds["pertubfactor"]))
#
#                     # After modifying parameter values in file,
#                     modifyParInFileBsn(parm_basin_level,
#                                        proj_path,
#                                        self.pipe_process_to_gui)
#                 pip_info_send = """Process: Finished modifying swat input files !\n"""
#                 self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#             # After modifying the parameters, run the swat model,
#             # calculate statistics, and update best parameter values.
#             # Run swat model after modifying the parameters
#             # Run the swat model
#             # Intiate the function with an individual Process, which do not share memory
#             # with the main interface like using Thread.
#             # Then get the commandline output into the pipe for display
#             runSWATModel(GlobalVars.os_platform,
#                         proj_path,
#                          "workingdir",
#                         GlobalVars.path_src_swat_exe,
#                         self.pipe_process_to_gui)
#
#             # Get reach file contents into dataframe for calculating statistics
#             path_output_rch = os.path.join(proj_path, "workingdir", "output.rch")
#             try:
#                 dataframe_outrch_whole = getRch2DF(path_output_rch,
#                                                    cali_options["iprint"],
#                                                    len(cali_options["all_outlets_reach"]))
#             except IOError as e:
#                 showinfo("Warning",
#                          """File {} does not exist: {}. Please double check your TxtInOut \
#                         folder and make sure you have a complete set""".format(path_output_rch, e))
#                 return
#             # Then construct series of observed and simulated pairs for stat calculation
#             all_outlet_detail = buildObsSimPair(
#                 all_outlet_detail,
#                 dataframe_outrch_whole,
#                 GlobalVars.pair_varid_obs_header,
#                 cali_options)
#
#             # Write the output pair into a file
#             writePairToFile(all_outlet_detail,
#                             fd_ts_eachrun,
#                             runIdx,
#                             GlobalVars.pair_varid_obs_header)
#
#             all_outlet_detail = calAllStatEachOlt(
#                 all_outlet_detail,
#                 GlobalVars.pair_varid_obs_header)
#
#             all_outlet_detail = calOltObjFunValue(all_outlet_detail)
#
#             basin_obj_func_values["obj_basin_test"] = calOltBsnFunValue(
#                 all_outlet_detail,
#                 basin_obj_func_values["obj_basin_test"])
#
#             all_outlet_detail, basin_obj_func_values, parm_basin_level = updateBestParmSubAndBasin(
#                 runIdx,
#                 all_outlet_detail,
#                 basin_obj_func_values,
#                 cali_options["cali_mode"],
#                 GlobalVars.pair_varid_obs_header,
#                 parm_basin_level,
#                 sub_parm_value_outfn,
#                 sub_objfun_outfn,
#                 sub_parm_select_outfn,
#                 bsn_parm_value_outfn,
#                 bsn_parm_sel_outfn,
#                 probVal,
#                 self.pipe_process_to_gui)
#
#         pip_info_send = """Confirmation: DDS procedure finished"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         pip_info_send = """Confirmation: Calibration completed"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#     ##########################################################################
#     def runSensitivityAnalysis(self,
#                                sa_method_parm,
#                                cali_options,
#                                proj_path,
#                                proj_parm
#                                ):
#         """
#         This function is the main function for the sensitivity analysis.
#         It includes the whole procedures, which include the following steps:
#         1. get parameter sets
#         2. preparing output file names
#         3. generate parameter set
#         4. modify parameters and run the model
#         5. calculate the sensitivity analysis index for corresponding mode.
#         :return:
#         """
#         pip_info_send = """Process: Sensitivity Analysis procedure start"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Preparation procedures
#         # get Subarea_groups based on calibration mode.
#         # subarea_groups:
#         # : Dictionary
#         # : outlet: [list of subareas for this outlet]
#         # If the user selected distributed mode, the groups will be
#         # generated for each outlet. A new key named "not_grouped_subareas"
#         # might be added if some subareas are excluded in groups for all outlets.
#         subarea_groups = getSubGroupsForOutlet(
#             cali_options["outlet_details"],
#             sa_method_parm["sa_mode"],
#             proj_path)
#
#         # Only one set of parameter values will be used for sensitivity analysis
#         subarea_groups_not_grouped = getSubGroupsForOutlet(
#             cali_options["outlet_details"],
#             "lump",
#             proj_path)
#
#         pip_info_send = """Process: Finished grouping subareas"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         sub_level_fname_for_groups, hru_level_fname_for_groups = initFilenameList(
#             proj_path,
#             subarea_groups)
#
#         # Get parameter lists
#         parm_basin_level, parm_sub_level = getParmSets(
#             proj_parm,
#             GlobalVars.basin_file_exts,
#             GlobalVars.sub_level_file_exts,
#             GlobalVars.hru_level_file_exts)
#
#         pip_info_send = """Process: Finished creating parameter database"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         # Generate parameter set for
#         fnp_parm_samples, sa_parm_sample_df, sa_parm_sample_array, sa_parm_problem = geneParmSamplesForSA(
#             parm_basin_level,
#             parm_sub_level,
#             sa_method_parm,
#             proj_path)
#         pip_info_send = """Process: Finished generating samples"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         all_outlet_detail = generateAllOutletDetails(
#             cali_options["outlet_details"],
#             len(sa_parm_sample_df))
#
#         # Initialize output files for each outlet
#         sa_fnout_avgvar = initialOutFileSA(
#             all_outlet_detail,
#             proj_path)
#
#         pip_info_send = """Process: Total iterations for Sensitivity analysis: {}""".format(
#             len(sa_parm_sample_df)
#         )
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         parm_sub_level_for_modify = copy.deepcopy(parm_sub_level)
#         parm_basin_level_for_modify = copy.deepcopy(parm_basin_level)
#
#         for sa_runidx in range(len(sa_parm_sample_df.index)):
#             pip_info_send = """Process: Running Sensitivity analysis iteration {}""".format(
#                 sa_runidx + 1
#             )
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#             if len(parm_sub_level.index) > 0:
#                 parm_sub_level_for_modify = updateParmInDf(parm_sub_level_for_modify,
#                                                            sa_parm_sample_df.loc[sa_runidx + 1, :])
#                 modifyParInFileSub(proj_path,
#                                    sub_level_fname_for_groups,
#                                    hru_level_fname_for_groups,
#                                    parm_sub_level_for_modify,
#                                    "not_grouped_subareas",
#                                    self.pipe_process_to_gui)
#
#             if len(parm_basin_level.index) > 0:
#                 parm_basin_level_for_modify = updateParmInDf(parm_basin_level_for_modify,
#                                                              sa_parm_sample_df.loc[sa_runidx + 1, :])
#                 modifyParInFileBsn(parm_basin_level_for_modify,
#                                    proj_path,
#                                    self.pipe_process_to_gui)
#
#             # After modifying the parameters, run the swat model,
#             # calculate statistics, and update best parameter values.
#             # Run swat model after modifying the parameters
#             # Run the swat model
#             # Intiate the function with an individual Process, which do not share memory
#             # with the main interface like using Thread.
#             # Then get the commandline output into the pipe for display
#             runSWATModel(GlobalVars.os_platform,
#                          proj_path,
#                          "workingdir",
#                          GlobalVars.path_src_swat_exe,
#                          self.pipe_process_to_gui)
#
#             # Get reach file contents into dataframe for calculating statistics
#             path_output_rch = os.path.join(proj_path, "workingdir", "output.rch")
#             try:
#                 dataframe_outrch_whole = getRch2DF(path_output_rch,
#                                                    cali_options["iprint"],
#                                                    len(cali_options["all_outlets_reach"]))
#             except IOError as e:
#                 showinfo("Warning",
#                          """File {} does not exist: {}. Please double check your TxtInOut \
#                         folder and make sure you have a complete set""".format(path_output_rch, e))
#
#             # Extract output values for evaluation
#             # The average value over the time step for the corresponding variable
#             # of each outlet will be extracted
#             all_outlet_detail = extractSimValuesEachGroup(
#                 sa_fnout_avgvar,
#                 all_outlet_detail,
#                 cali_options,
#                 dataframe_outrch_whole,
#                 GlobalVars.pair_varid_obs_header,
#                 sa_runidx)
#
#         # After evalutaing the model with samples, run the analysis to get the sensitivity analysis
#         # index for each outlet.
#         calculateSAIndex(sa_parm_sample_array,
#                          sa_parm_problem,
#                          all_outlet_detail,
#                          proj_path,
#                          sa_method_parm)
#
#         # if sa_method_parm["sa_mode"] == "dist":
#         #     pip_info_send = """Process: Conducting sensitivity analysis in the Distributed mode."""
#         #     self.pipe_process_to_gui.send("{}".format(pip_info_send))
#         #
#         # elif sa_method_parm["sa_mode"] == "lump":
#         #     pip_info_send = """Process: Conducting sensitivity analysis in the Lumped mode."""
#         #     self.pipe_process_to_gui.send("{}".format(pip_info_send))
#         #
#         #     print(subarea_groups)
#
#         pip_info_send = """Process: Sensitivity Analysis procedure finished"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#
#     def runPlotting(self,
#         all_outlet_detail,
#         proj_path,
#         cali_mode,
#         total_dds_iterations
#        ):
#         """
#         Side process for generating user specified plots
#         :param all_outlet_detail:
#         :param proj_path:
#         :param cali_mode:
#         :param total_dds_iterations:
#         :return:
#         """
#         pip_info_send = """Process: Start creating plots"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         for outlet_key, outlet_detail in all_outlet_detail.items():
#             if not outlet_detail["outletid"] == "not_grouped_subareas":
#
#                 # Check whether the run index is out of the range of total iteration number
#                 if int(outlet_detail["plot_runno"]) > int(total_dds_iterations):
#                     showinfo("Warning",
#                              """The run no you entered for outlet {} is larger than the total iterantions \
#                             Please enter a number smaller than the number.""".format(outlet_detail["outletid"]))
#                     return
#                 else:
#
#                     generatingPlots(proj_path,
#                                    outlet_detail,
#                                    cali_mode,
#                                    outlet_detail["plot_runno"],
#                                    GlobalVars.pair_varid_obs_header,
#                                    self.pipe_process_to_gui)
#
#         pip_info_send = """Process: Finished creating plots"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#
#     def runUncertaintyPlot(self,
#         all_outlet_detail,
#         proj_path,
#         cali_options,
#         total_sim_no
#        ):
#         """
#         Side process for generating uncertainty plots
#         :param all_outlet_detail:
#         :param proj_path:
#         :param cali_mode:
#         :param total_dds_iterations:
#         :return:
#         """
#         # Get the run numbers that have objective functions larger than 0.5
#         fdname_out_calibration = "outfiles_calibration"
#         fdname_observed = "observeddata"
#         path_out_calibration = os.path.join(proj_path, fdname_out_calibration)
#         path_ts_eachrun = os.path.join(path_out_calibration, "timeseries")
#
#         all_outlet_detail = read_observed_data(
#             cali_options,
#             proj_path,
#             GlobalVars.pair_varid_obs_header,
#             GlobalVars.obs_data_header)
#
#         pip_info_send = """Process: Getting Simulated values for each outlet"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#         ts_obs_sim_all_runs = {}
#
#         for olt_key, outlet_detail in all_outlet_detail.items():
#             var_name_full = GlobalVars.pair_varid_obs_header[outlet_detail["variableid"]]
#             var_name = var_name_full.split("(")[0]
#             # Get objective function values
#             # sub_objfun_outfn = os.path.join(path_out_calibration,
#             #                                     "DMPOT_ObjFun_{}{}_{}.out".format(
#             #                                         outlet_detail["outletid"],
#             #                                         var_name,
#             #                                         "dist"))
#
#             # Get time series values
#             for run_index in range(1, int(total_sim_no)+1):
#                 fnp_sim_this_run = os.path.join(path_ts_eachrun,
#                                             "obssimpair_{}_{}_{}.csv".format(
#                                                 outlet_detail["outletid"],
#                                                 var_name,
#                                                 run_index
#                                             ))
#                 # Read in the parameter from the calibrated file
#                 timeseries_sub_whole = pandas.read_csv(
#                     fnp_sim_this_run, sep=",")
#
#                 # Get the observed and date in the frist run
#                 if run_index == 1:
#                     # Create an array to store simulated runs for all runs
#                     ts_obs_sim_all_runs[olt_key] = dict()
#                     ts_obs_sim_all_runs[olt_key]["Date"] = timeseries_sub_whole["Date"]
#                     ts_obs_sim_all_runs[olt_key]["Obs"] = timeseries_sub_whole["{}_x".format(var_name_full)]
#                     ts_obs_sim_all_runs[olt_key]["Sim"] = timeseries_sub_whole["{}_y".format(var_name_full)]
#                 # Stack the following arrays to the Simed_array
#                 elif run_index > 1:
#                     ts_obs_sim_all_runs[olt_key]["Sim"] = numpy.vstack(
#                         (ts_obs_sim_all_runs[olt_key]["Sim"]
#                          ,timeseries_sub_whole["{}_y".format(var_name_full)])
#                     )
#
#             # Making plots
#             pip_info_send = """Process: Creating uncertainty plots with 95 percentile"""
#             self.pipe_process_to_gui.send("{}".format(pip_info_send))
#
#             generatingUncertaintyPlots(
#                 outlet_detail["outletid"],
#                 var_name,
#                 proj_path,
#                 ts_obs_sim_all_runs[olt_key],
#                 cali_options["best_run_no"]
#             )
#         # Making plots
#         pip_info_send = """Confirmation: Finished creating uncertainty plots with 95 percentile"""
#         self.pipe_process_to_gui.send("{}".format(pip_info_send))
