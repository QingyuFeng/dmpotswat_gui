# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16, 2022

This class is designed to be a collection of functions dealing with
plotting figures.

@author: Qingyu.Feng
"""
import os
import pandas
import numpy
import matplotlib.pyplot as plt
plt.switch_backend("agg")
# setting font sizeto 30
plt.rcParams.update({'font.size': 20})

##########################################################################
def generatingUncertaintyPlots(
        outlet_id,
        variable_name,
        proj_path,
        ts_obs_sim_all_runs,
        best_run_no):
    """
    This function generate the 95 percentile plots to show uncertainty and
    save them as individual PNG files.
    """
    fnp_out_fig = os.path.join(
        proj_path,
        "outfiles_dds",
        "uncertaintyplots{}{}.png".format(outlet_id, variable_name))

    fig, axes = plt.subplots(1, 1,
                        figsize=(10, 6),
                        dpi=300,
                        constrained_layout=True)

    # Plot the observed time series
    xlimit = len(ts_obs_sim_all_runs["Obs"])
    line_step = xlimit/10
    axes.plot(numpy.linspace(0, line_step, xlimit),
              ts_obs_sim_all_runs["Obs"],
              label="Observed", color='red')

    # Plot the best run selected by users
    axes.plot(numpy.linspace(0, line_step, xlimit),
              ts_obs_sim_all_runs["Sim"][int(best_run_no) - 1, :],
              label="Best simulated", color='blue')

    # in percent
    prediction_interval = 95.0

    # Determining the upper and lower bounds of the simulated values

    lower_percentile = numpy.percentile(
        ts_obs_sim_all_runs["Sim"],
        50 - prediction_interval / 2., axis=0)
    upper_percentile = numpy.percentile(
        ts_obs_sim_all_runs["Sim"],
        50 + prediction_interval / 2., axis=0)

    axes.fill_between(numpy.linspace(0, line_step, xlimit),
                     lower_percentile,
                     upper_percentile,
                     alpha=0.5, color='black',
                     label=f"{prediction_interval} % prediction interval")

    # axes.set_xlabel("")
    axes.set_ylabel("{}".format(variable_name))
    axes.legend(title="95Percentile{}{}".format(outlet_id, variable_name),
               loc='upper right')._legend_box.align = "left"

    fig.savefig(fnp_out_fig, bbox_inches="tight")


##########################################################################
def generatingPlots(proj_path,
                   outlet_detail,
                   cali_mode,
                   run_index,
                   pair_varid_obs_header,
                   plot_purpose,
                   fnd_ts_outfiles,
                   pipe_process_to_gui):
    """
    This function generate line charts for observed vs simulated flow and
    save them as individual PNG files."outfiles_calibration""outfiles_plots"
    """

    outlet_id = int(outlet_detail["outletid"])
    variable_id = outlet_detail["variableid"]
    variable_header = pair_varid_obs_header[variable_id]

    cali_mode_text = ""

    if cali_mode == "dist":
        cali_mode_text = "Distributed"
    elif cali_mode == "lump":
        cali_mode_text = "Lumped"

    # Read the output csv files for specified run no
    fd_ts_eachrun = os.path.join(proj_path, fnd_ts_outfiles, "timeseries")
    fnp_sim_this_run = os.path.join(fd_ts_eachrun,
                                    "obssimpair_{}_{}_{}.csv".format(
                                        outlet_detail["outletid"],
                                        variable_header.split("(")[0],
                                        run_index
                                    ))

    # Columns: yyyy,mm,dd,Date,sf(m3/s)_x,RCH,GIS,MON,AREAkm2,sf(m3/s)_y
    obs_sim_pair_dataframe = pandas.read_csv(fnp_sim_this_run)

    fd_output_plots = os.path.join(proj_path, fnd_ts_outfiles)
    fnp_time_series = os.path.join(
        fd_output_plots,
        "timeseries_{}_{}_{}_{}.png".format(
            outlet_detail["outletid"],
            variable_header.split("(")[0],
            run_index,
            plot_purpose))

    fnp_duration_curve = os.path.join(
        fd_output_plots,
        "duration_curve_{}_{}_{}_{}.png".format(
            outlet_detail["outletid"],
            variable_header.split("(")[0],
            run_index,
            plot_purpose))

    if os.path.isfile(fnp_time_series):
        os.remove(fnp_time_series)

    if outlet_detail["plot_time_series"] == "true":
        pip_info_send = """Process: Creating time series plots for {} {}""".format(
            outlet_id, variable_header
        )
        pipe_process_to_gui.send("{}".format(pip_info_send))

        genePlotTimeSeries(
            fnp_time_series,
            obs_sim_pair_dataframe,
            cali_mode_text,
            run_index,
            outlet_detail["outletid"],
            variable_header,
            plot_purpose)

        pip_info_send = """Process: {}""".format(
            fnp_time_series
        )
        pipe_process_to_gui.send("{}".format(pip_info_send))

    if outlet_detail["plot_duration_curve"] == "true":
        pip_info_send = """Process: Creating duration curve plots for {} {}""".format(
            outlet_id, variable_header
        )
        pipe_process_to_gui.send("{}".format(pip_info_send))

        genePlotDurationCurve(fnp_duration_curve,
            obs_sim_pair_dataframe,
            cali_mode_text,
            run_index,
            outlet_detail["outletid"],
            variable_header,
            plot_purpose)
        pip_info_send = """Process: {}""".format(
            fnp_duration_curve
        )
        pipe_process_to_gui.send("{}".format(pip_info_send))


##########################################################################
def genePlotDurationCurve(fnp_duration_curve,
        obs_sim_pair_dataframe,
        cali_mode_text,
        run_index,
        outletid,
        variable_header,
        plot_purpose):
    """
    This function generate figure for one outlet.
    """
    fig = None

    obs_ts = obs_sim_pair_dataframe["{}_x".format(variable_header)].tolist()
    sim_ts = obs_sim_pair_dataframe["{}_y".format(variable_header)].tolist()

    # The number of subplots need to be specified by users
    # for customization
    noColFig = 1
    noRowFig = 1
    figWidth = 10
    figHeight = 6

    # In order to include missing values in observed data, they will be converted to
    # np.nan
    for obsIdx in range(len(obs_ts)):
        if obs_ts[obsIdx] == -99:
            obs_ts[obsIdx] = numpy.nan
            sim_ts[obsIdx] = numpy.nan

    fig, axes = plt.subplots(noRowFig, noColFig,
                        figsize=(figWidth, figHeight),
                        dpi=300,
                        tight_layout=True)

    """
    Calculates and plots a flow duration curve from timeSeries. 

    All observations/simulations are ordered and the empirical probability is
    calculated. This is then plotted as a flow duration curve. 

    Additionally a comparison can be given to the function, which is plotted in
    the same ax.

    :param timeSeries: list of simulated and/or observed flow
    :param comparison: numpy array or pandas dataframe of discharge that should
    also be plotted in the same ax
    :param axis: int, axis along which x is iterated through
    :param ax: matplotlib subplot object, if not None, will plot in that 
    instance
    :param plot: bool, if False function will not show the plot, but simply
    return the ax object
    :param log: bool, if True plot on loglog axis
    :param percentiles: tuple of int, percentiles that should be used for 
    drawing a range flow duration curve
    :param fdc_kwargs: dict, matplotlib keywords for the normal fdc
    :param fdc_range_kwargs: dict, matplotlib keywords for the range fdc
    :param fdc_comparison_kwargs: dict, matplotlib keywords for the comparison 
    fdc

    return: subplot object with the flow duration curve in it
    """

    axes = plot_single_flow_duration_curve(axes, sim_ts, outletid)

    # Add a comparison to the plot if is present
    axes = plot_single_flow_duration_curve(axes, obs_ts, outletid, iObs=True)

    # Figure refine
    # Control legend
    axes.legend(title="{} {} {}".format(cali_mode_text, outletid, plot_purpose),
                framealpha=1,
                loc='upper right'
                )._legend_box.align = "left"

    # box = ax1.get_position()
    # # setposition(left, bottom, width, height)
    # ax1.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    # Control label
    # set: a property batch setter
    # set_xlabel(xlabel, labelpad, **kwargs)
    axes.set_xlabel("Exceedance Probability")
    # Only create y label for the first column of figures
    axes.set_ylabel("{}".format(variable_header))

    # Control grids
    axes.grid(which='major')

    # Control ticks
    axes.set_xlim(left=-5, right=105)

    axes.tick_params(
        which='major',
        direction="in")

    fig.savefig(fnp_duration_curve, bbox_inches="tight")


def plot_single_flow_duration_curve(ax, timeseries, oltNo, iObs=False):
    """
    Plots a single fdc into an ax.

    :param ax: matplotlib subplot object
    :param timeseries: list like iterable

    return: subplot object with a flow duration curve drawn into it
    """
    # Get the probability
    exceedence = numpy.arange(1., len(timeseries) + 1) / len(timeseries)
    exceedence *= 100
    if not iObs:
        ax.scatter(exceedence,
                   sorted(timeseries, reverse=True),
                   label="Simulated",
                   marker=".",
                   c="blue"
                   )
    else:
        ax.scatter(exceedence,
                   sorted(timeseries, reverse=True),
                   label="Observed",
                   marker=".",
                   c="red"
                   )
    # Figure refine


def plot_single_flow_duration_curve(ax, timeseries, oltNo, iObs=False):
    """
    Plots a single fdc into an ax.

    :param ax: matplotlib subplot object
    :param timeseries: list like iterable

    return: subplot object with a flow duration curve drawn into it
    """

    # Get the probability
    exceedence = numpy.arange(1., len(timeseries) + 1) / len(timeseries)
    exceedence *= 100
    if not iObs:
        ax.scatter(exceedence,
                   sorted(timeseries, reverse=True),
                   label="Simulated",
                   marker=".",
                   c="blue"
                   )
    else:
        ax.scatter(exceedence,
                   sorted(timeseries, reverse=True),
                   label="Observed",
                   marker=".",
                   c="red"
                   )

    return ax


##########################################################################
def genePlotTimeSeries(fnp_time_series,
        obs_sim_pair_dataframe,
        cali_mode_text,
        run_index,
        outletid,
        variable_header,
        plot_purpose):
    """
    This function generate figure for one outlet.
    """
    fig = None

    obs_ts = obs_sim_pair_dataframe["{}_x".format(variable_header)].tolist()
    sim_ts = obs_sim_pair_dataframe["{}_y".format(variable_header)].tolist()

    # In order to include missing values in observed data, they will be converted to
    # np.nan
    for obsIdx in range(len(obs_ts)):
        if obs_ts[obsIdx] == -99:
            obs_ts[obsIdx] = numpy.nan
            sim_ts[obsIdx] = numpy.nan

    fig, axes = plt.subplots(1, 1,
                             figsize=(10, 6),
                             dpi=300,
                             tight_layout=True)

    axes.plot(obs_ts, label="Observed", color='red')
    axes.plot(sim_ts, label="Simulated", color='blue')

    axes.legend(title="Outlet {} {} Run {} {}".format(
        outletid, variable_header, plot_purpose, cali_mode_text),
                loc="upper right")
    # axes.set_title("Outlet {} {} Run No {} {} {}".format(
    #     outletid, variable_header, run_index, plot_purpose, cali_mode_text))

    axes.set_xlabel("Time")
    axes.set_ylabel("{}".format(variable_header))

    # Control grids
    axes.grid(which='major')

    # Control ticks
    axes.tick_params(which='major', direction="in")

    fig.savefig(fnp_time_series, bbox_inches="tight")

    # Close plot
    plt.close()