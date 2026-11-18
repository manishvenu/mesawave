"""Core-hours charged to MESAWAVE jobs, by project code, for docs/source/compute.md.

usage: core_hours.py DERECHO_CSV CASPER_CSV

Make each CSV on its machine with
    qhist -u manishrv -d 120 -t h -c --format="short_id,account,name,queue,numnodes,numcpus,elapsed,start,status"
Derecho's main queue charges whole nodes (nodes x 128 x hours); its develop queue (cpudev) and Casper
charge the cores used. MESAWAVE jobs are picked by job name (GROUPS); every NCGD0039 job counts.
Add a pattern to GROUPS when a new kind of case is run.
"""
import collections
import csv
import re
import sys

GROUPS = [  # (label, regex on the job name)
    ("wu025r005 scaling runs", r"wu025r005_scaling"),
    ("wu025r005 smoke runs", r"mesaclip_ww3_wu025r005"),
    ("ERA5 runs on wu025r004/wu025r005", r"era5uw_ww3_"),
    ("Mesh builds and staging", r"ww3mesh_|ww3_stage"),
    ("Point output test", r"pointout_ww3"),
    ("wu2r05 global test", r"mesaclip_ww3_wu2r05"),
    ("A cases", r"mesaclip_a_hist|mesaclip_dice_a_hist"),
    ("Regional WW3 tests", r"mesaclip_ww3_alaska|mesaclip_dice_ww3_alaska|mesaclip_ww3_offset|mesaclip_crocodash_alaska"),
    ("Ice tests", r"alaska_ice_|alaska_cice_ww3"),
    ("CDEPS tests and checks", r"T62_t232_w|cdeps_years_cjra|gwr_jra_cplhist|u10_"),
]

total, group = collections.defaultdict(float), collections.defaultdict(float)
for path, machine in ((sys.argv[1], "Derecho"), (sys.argv[2], "Casper")):
    for r in csv.DictReader(open(path)):
        account, name, hours = r["Account"].upper(), r["Job Name"], float(r["Elapsed"])
        whole_nodes = machine == "Derecho" and r["Queue"] != "cpudev"
        charged = hours * (int(r["Nodes"]) * 128 if whole_nodes else int(r["NCPUs"]))
        label = next((g for g, rx in GROUPS if re.search(rx, name)), None)
        if label is None and account == "NCGD0039":
            label = "Other"
        if label is None:
            continue
        total[(account, machine)] += charged
        group[(account, label)] += charged

for (account, machine), v in sorted(total.items()):
    print(f"{account} {machine:8} {v:10,.0f}")
for (account, label), v in sorted(group.items()):
    print(f"{account} {label:40} {v:10,.0f}")
