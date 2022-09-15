import sys

log = sys.argv[1]

with open(log, 'r') as f:
        lines = [i.rstrip() for i in f.readlines()]

#print (f"{len(lines)}")

#automatically detect synchroniser names
syncs = []
for line in lines:
    if 'Label:' in line:
        if line.split(" ")[1] not in syncs:
            syncs.append(line.split(" ")[1])

#build map of file - each run of the list_synchronisers.py is ended with a summary of synchronsiers, both running and pending listed ..
run_map = {}
line_count = 1
for line in lines:
    if 'dhus for hub' in line:
        
        #extract datetime for this run
        run_map[line_count] = f"{line.split(' ')[-2]} {line.split(' ')[-1]}"

    line_count += 1


#now run through markers and extract publication delays for the 2 synchronisers
#sync1_name='S2A_MSIL1_GLOB_dhr__10022022T154348'
#sync2_name='S2B_MSIL1_GLOB_dhr__10022022T154335'

cnt = 1

plot_data = {}

for i in run_map.keys():

    revcntr = 1

    sync_lcds = {}
    
    #go to line number in file
    while revcntr <= 7: #safety line

        analyse_line = lines[i-revcntr]

        #search backwards (upwards in file!) and find FIRST instances of sync entry..
        for sync in syncs:
            if sync in analyse_line:
                if sync not in sync_lcds.keys():
                    sync_lcds[sync] = analyse_line.split(' ')[15]

        revcntr+=1

    #pad out any unused synchronisers to make it easier to print out later
    for available_sync in syncs:
        if available_sync not in plot_data.keys():
            plot_data[available_sync] = 'NULL'

    plot_data[run_map[i]] = sync_lcds
    cnt += 1

#print column headers
print(f"Date,{','.join(str(x) for x in syncs)}")

for i in run_map.keys():

    #print all on one line to stdout - padding out where any missing entries for changed synchronisers
    #remember that input file is a weeks worth of LCD polls.... so syncs can change in that time
    #print (f"{cnt},{run_map[i]},{sync1_name_lcd},{sync2_name_lcd}")

    #construct one line string
    lsyncs = [plot_data[run_map[i]][j] for j in syncs]
    print (f"{run_map[i]},{','.join(str(x) for x in lsyncs)}")