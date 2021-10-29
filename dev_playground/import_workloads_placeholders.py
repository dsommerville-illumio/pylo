import pylo
import sys
import copy

originHostname='10.107.3.2'
targetHostname='ilo-emea-poc.xmp.net.intra'



origin = pylo.Organization(1)
target = pylo.Organization(1)


print("Loading Origin PCE configuration from " + originHostname + " or cached file... ", end="", flush=True)
origin.load_from_cache_or_saved_credentials(originHostname)
print("OK!")
print("Loading Target PCE configuration from " + targetHostname + " or cached file ... ", end="", flush=True)
target.load_from_cache_or_saved_credentials(targetHostname)
print("OK!")
print()

print("Building Origin to Target Label matching table...", flush=True, end='')
old_to_new_loc_labels = pylo.IDTranslationTable()
old_to_new_env_labels = pylo.IDTranslationTable()
old_to_new_app_labels = pylo.IDTranslationTable()
old_to_new_role_labels = pylo.IDTranslationTable()

for label in origin.LabelStore.location_labels.values():
    old_to_new_loc_labels.add_source(label.name, label)
for label in target.LabelStore.location_labels.values():
    old_to_new_loc_labels.add_destination(label.name, label)

for label in origin.LabelStore.environment_labels.values():
    old_to_new_env_labels.add_source(label.name, label)
for label in target.LabelStore.environment_labels.values():
    old_to_new_env_labels.add_destination(label.name, label)

for label in origin.LabelStore.application_labels.values():
    old_to_new_app_labels.add_source(label.name, label)
for label in target.LabelStore.application_labels.values():
    old_to_new_app_labels.add_destination(label.name, label)

for label in origin.LabelStore.role_labels.values():
    old_to_new_role_labels.add_source(label.name, label)
for label in target.LabelStore.role_labels.values():
    old_to_new_role_labels.add_destination(label.name, label)

print("OK!")

print('Location Labels Translation table stats:\n{}\n'.format(old_to_new_loc_labels.stats_to_str('  ')))

workloads_selected_for_import = origin.WorkloadStore.items_by_href

print("* After filtering %i Workloads are marked as Importable" % len(workloads_selected_for_import))

for workload in workloads_selected_for_import.values():
    print("* Processing Origin WKL '%s'%s" % (workload.name, workload.href))

    interfaces_sanitized = copy.deepcopy(workload.raw_json["interfaces"])

    #print(pylo.nice_json(interfaces_sanitized))
    for if_details in interfaces_sanitized:
        if_details.pop('network_detection_mode')
        if_details.pop('network_id')
        if_details.pop('link_state')
        if if_details['friendly_name'] is None:
            if_details.pop('friendly_name')
        if if_details['cidr_block'] is None:
            if_details.pop('cidr_block')
        if if_details['default_gateway_address'] is None:
            if_details.pop('default_gateway_address')



    newWorkloadObject = {"name": "placeholder_" + workload.name,
                         "hostname": "placeholder_" + workload.name,
                         "os_id": "Linux",
                         "os_detail": "Centos 7.1",
                         "interfaces": interfaces_sanitized,
                         "description": "[MIG|AMER|{}|{}]".format(workload.href, workload.name, workload.hostname)}

    labels = []

    if workload.loc_label is not None:
        newLabel = old_to_new_loc_labels.find_new_or_die(workload.loc_label)  # type: pylo.Label
        labels.append({'href': newLabel.href})
    if workload.env_label is not None:
        newLabel = old_to_new_env_labels.find_new_or_die(workload.env_label)  # type: pylo.Label
        labels.append({'href': newLabel.href})
    if workload.app_label is not None:
        newLabel = old_to_new_app_labels.find_new_or_die(workload.app_label)  # type: pylo.Label
        labels.append({'href': newLabel.href})
    if workload.role_label is not None:
        newLabel = old_to_new_role_labels.find_new_or_die(workload.role_label)  # type: pylo.Label
        labels.append({'href': newLabel.href})

    newWorkloadObject["labels"] = labels

    target.connector.objects_workload_create_single_unmanaged(newWorkloadObject)
    print("   - CREATED!")


print()