import pathlib
import os
import sys
import pytz

# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
#     return os.path.join(base_path, relative_path)
#

class global_vars():

    def __init__(self):
        # Progress:
        # 1: created projects
        # 2: checked txt
        # 3: checked reach
        # 4: setup options
        # 5: setup parametersos.path.dirname(__file__), "img"
        self.path_app_root = os.path.dirname(__file__)
        # self.path_app_root = pathlib.Path(__file__).parent.absolute()
        self.time_zone = pytz.timezone('Asia/Shanghai')

        # OutVariable header and numbers in the observed files
        # In the Control File:
        # Output Variables (0-15): '0- Baseflow', '1-Stream Flow',
        # '2-Sediment','3-org-N','4-org-P','5-NO_3-N','6-NH_4-N',
        # '7-NO_2-N','8-Mineral-P','9-Soluble Pesticide',
        # '10-Sorbed Pesticide','11-Total Phosphorus',
        # '12-Total Nitrogen','13-Total Pesticide','14-TKN',
        #  '15-NO2+NO3'
        # Headers in the Observed data:
        # sf(m3/s)	sed(t/ha)
        # orgn(kg/ha)	orgp(kg/ha)	no3n(kg/ha)
        # 	nh4n(kg/ha)	no2n(kg/ha)	minp(kg/ha)
        # 	solpst(mg/ha)	sorpst(mg/ha)	tp(kg/ha)
        # 	tn(kg/ha)	tpst(ppb)
        self.pair_varid_obs_header = {
            "1": "sf(m3/s)",
            "2": "sed(t/ha)",
            "3": "orgn(kg/ha)",
            "4": "orgp(kg/ha)",
            "5": "no3n(kg/ha)",
            "6": "nh4n(kg/ha)",
            "7": "no2n(kg/ha)",
            "8": "minp(kg/ha)",
            "9": "solpst(mg/ha)",
            "10": "sorpst(mg/ha)",
            "11": "tp(kg/ha)",
            "12": "tn(kg/ha)",
            "13": "tpst(ppb)"
        }

        self.obs_data_header = ["yyyy", "mm", "dd", "sf(m3/s)", "sed(t/ha)", "orgn(kg/ha)",
                                "orgp(kg/ha)", "no3n(kg/ha)", "nh4n(kg/ha)",
                                "no2n(kg/ha)", "minp(kg/ha)", "solpst(mg/ha)",
                                "sorpst(mg/ha)", "tp(kg/ha)", "tn(kg/ha)", "tpst(ppb)"]

        self.basin_file_exts = [".bsn", "crop.dat", ".wwq"]
        self.sub_level_file_exts = [".sub", ".rte", ".swq", ".res"]
        self.hru_level_file_exts = [".gw", ".hru", ".mgt", ".sol", ".chm"]

        self.platforms = {
            'linux': 'Linux',
            'darwin': 'OS X',
            'win32': 'Windows'
        }

        self.os_platform = self.platforms[sys.platform]

        if self.os_platform == "Linux":
            self.fname_swat_executable = "swat2012.681.gfort.rel"

        elif self.os_platform == "Windows":
            self.fname_swat_executable = "swat201268564rel.exe"

        self.path_src_swat_exe = os.path.join(
            self.path_app_root,
            self.fname_swat_executable
        )

        self.fname_main_icon = "DmpotswaticoCreation.ico"
        self.path_main_icon = os.path.join(
            self.path_app_root,
            self.fname_main_icon
        )
        self.fname_logo = "DmpotswaticoCreation.png"
        self.path_main_logo = os.path.join(
            self.path_app_root,
            self.fname_logo
        )

        # Output variables determined in the file.cio file
        # 1bfr,2sf,3sed,4orgn,5orgp,6no3n,7nh4n,8no2n,9minp,
        # 10solpst,11sorpst,12tp,13tn,14tpst
        # rchVarSelLst = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
        self.reach_var_list = [2, 6, 9, 11, 13, 15, 17, 19, 27, 29]

        # Row crop and pasture list
        self.row_crop_list = ["CORN", "SOYB", "WWHT", "AGRL", "AGRR", "AGRC",
                              "CCRN", "CSOY", "CWHT", "CYCN", "SYCN", "SYWH", "WHCN"]

        self.pasture_hay_list = ["PAST", "HAY", "ALFA"]
        self.forest_list = ["FRST", "FRSD", "FRSE"]
        self.urban_list = ["URHD", "URMD", "URML", "URLD", "UCOM", "UIDU", "UTRN", "UINS"]




