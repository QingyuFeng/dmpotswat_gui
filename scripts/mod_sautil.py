# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16, 2022

This class is designed to be a collection of functions dealing with
the Sensitivity analysis procedure.

@author: Qingyu.Feng
"""

import os
import numpy as np
import pandas
import copy
from SALib.analyze import sobol, fast
from SALib.sample import saltelli, fast_sampler
import SALib.sample.morris as morris_sample
import SALib.analyze.morris as morris_analyze


##########################################################################
def geneParmSamplesForSA(parm_basin_level,
                         parm_sub_level,
                         sa_method_parm,
                         proj_path):
    """
    This function takes the basin and subarea level parameter selected
    by users and generate the problem varaible required for SALib.
    Input:
    parmBsnLvl, parmSubLvl (Format: Dataframe)
    sa_method: sobol, morris, fast
    Output：
    Dictionary
    problem = {
    'num_vars': 3,
    'names': ['x1', 'x2', 'x3'],
    'bounds': [[-3.14159265359, 3.14159265359],
               [-3.14159265359, 3.14159265359],
               [-3.14159265359, 3.14159265359]]
    }

    """

    parm_symbol_list = parm_sub_level["Symbol"].tolist() + parm_basin_level["Symbol"].tolist()
    parm_bounds_array = parm_sub_level[["LowerBound", "UpperBound"]].values.tolist() + parm_basin_level[[
        "LowerBound", "UpperBound"]].values.tolist()

    problem = {}
    problem['num_vars'] = len(parm_symbol_list)
    problem['names'] = parm_symbol_list
    problem['bounds'] = parm_bounds_array

    if sa_method_parm["method"] == "sobol":
        parm_samples = saltelli.sample(problem,
                                       int(sa_method_parm["sobol_n"]),
                                       skip_values=int(sa_method_parm["sobol_n"]))

    elif sa_method_parm["method"] == "morris":  # For Morris method
        parm_samples = morris_sample.sample(problem,
                                            int(sa_method_parm["morris_n"]),
                                            num_levels=4)

    elif sa_method_parm["method"] == "fast":  # For FAST method
        # SALib.sample.fast_sampler.sample(problem, N, M=4, seed=None)[source]
        parm_samples = fast_sampler.sample(problem,
                                           int(sa_method_parm["fast_n"]))

    fd_sa_outputs = os.path.join(proj_path, "outfiles_sa")
    fnp_parm_samples = os.path.join(fd_sa_outputs, "parmSample_{}.txt".format(sa_method_parm["method"]))
    if os.path.isfile(fnp_parm_samples):
        os.remove(fnp_parm_samples)
    np.savetxt(fnp_parm_samples, parm_samples, fmt='%.8f', delimiter=' ')

    # Convert the samples into pandas dataframe
    sa_parm_dataframe = pandas.DataFrame(
        parm_samples,
        columns=parm_symbol_list,
        index=range(1, parm_samples.shape[0] + 1))

    return fnp_parm_samples, sa_parm_dataframe, parm_samples, problem


##########################################################################
def updateParmInDf(parm_dataframe, parm_sample_dataframe):
    """
    This function updates the parameter values to the sample values.
    """
    for df_index in parm_dataframe.index:
        col_name = parm_dataframe.loc[df_index, "Symbol"]
        parm_dataframe.loc[df_index, "TestVal"] = parm_sample_dataframe[col_name]

    return parm_dataframe


##########################################################################
def initialOutFileSA(all_outlet_detail,
            proj_path,
            fnd_outfiles_sa):
    """
    This funciton initialize the output files storing the
    Y output
    :param all_outlet_detail:
    :param proj_path:
    :return:
    """
    sa_fnout_avgvar = {}

    fd_sa_outputs = os.path.join(proj_path, fnd_outfiles_sa)

    for outlet_key, outlet_detail in all_outlet_detail.items():
        if not outlet_detail["outletid"] == "not_grouped_subareas":
            outlet_id = int(outlet_detail["outletid"])
            variable_id = outlet_detail["variableid"]

            fnp_sa = os.path.join(fd_sa_outputs, "oltVal_{}_{}.txt".format(outlet_id, variable_id))
            sa_fnout_avgvar[outlet_key] = fnp_sa
            # if os.path.isfile(fnp_sa):
            #     os.remove(fnp_sa)

    return sa_fnout_avgvar


##########################################################################
def generateAllOutletDetails(
        outlet_details,
        total_sample_rows
        ):

    all_outlet_detail = copy.deepcopy(outlet_details)
    for outlet_key, outlet_detail in all_outlet_detail.items():
        if not outlet_detail["outletid"] == "not_grouped_subareas":
            outlet_detail["list_sim_avg"] = np.zeros(total_sample_rows)

    return all_outlet_detail


##########################################################################
def extractSimValuesEachGroup(
        sa_fnout_avgvar,
        all_outlet_detail,
        cali_options,
        dataframe_outrch_whole,
        pair_varid_obs_header,
        sa_runindex):
    """
    Get the corresponding simulated values for each variable.
    :param sa_fnout_avgvar:
    :param all_outlet_detail:
    :param cali_options:
    :param dataframe_outrch_whole:
    :param pair_varid_obs_header:
    :return:
    """
    sim_start_date = cali_options["simstartdate"]
    sim_end_date = cali_options["simenddate"]
    warmup_year = cali_options["warmupyrs"]

    # Check the length of the observed data to make sure it covered the
    # simulation length specified by user.
    sim_start_date_lst = sim_start_date.split("/")
    sim_end_date_lst = sim_end_date.split("/")

    date_header = ["yyyy", "mm", "dd", "Date"]

    sim_real_start_date = pandas.Timestamp(
            year=int(sim_start_date_lst[2]) + int(warmup_year),
            month=int(sim_start_date_lst[0]),
            day=int(sim_start_date_lst[1]))

    sim_end_date = pandas.Timestamp(
            year=int(sim_end_date_lst[2]),
            month=int(sim_end_date_lst[0]),
            day=int(sim_end_date_lst[1]))

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
                sim_mon_range = pandas.date_range(sim_real_start_date,
                                                  sim_end_date,
                                                  freq='M')
                outlet_rch_rows["Date"] = sim_mon_range
            elif cali_options["iprint"] == "daily":
                sim_daily_range = pandas.date_range(sim_real_start_date,
                                                    sim_end_date,
                                                    freq='D')
                outlet_rch_rows["Date"] = sim_daily_range
            elif cali_options["iprint"] == "annual":
                sim_year_range = pandas.date_range(sim_real_start_date,
                                                   sim_end_date,
                                                   freq='Y')
                outlet_rch_rows["Date"] = sim_year_range
            # Combine the two pair based on dates
            outlet_detail["list_sim_avg"][sa_runindex] = outlet_rch_rows[variable_header].mean()

            # Write the mean and values for corresponding time step into a file
            with open(sa_fnout_avgvar[outlet_key], "a") as sa_outfile:
                sa_outfile.writelines("""{}\n""".format(outlet_rch_rows[variable_header].mean()))

    return all_outlet_detail



##########################################################################
def writeObjFunValtoFile(
        runIdx,
        all_outlet_detail,
        basin_obj_func_values,
        pair_varid_obs_header,
        sub_objfun_outfn,
        bsn_obj_fn,
        pipe_process_to_gui):
    """
    This function writet the statistics and objective function values into
    output files for calculation of sa index.
    """
    # For each outlet_variable combination, the difference between the lump and
    # dist mode is the way how parameter is updated and which objective function is used.
    # Besides, the way how not_grouped_subareas is processed in different ways.
    for ovid, outlet_detail in all_outlet_detail.items():
        variable_id = outlet_detail["variableid"]
        variable_header = pair_varid_obs_header[variable_id]

        if outlet_detail["outletid"] != "not_grouped_subareas":
            # Display the objective function values
            pip_info_send = """Objective function value for outlet {} var {} is: {:.5f}""".format(
                outlet_detail["outletid"],
                variable_header,
                float(outlet_detail["test_obj_dist"]))
            pipe_process_to_gui.send("{}".format(pip_info_send))

            # Write the objective function values into files
            # These will be written under both dist and lump mode
            # Need to write these variables into a file
            # lfwAllStat = "RunNo,OutLet,Variable,NSE,R2,MSE,PBIAS,RMSE,TestOF\n"
            # print("type: nse_value, ", type(outlet_detail["nse_value"]), outlet_detail["nse_value"])
            # print("type: r2_value, ", type(outlet_detail["r2_value"]), outlet_detail["r2_value"])
            # print("type: mse_value, ", type(outlet_detail["mse_value"]), outlet_detail["mse_value"])
            # print("type: pbias_value, ", type(outlet_detail["pbias_value"]), outlet_detail["pbias_value"])
            # print("type: rmse_value, ", type(outlet_detail["rmse_value"]), outlet_detail["rmse_value"])
            # print("type: test_obj_dist, ", type(outlet_detail["test_obj_dist"]), outlet_detail["test_obj_dist"])
            # print("type: best_obj_dist, ", type(outlet_detail["best_obj_dist"]), outlet_detail["best_obj_dist"])

            lfw_stat_objfun = """{},{},{},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f}\n""".format(
                runIdx, outlet_detail["outletid"], variable_header,
                outlet_detail["nse_value"],
                outlet_detail["r2_value"],
                outlet_detail["mse_value"],
                outlet_detail["pbias_value"],
                outlet_detail["rmse_value"],
                outlet_detail["test_obj_dist"])

            with open(sub_objfun_outfn[ovid], 'a') as obfFile:
                obfFile.writelines(lfw_stat_objfun)

        elif outlet_detail["outletid"] == "not_grouped_subareas":
            # Display the objective function values
            pip_info_send = """Sum of objective functions is: {:.5f}""".format(
                basin_obj_func_values["obj_basin_test"])
            pipe_process_to_gui.send("{}".format(pip_info_send))

    # Write the objective function values into files
    # Need to write these variables into a file
    # lfwAllStat = "RunNo,OutLet,TestOF\n"
    lfw_stat_objfun = """{},sumobjf,{:.5f}\n""".format(
        runIdx, float(basin_obj_func_values["obj_basin_test"]))

    with open(bsn_obj_fn, 'a') as obfFile:
        obfFile.writelines(lfw_stat_objfun)


##########################################################################
def writeSAObjFunFileStatHdrs(all_outlet_detail,
                              sub_objfun_outfn,
                              bsn_obj_fn):
    """
    Initialize the output file names, including subarea parameter values, subarea
    objective function, and parameter select during the runs
    """
    sub_obj_val_hdr = "RunNo,OutLet,Variable,NSE,R2,MSE,PBIAS,RMSE,TestOF\n"
    bsn_obj_val_hdr = "RunNo,OutLet,TestOF\n"

    for opKeys, outlet_detail in all_outlet_detail.items():
        if opKeys != "not_grouped_subareas":
            # Get the corresponding parameter set for the variables of this pair
            var_id = outlet_detail["variableid"]
            # var_name = pair_varid_obs_header[var_id].split("(")[0]
            if os.path.isfile(sub_objfun_outfn[opKeys]):
                os.remove(sub_objfun_outfn[opKeys])
            with open(sub_objfun_outfn[opKeys], 'a') as obfFile:
                obfFile.writelines(sub_obj_val_hdr)

    # Initialize the basin level parameter file as a record
    if os.path.isfile(bsn_obj_fn):
        os.remove(bsn_obj_fn)
    with open(bsn_obj_fn, 'a') as bsnParmSFile:
        bsnParmSFile.writelines(bsn_obj_val_hdr)


##########################################################################
def calculateSAIndex(
        sa_parm_sample_array,
        sa_parm_problem,
        all_outlet_detail,
        proj_path,
        sa_method_parm,
        sub_objfun_outfn
):
    """
    Calculate the saindex with corresponding analysis method.
    :param sa_parm_sample_array:
    :param all_outlet_detail:
    :param proj_path:
    :param proj_path:
    :return:
    """
    fd_sa_outputs = os.path.join(proj_path, "outfiles_sa")

    for outlet_key, outlet_detail in all_outlet_detail.items():
        if not outlet_detail["outletid"] == "not_grouped_subareas":
            outlet_id = int(outlet_detail["outletid"])
            variable_id = outlet_detail["variableid"]

            outlet_statistics = pandas.read_table(
                sub_objfun_outfn[outlet_key],
                sep=",",
                header=0,
                index_col=0
            )

            response_list = outlet_statistics["TestOF"].to_numpy()

            if sa_method_parm["method"] == "sobol":
                # SALib.analyze.sobol.analyze(problem, Y, calc_second_order=True,
                # num_resamples=100, conf_level=0.95, print_to_console=False,
                #  parallel=False, n_processors=None, keep_resamples=False,
                # seed=None)
                sa_output = sobol.analyze(sa_parm_problem,
                                          response_list,
                                          calc_second_order=True,
                                          print_to_console=False)
                # Write the output as a dataframe and into a file
                sa_output_dataframe = sa_output.to_df()
                fnpout_sa_total = os.path.join(fd_sa_outputs,
                                               "oltSATotal_{}_{}_{}.csv".format(
                                                   outlet_id,
                                                   variable_id,
                                                   sa_method_parm["method"]))

                sa_output_dataframe[0].to_csv(fnpout_sa_total)

                fnpout_sa_first = os.path.join(fd_sa_outputs,
                                               "oltSAFirst_{}_{}_{}.csv".format(
                                                   outlet_id,
                                                   variable_id,
                                                   sa_method_parm["method"]))
                if os.path.isfile(fnpout_sa_first):
                    os.remove(fnpout_sa_first)
                sa_output_dataframe[1].to_csv(fnpout_sa_first)

            elif sa_method_parm["method"] == "morris":  # For Morris method
                # SALib.analyze.morris.analyze(problem: Dict, X: numpy.ndarray,
                #  Y: numpy.ndarray, num_resamples: int = 100,
                #  conf_level: float = 0.95, print_to_console: bool = False,
                #  num_levels: int = 4, seed=None) → numpy.ndarray
                # Returns a dictionary with keys ‘mu’, ‘mu_star’, ‘sigma’,
                # and ‘mu_star_conf’, where each entry is a list of parameters
                # containing the indices in the same order as the parameter file.
                # sa_parm_sample_array = np.loadtxt(fn_sample_array_txt)
                sa_output_morris = morris_analyze.analyze(
                    sa_parm_problem,
                    sa_parm_sample_array,
                    response_list,
                    conf_level=0.95,
                    print_to_console=False
                )

                # Write the output as a dataframe and into a file
                sa_output_dataframe_morris = sa_output_morris.to_df()
                fnpout_sa_mu = os.path.join(fd_sa_outputs,
                                            "oltSA_{}_{}_{}.csv".format(
                                                outlet_id,
                                                variable_id,
                                                sa_method_parm["method"]))
                if os.path.isfile(fnpout_sa_mu):
                    os.remove(fnpout_sa_mu)
                sa_output_dataframe_morris.to_csv(fnpout_sa_mu)

            elif sa_method_parm["method"] == "fast":  # For FAST method
                # SALib.analyze.fast.analyze(problem,
                # Y, M=4, num_resamples=100,
                #  conf_level=0.95, print_to_console=False, seed=None)
                # Returns a dictionary with keys ‘S1’ and ‘ST’,
                # where each entry is a list of size D (the number of parameters)
                # containing the indices in the same order as the parameter file.
                sa_output_fast = fast.analyze(sa_parm_problem,
                                              response_list,
                                              print_to_console=False)
                # Write the output as a dataframe and into a file
                sa_output_dataframe_fast = sa_output_fast.to_df()
                fnpout_sa_fast = os.path.join(fd_sa_outputs,
                                              "oltSATotal_{}_{}.csv".format(
                                                  outlet_id,
                                                  variable_id,
                                                  sa_method_parm["method"]))
                if os.path.isfile(fnpout_sa_fast):
                    os.remove(fnpout_sa_fast)
                sa_output_dataframe.to_csv(fnpout_sa_fast)

