#! /usr/bin/env python
# Last Change: Mon Jul 09 02:00 PM 2007 J

# This script generates a python file from the txt data
import time
import csv

dataname = 'heart'
f = open(dataname, 'r')
a = csv.reader(f, delimiter = ' ')
el = [i for i in a]
# Remove last value corresponding to empty line in data file
assert len(el) == 270

age = [i[0] for i in el]
sex = [i[1] for i in el]
chpain = [i[2] for i in el]
resblpress = [i[3] for i in el]
serhol = [i[4] for i in el]
fasblsug = [i[5] for i in el]
resecg = [i[6] for i in el]
maxheartrate = [i[7] for i in el]
exindang = [i[8] for i in el]
oldpk = [i[9] for i in el]
slpk = [i[10] for i in el]
nmaj = [i[11] for i in el]
thal = [i[12] for i in el]

# Write the data in oldfaitful.py
a = open("heart.py", "w")
a.write('# Autogenerated by convert.py at %s\n\n' % 
        time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()))

def dump_var(var, varname):
    import textwrap
    strvar = varname + " = " + str(var)
    a.writelines([i + '\n' for i in textwrap.wrap(strvar, 79)])
    a.write("\n")

dump_var(age, 'Age')
dump_var(sex, 'Sex')
dump_var(chpain, 'ChestPain')
dump_var(resblpress, 'RestingBloodPressure')
dump_var(serhol, 'SerumCholesterol')
dump_var(fasblsug, 'FastingBloodSugar')
dump_var(resecg, 'RestECGResults')
dump_var(maxheartrate, 'MaximumHearRate')
dump_var(exindang, 'ExerciceInducedAngina')
dump_var(oldpk, 'OldPeak')
dump_var(slpk, 'SlopePeak')
dump_var(nmaj, 'MajorVesselsFlourated')
dump_var(thal, 'Thal')
