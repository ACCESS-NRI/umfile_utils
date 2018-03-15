# Based on sortum perl script, but extended to work with file suffixes
# like .nc

import sys, re

months = {'jan':'01', 'feb':'02', 'mar':'03', 'apr':'04',
          'may':'05', 'jun':'06', 'jul':'07', 'aug':'08',
          'sep':'09', 'oct':'10', 'nov':'11', 'dec':'12'}

fname_re = re.compile("[a-z][a-z]\d{3,3}a.p[a-z]\d{4,4}(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).*")

flist = []
for fname in sys.argv[1:]:
    m = fname_re.match(fname)
    if m:
        key = fname[m.start(0):m.start(1)] + months[m.group(1)] +\
              fname[m.end(1):m.end()]
        flist.append((key, fname))
    else:
        flist.append((fname, fname))

flist.sort()

for f in flist:
    sys.stdout.write('%s ' % f[1])
        

