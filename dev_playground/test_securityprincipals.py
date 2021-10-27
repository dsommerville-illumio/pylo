
import pylo
import sys
import argparse
import random

parser = argparse.ArgumentParser(description='TODO LATER')
parser.add_argument('--pce', type=str, required=True,
                    help='hostname of the PCE')

args = vars(parser.parse_args())

hostname = args['pce']


org = pylo.Organization(1)

print("Loading Origin PCE configuration from " + hostname + " or cached file... ", end="", flush=True)
org.load_from_cache_or_saved_credentials(hostname)
print("OK!\n")

print("Organization statistics:\n{}\n\n".format(org.stats_to_str()))

# pylo.log_set_debug()

for group in org.SecurityPrincipalStore.items_by_href.values():
    print(" - Found User Group '{}' with SID '{}'".format(group.name, group.href))
    print("    + used in '{}' places".format(group.count_references()))


base = 'S-1-5-21-1180699209-877415012-{}-1004'.format(random.randint(1000,999999))
print("\nAbout to create Group SID {}".format(base))

print(
    org.connector.objects_securityprincipal_create('grp-{}'.format(random.randint(10000,999999)), base)
)

print("\nEND OF SCRIPT\n")

