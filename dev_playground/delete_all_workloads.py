import sys

from pylo import log
import logging

sys.path.append('..')

import argparse
import pylo

parser = argparse.ArgumentParser(description='TODO LATER')
parser.add_argument('--pce', type=str, required=True,
                    help='hostname of the PCE')
parser.add_argument('--debug', type=bool, nargs='?', required=False, default=False, const=True,
                    help='Enabled extra debug output')

args = vars(parser.parse_args())

if args['debug']:
    pylo.log_set_debug()

targetHostname = args['pce']
numberOfWorkloadsPerBatch = 100

target = pylo.Organization(1)
print("Loading Organization's data from API... ", flush=True, end='')
target.load_from_saved_credentials(targetHostname)
print("done!")

print("Organisation Statistics:\n", target.stats_to_str())

print("\n")

deletedWorkloads = 0

href_list = list(target.WorkloadStore.items_by_href.keys())

while deletedWorkloads < len(target.WorkloadStore.items_by_href):
    print(" - Deleting workloads " + str(deletedWorkloads+1) + "-" + str(numberOfWorkloadsPerBatch+deletedWorkloads) +
          " of " + str(len(target.WorkloadStore.items_by_href)))
    href_to_delete = []
    for i in range(0, numberOfWorkloadsPerBatch):
        if deletedWorkloads+i >= len(target.WorkloadStore.items_by_href):
            continue
        href_to_delete.append(href_list[deletedWorkloads+i])

    target.connector.objects_workload_delete_multi(href_to_delete)
    deletedWorkloads += numberOfWorkloadsPerBatch






