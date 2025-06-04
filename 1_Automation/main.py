from analysis import *
# =====================
# Running the simulations
# =====================

run_benchmark(1,2,3,4,5,6)

analyse_original()

exhaustive_search(1, 2)

dIterSettings ={
    "dryRun": False,
    "winnerSampleSize": 3,
    "iterations": 3,
    "lNumOfNodes":[4, 5, 6]
}
perform_iterative_search(**dIterSettings)
perform_directed_iterative_search(maxDepth=3, **dIterSettings)

altered_mappings()

perform_priority_tests(get_priority_configs([
    "N4-PAd_Ad_Ad_MI-SFC_FC_FC_FC-V100_100_100_100",
    "N4-PAd_Ad_Ad_MI-SFC_FC_FC_PB-V75_100_100_100",
    "N4-PAd_Ad_Ad_MI-SFC_FC_PB_PB-V100_100_100_100",
    "N4-PAd_Ad_Ad_MI-SFC_FC_PB_PB-V100_100_100_75",
    "N4-PAd_Ad_Ad_MI-SPB_FC_FC_FC-V100_100_100_100",
    "N4-PMI_Ad_Ad_Ad-SFC_FC_FC_FC-V100_100_100_75",
    "N4-PMI_Ad_Ad_Ad-SPB_FC_FC_FC-V100_100_100_100",
    "N4-PMI_Ad_Ad_MI-SFC_FC_FC_FC-V100_100_100_100",
    "N4-PMI_Ad_Ad_MI-SFC_FC_FC_FC-V100_100_100_75",
    "N4-PMI_Ad_Ad_MI-SFC_FC_FC_PB-V100_100_100_100",
    "N4-PMI_Ad_Ad_MI-SFC_FC_FC_PB-V100_100_100_75",
    "N4-PMI_Ad_Ad_MI-SFC_FC_PB_PB-V100_100_100_100",
    "N4-PMI_Ad_Ad_MI-SPB_FC_FC_FC-V100_100_100_100",
    "N4-PMI_Ad_Ad_MI-SPB_FC_FC_FC-V100_100_100_66",
    "N4-PMI_Ad_Ad_MI-SPB_FC_FC_PB-V100_100_100_100",
    "N4-PMI_Ad_Ad_MI-SPB_FC_PB_PB-V100_100_100_100",
    "N4-PMI_Ad_Ad_MI-SPB_FC_PB_PB-V100_100_100_75",
]))

print("Finished")