import sys

log = sys.argv[1]

with open(log, 'r') as f:
        lines = [i.rstrip() for i in f.readlines()]

print (f"{len(lines)}")

print ("hello test")

#build map of file - each run of the list_synchronisers.py is ended with a summary of synchronsiers, both running and pending listed ..
run_map = {}
line_count = 1
for line in lines:
    if 'dhus for hub' in line:
        
        #extract datetime for this run
        run_map[line_count] = f"{line.split(' ')[-2]} {line.split(' ')[-1]}"

    line_count += 1


#now run through markers and extract publication delays for the 2 synchronisers
sync1_name='S2A_MSIL1_GLOB_dhr__10022022T154348'
sync2_name='S2B_MSIL1_GLOB_dhr__10022022T154335'

cnt = 1

for i in run_map.keys():

    revcntr = 1

    sync1_name_lcd = None
    sync2_name_lcd = None

    #go to line number in file
    while revcntr <= 7: #safety line

        analyse_line = lines[i-revcntr]

        #search backwards (upwards in file!) and find FIRST instances of sync entry..
        if sync1_name in analyse_line:
            sync1_name_lcd = analyse_line.split(' ')[15]

        if sync2_name in analyse_line:
            sync2_name_lcd = analyse_line.split(' ')[15]

        #have both been found?
        if sync1_name_lcd and sync2_name_lcd:
            #print ("here")
            break

        revcntr+=1

    print (f"{cnt},{run_map[i]},{sync1_name_lcd},{sync2_name_lcd}")

    cnt += 1