default_dmpotconf = {

    "gui_status":
        {
            "projectname": "default",
            "proj_path": "default",
            "proj_file": "default",
            "newproject": "false",
            "loadporject": "false",
            "saveporject": "false",
            "checktxtinout": "false",
            "checkreach": "false",
            "set_swat_model": "false",
            "definebtnclick": "false",
            "setParm": "false",
            "setSA": "false",
            "setCali": "false",
            "finished_cali_run": "false",
            "copy_observed_data": "false",
            "define_plot_target": "false"
        },

    "cali_options":
        {
            "copy_txtinout": "false",
            "warmupyrs": "dft",
            "simstartdate": "dft",
            "simenddate": "dft",
            "iprint": "dft",
            "cali_mode": "dist",
            "total_outlet_vars": "dft",
            "all_outlets_reach": [],
            "outlet_details": "dummy",
            "default_best_run": "default",
            "best_run_no": "0",
            "no_multi_cores": "1",
            "bestrun_purpose": "calibration"
        },

    "basin_obj_func_values":
        {
            "obj_basin_test": 10000.0,
            "obj_basin_best": 10000.0
        },

    "outlet_details_template":
        {
            "outlet_var": {
                "orderno": "0",
                "outletid": "0",
                "variableid": "0",
                "varweight": "0",
                "r2_select": "0",
                "r2_weight": "0",
                "nse_select": "0",
                "nse_weight": "0",
                "pbias_select": "0",
                "pbias_weight": "0",
                "mse_select": "0",
                "mse_weight": "0",
                "rmse_select": "0",
                "rmse_weight": "0",
                "r2_value": "999.9",
                "nse_value": "999.9",
                "pbias_value": "999.9",
                "mse_value": "999.9",
                "rmse_value": "999.9",
                "rsr_value": "999.9",
                "test_obj_dist": "10000.0",
                "best_obj_dist": "10000.0",
                "df_obs": "",
                "df_obs_sim": "",
                "list_sim_avg": [],
                "parm_sub": "",
                "subarea_list": [],
                "plot_time_series": "false",
                "plot_duration_curve": "false",
                "plot_runno": "0"
            }
        },

    "sa_method_parm":
        {
            "method": "sobol",
            "sobol_n": "8",
            "morris_n": "20",
            "fast_n": "70",
            "sa_mode": "dist"
        },

    "cali_dds":
        {

            "pertubfactor": "0.2",
            "totalsimno": "100",
            "initparaidx": "random",
            "restartmech": "restart",
            "inpuncertidx": "unchecked",
            "measuncertidx": "unchecked",
            "measerr": "15"
        },

    "soft_data":
        {
            "Denitification":
                {
                    "select": "unchecked",
                    "upper": "60",
                    "lower": "0"
                },

            "NO3 Leach":
                {
                    "select": "unchecked",
                    "upper": "3",
                    "lower": "0"
                },

            "P leached":
                {
                    "select": "unchecked",
                    "upper": "1",
                    "lower": "0"
                },

            "SSQ/(SQ+SSQ) NO3 Yield":
                {
                    "select": "unchecked",
                    "upper": "0.99",
                    "lower": "0.6"
                }
        },

    "parms": {
        "1": {
            "ObjectID": "1",
            "Symbol": "DEPIMP_BSN",
            "File": ".bsn",
            "Unit": "mm",
            "InitVal": "3000",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "6000",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "2": {
            "ObjectID": "2",
            "Symbol": "EPCO",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "0.3901",
            "selectFlag": "1",
            "LowerBound": "0.001",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "3": {
            "ObjectID": "3",
            "Symbol": "SFTMP",
            "File": ".bsn",
            "Unit": "oC",
            "InitVal": "2.688",
            "selectFlag": "1",
            "LowerBound": "-5",
            "UpperBound": "5",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "4": {
            "ObjectID": "4",
            "Symbol": "SMFMN",
            "File": ".bsn",
            "Unit": "mm/oC-day",
            "InitVal": "2.437",
            "selectFlag": "1",
            "LowerBound": "1.4",
            "UpperBound": "6.9",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "5": {
            "ObjectID": "5",
            "Symbol": "SMFMX",
            "File": ".bsn",
            "Unit": "mm/oC-day",
            "InitVal": "2.215",
            "selectFlag": "1",
            "LowerBound": "1.4",
            "UpperBound": "6.9",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "6": {
            "ObjectID": "6",
            "Symbol": "SMTMP",
            "File": ".bsn",
            "Unit": "oC",
            "InitVal": "-0.5697",
            "selectFlag": "1",
            "LowerBound": "-5",
            "UpperBound": "5",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "7": {
            "ObjectID": "7",
            "Symbol": "SNOCOVMX",
            "File": ".bsn",
            "Unit": "mm",
            "InitVal": "46.17",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "650",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "8": {
            "ObjectID": "8",
            "Symbol": "SNO50COV",
            "File": ".bsn",
            "Unit": "mm",
            "InitVal": "0.9826",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "9": {
            "ObjectID": "9",
            "Symbol": "SURLAG",
            "File": ".bsn",
            "Unit": "day",
            "InitVal": "5.021",
            "selectFlag": "1",
            "LowerBound": "0.05",
            "UpperBound": "24",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "10": {
            "ObjectID": "10",
            "Symbol": "TIMP",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "0.9019",
            "selectFlag": "1",
            "LowerBound": "0.01",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "11": {
            "ObjectID": "11",
            "Symbol": "ALPHA_BF",
            "File": ".gw",
            "Unit": "days",
            "InitVal": "0.9941",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "12": {
            "ObjectID": "12",
            "Symbol": "GW_DELAY",
            "File": ".gw",
            "Unit": "day",
            "InitVal": "12.3",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "60",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "13": {
            "ObjectID": "13",
            "Symbol": "GW_REVAP",
            "File": ".gw",
            "Unit": "-",
            "InitVal": "0.09242",
            "selectFlag": "1",
            "LowerBound": "0.0",
            "UpperBound": "0.2",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "14": {
            "ObjectID": "14",
            "Symbol": "GW_SPYLD",
            "File": ".gw",
            "Unit": "%",
            "InitVal": "-0.1199",
            "selectFlag": "1",
            "LowerBound": "-0.2",
            "UpperBound": "0.2",
            "ChangeType": "FRAC",
            "ForVariable": "Flow"
        },
        "15": {
            "ObjectID": "15",
            "Symbol": "GWHT",
            "File": ".gw",
            "Unit": "m",
            "InitVal": "13.87",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "25",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "16": {
            "ObjectID": "16",
            "Symbol": "GWQMN",
            "File": ".gw",
            "Unit": "mm",
            "InitVal": "913.9",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "5000",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "17": {
            "ObjectID": "17",
            "Symbol": "RCHRG_DP",
            "File": ".gw",
            "Unit": "-",
            "InitVal": "0.2447",
            "selectFlag": "1",
            "LowerBound": "0.01",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "18": {
            "ObjectID": "18",
            "Symbol": "REVEP_MN",
            "File": ".gw",
            "Unit": "mm",
            "InitVal": "197.1",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "500",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "19": {
            "ObjectID": "19",
            "Symbol": "ESCO",
            "File": ".hru",
            "Unit": "-",
            "InitVal": "0.6049",
            "selectFlag": "1",
            "LowerBound": "0.6",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "20": {
            "ObjectID": "20",
            "Symbol": "CANMX",
            "File": ".hru",
            "Unit": "mm",
            "InitVal": "1.06",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "10",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "21": {
            "ObjectID": "21",
            "Symbol": "OV_N",
            "File": ".hru",
            "Unit": "-",
            "InitVal": "0.107",
            "selectFlag": "1",
            "LowerBound": "0.01",
            "UpperBound": "0.6",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "22": {
            "ObjectID": "22",
            "Symbol": "SLOPE",
            "File": ".hru",
            "Unit": "%",
            "InitVal": "0.1955",
            "selectFlag": "1",
            "LowerBound": "-0.2",
            "UpperBound": "0.2",
            "ChangeType": "FRAC",
            "ForVariable": "Flow"
        },
        "23": {
            "ObjectID": "23",
            "Symbol": "CN_F",
            "File": ".mgt",
            "Unit": "%",
            "InitVal": "0.05946",
            "selectFlag": "1",
            "LowerBound": "-0.20",
            "UpperBound": "0.20",
            "ChangeType": "FRAC",
            "ForVariable": "Flow"
        },
        "24": {
            "ObjectID": "24",
            "Symbol": "CH_KII",
            "File": ".rte",
            "Unit": "mm/hr",
            "InitVal": "66.79",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "250",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "25": {
            "ObjectID": "25",
            "Symbol": "CH_NII",
            "File": ".rte",
            "Unit": "-",
            "InitVal": "0.02577",
            "selectFlag": "1",
            "LowerBound": "0.01",
            "UpperBound": "0.2",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "26": {
            "ObjectID": "26",
            "Symbol": "CH_SII",
            "File": ".rte",
            "Unit": "%",
            "InitVal": "0",
            "selectFlag": "1",
            "LowerBound": "-0.2",
            "UpperBound": "2",
            "ChangeType": "FRAC",
            "ForVariable": "Flow"
        },
        "27": {
            "ObjectID": "27",
            "Symbol": "SOL_AWC",
            "File": ".sol",
            "Unit": "%",
            "InitVal": "0.4941",
            "selectFlag": "1",
            "LowerBound": "-0.5",
            "UpperBound": "0.5",
            "ChangeType": "FRAC",
            "ForVariable": "Flow"
        },
        "28": {
            "ObjectID": "28",
            "Symbol": "SOL_K",
            "File": ".sol",
            "Unit": "%",
            "InitVal": "0.4877",
            "selectFlag": "1",
            "LowerBound": "-0.5",
            "UpperBound": "0.5",
            "ChangeType": "FRAC",
            "ForVariable": "Flow"
        },
        "29": {
            "ObjectID": "29",
            "Symbol": "CH_KI",
            "File": ".sub",
            "Unit": "mm/hr",
            "InitVal": "99.66",
            "selectFlag": "1",
            "LowerBound": "0",
            "UpperBound": "250",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "30": {
            "ObjectID": "30",
            "Symbol": "CH_NI",
            "File": ".sub",
            "Unit": "-",
            "InitVal": "0.04644",
            "selectFlag": "1",
            "LowerBound": "0.01",
            "UpperBound": "0.2",
            "ChangeType": "ABS",
            "ForVariable": "Flow"
        },
        "31": {
            "ObjectID": "31",
            "Symbol": "ADJ_PKR",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "1.25",
            "selectFlag": "0",
            "LowerBound": "0.5",
            "UpperBound": "2",
            "ChangeType": "ABS",
            "ForVariable": "Sediment"
        },
        "32": {
            "ObjectID": "32",
            "Symbol": "PRF",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "1",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "2",
            "ChangeType": "ABS",
            "ForVariable": "Sediment"
        },
        "33": {
            "ObjectID": "33",
            "Symbol": "SPCON",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "0.00505",
            "selectFlag": "0",
            "LowerBound": "0.0001",
            "UpperBound": "0.01",
            "ChangeType": "ABS",
            "ForVariable": "Sediment"
        },
        "34": {
            "ObjectID": "34",
            "Symbol": "SPEXP",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "1.5",
            "selectFlag": "0",
            "LowerBound": "1",
            "UpperBound": "2",
            "ChangeType": "ABS",
            "ForVariable": "Sediment"
        },
        "35": {
            "ObjectID": "35",
            "Symbol": "SLSUBBSN",
            "File": ".hru",
            "Unit": "m",
            "InitVal": "80",
            "selectFlag": "0",
            "LowerBound": "10",
            "UpperBound": "150",
            "ChangeType": "ABS",
            "ForVariable": "Sediment"
        },
        "36": {
            "ObjectID": "36",
            "Symbol": "USLE_P",
            "File": ".mgt",
            "Unit": "-",
            "InitVal": "0.5",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Sediment"
        },
        "37": {
            "ObjectID": "37",
            "Symbol": "CH_COV1",
            "File": ".rte",
            "Unit": "-",
            "InitVal": "0.03696",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Sediment"
        },
        "38": {
            "ObjectID": "38",
            "Symbol": "CH_COV2",
            "File": ".rte",
            "Unit": "-",
            "InitVal": "0.2191",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Sediment"
        },
        "39": {
            "ObjectID": "39",
            "Symbol": "USLE_K",
            "File": ".sol",
            "Unit": "%",
            "InitVal": "0.25",
            "selectFlag": "0",
            "LowerBound": "-0.5",
            "UpperBound": "0.5",
            "ChangeType": "FRAC",
            "ForVariable": "Sediment"
        },
        "40": {
            "ObjectID": "40",
            "Symbol": "USLE_C",
            "File": "crop.dat",
            "Unit": "%",
            "InitVal": "0.25",
            "selectFlag": "0",
            "LowerBound": "-0.5",
            "UpperBound": "0.5",
            "ChangeType": "FRAC",
            "ForVariable": "Sediment"
        },
        "41": {
            "ObjectID": "41",
            "Symbol": "CDN",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "0.5",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "42": {
            "ObjectID": "42",
            "Symbol": "NPERCO",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "0.505",
            "selectFlag": "0",
            "LowerBound": "0.01",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "43": {
            "ObjectID": "43",
            "Symbol": "RCN",
            "File": ".bsn",
            "Unit": "mg-N/l",
            "InitVal": "7.5",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "0.50 ",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "44": {
            "ObjectID": "44",
            "Symbol": "SDNCO",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "0.5",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "45": {
            "ObjectID": "45",
            "Symbol": "ORGN",
            "File": ".chm",
            "Unit": "kg-N/ha",
            "InitVal": "500",
            "selectFlag": "0",
            "LowerBound": "1",
            "UpperBound": "1000",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "46": {
            "ObjectID": "46",
            "Symbol": "SOLN",
            "File": ".chm",
            "Unit": "-",
            "InitVal": "2.55",
            "selectFlag": "0",
            "LowerBound": "0.1",
            "UpperBound": "5",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "47": {
            "ObjectID": "47",
            "Symbol": "DEP_IMP",
            "File": ".hru",
            "Unit": "mm",
            "InitVal": "2000",
            "selectFlag": "0",
            "LowerBound": "1500",
            "UpperBound": "2500",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "48": {
            "ObjectID": "48",
            "Symbol": "DDRAIN",
            "File": ".mgt",
            "Unit": "mm",
            "InitVal": "1000",
            "selectFlag": "0",
            "LowerBound": "500",
            "UpperBound": "1500",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "49": {
            "ObjectID": "49",
            "Symbol": "GDRAIN",
            "File": ".mgt",
            "Unit": "hr",
            "InitVal": "50",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "100",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "50": {
            "ObjectID": "50",
            "Symbol": "TDRAIN",
            "File": ".mgt",
            "Unit": "hr",
            "InitVal": "36",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "72",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "51": {
            "ObjectID": "51",
            "Symbol": "BC1",
            "File": ".swq",
            "Unit": "1/day",
            "InitVal": "0.55",
            "selectFlag": "0",
            "LowerBound": "0.1",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "52": {
            "ObjectID": "52",
            "Symbol": "BC2",
            "File": ".swq",
            "Unit": "1/day",
            "InitVal": "1.1",
            "selectFlag": "0",
            "LowerBound": "0.2",
            "UpperBound": "2",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "53": {
            "ObjectID": "53",
            "Symbol": "BC3",
            "File": ".swq",
            "Unit": "1/day",
            "InitVal": "0.3",
            "selectFlag": "0",
            "LowerBound": "0.2",
            "UpperBound": "0.4",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "54": {
            "ObjectID": "54",
            "Symbol": "RS3",
            "File": ".swq",
            "Unit": "mg/m2-day",
            "InitVal": "0.5",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "55": {
            "ObjectID": "55",
            "Symbol": "RS4",
            "File": ".swq",
            "Unit": "1/day",
            "InitVal": "0.0505",
            "selectFlag": "0",
            "LowerBound": "0.001",
            "UpperBound": "0.1",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "56": {
            "ObjectID": "56",
            "Symbol": "AI1",
            "File": ".wwq",
            "Unit": "-",
            "InitVal": "0.08",
            "selectFlag": "0",
            "LowerBound": "0.07",
            "UpperBound": "0.09",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "57": {
            "ObjectID": "57",
            "Symbol": "K_N",
            "File": ".wwq",
            "Unit": "-",
            "InitVal": "0.155",
            "selectFlag": "0",
            "LowerBound": "0.01",
            "UpperBound": "0.3",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "58": {
            "ObjectID": "58",
            "Symbol": "P_N",
            "File": ".wwq",
            "Unit": "-",
            "InitVal": "0.5",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "1",
            "ChangeType": "ABS",
            "ForVariable": "Nitrogen"
        },
        "59": {
            "ObjectID": "59",
            "Symbol": "PHOSKD",
            "File": ".bsn",
            "Unit": "m3/Mg",
            "InitVal": "150",
            "selectFlag": "0",
            "LowerBound": "100",
            "UpperBound": "200",
            "ChangeType": "ABS",
            "ForVariable": "Phosphorus"
        },
        "60": {
            "ObjectID": "60",
            "Symbol": "PPERCO",
            "File": ".bsn",
            "Unit": "10m3/Mg",
            "InitVal": "13.75",
            "selectFlag": "0",
            "LowerBound": "10",
            "UpperBound": "17.5",
            "ChangeType": "ABS",
            "ForVariable": "Phosphorus"
        },
        "61": {
            "ObjectID": "61",
            "Symbol": "PSP",
            "File": ".bsn",
            "Unit": "-",
            "InitVal": "0.355",
            "selectFlag": "0",
            "LowerBound": "0.01",
            "UpperBound": "0.7",
            "ChangeType": "ABS",
            "ForVariable": "Phosphorus"
        },
        "62": {
            "ObjectID": "62",
            "Symbol": "LABP",
            "File": ".chm",
            "Unit": "mg/kg",
            "InitVal": "5",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "10",
            "ChangeType": "ABS",
            "ForVariable": "Phosphorus"
        },
        "63": {
            "ObjectID": "63",
            "Symbol": "ORGP",
            "File": ".chm",
            "Unit": "kg-P/ha",
            "InitVal": "10",
            "selectFlag": "0",
            "LowerBound": "0",
            "UpperBound": "20",
            "ChangeType": "ABS",
            "ForVariable": "Phosphorus"
        },
        "64": {
            "ObjectID": "64",
            "Symbol": "RS2",
            "File": ".swq",
            "Unit": "mg/m2-day",
            "InitVal": "0.0505",
            "selectFlag": "0",
            "LowerBound": "0.001",
            "UpperBound": "0.1",
            "ChangeType": "ABS",
            "ForVariable": "Phosphorus"
        },
        "65": {
            "ObjectID": "65",
            "Symbol": "RS5",
            "File": ".swq",
            "Unit": "1/day",
            "InitVal": "0.0505",
            "selectFlag": "0",
            "LowerBound": "0.001",
            "UpperBound": "0.1",
            "ChangeType": "ABS",
            "ForVariable": "Phosphorus"
        },
        "66": {
            "ObjectID": "66",
            "Symbol": "AI2",
            "File": ".wwq",
            "Unit": "-",
            "InitVal": "0.015",
            "selectFlag": "0",
            "LowerBound": "0.01",
            "UpperBound": "0.02",
            "ChangeType": "ABS",
            "ForVariable": "Phosphorus"
        }
    }

}
