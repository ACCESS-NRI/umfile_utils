# Based on sortum perl script, but extended to work with file suffixes
# like .nc

# For non standard file names use the prefix argument. Otherwise assume
# everything before the first . in the first filename is the prefix

import sys, re, argparse

parser = argparse.ArgumentParser(description="Sort list of UM files ")
parser.add_argument('-p', '--prefix', dest='prefix', help='Filename prefix')
parser.add_argument('files', nargs='+', help='Filenames to sort')
args = parser.parse_args()

months = {'jan':'01', 'feb':'02', 'mar':'03', 'apr':'04',
          'may':'05', 'jun':'06', 'jul':'07', 'aug':'08',
          'sep':'09', 'oct':'10', 'nov':'11', 'dec':'12'}

if not args.prefix:
    fname = args.files[0]
    args.prefix = fname[:fname.index('.')]
fname_re = re.compile("%s.p[0-9a-z]\d{4,4}(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).*" % args.prefix)

# Standard suite name
# fname_re = re.compile("[a-z][a-z]\d{3,3}a.p[a-z]\d{4,4}(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).*")

flist = []
for fname in args.files:
    m = fname_re.match(fname)
    if m:
        key = fname[m.start(0):m.start(1)] + months[m.group(1)] +\
              fname[m.end(1):m.end()]
        flist.append((key, fname))
    else:
        raise Exception("Error in matching name %s" % fname)

flist.sort()

for f in flist:
    sys.stdout.write('%s ' % f[1])
        

