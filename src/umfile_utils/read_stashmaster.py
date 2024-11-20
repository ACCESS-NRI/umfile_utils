# Read UM STASHmaster file to set up dictionary of variable names etc.
# Field names are taken from Appendix 3 of UMCP C4

# Format of STASHmaster file is

#|Model |Sectn | Item |Name |
#|Space |Point | Time | Grid |LevelT|LevelF|LevelL|PseudT|PseudF|PseudL|LevCom|
#| Option Codes | Version Mask | Halo |
#|DataT |DumpP | PC1 PC2 PC3 PC4 PC5 PC6 PC7 PC8 PC9 PCA |
#|Rotate| PPFC | USER | LBVC | BLEV | TLEV |RBLEVV| CFLL | CFFF |

stash_sections = {
    0:"Prognostic variables at the end of the time-step",
    1: "S.W Radiation",
    2: "L.W Radiation",
    3: "Boundary Layer/Surface",
    4: "Large-Scale Precipitation",
    5: "Convection",  
    6: "Gravity Wave  drag",
    7: "Vertical diffusion",
    8: "Hydrology",
    9: "Cloud: scheme",
    10: "Adjustment",
    11: "Tracer Advection",
    12: "Primary field advection",
    13: "Diffusion and filtering",
    14: "Energy adjustment",
    15: "Processed dynamics diags",
    16: "Processed physics diags",
    17: "Sulphur Cycle",
    18: "Data assimilation",
    19: "Vegetation",
    20: "Field Calc Diagnostic",
    26: "River Routing",
    30: "Processed Climate diagnostics",
    31: "LBC fields for input (ie. by a LAM model)",
    32: "LBC fields for output",
    33: "Atmospheric Tracers",
    34: "UKCA Chemistry"}

# Variable data type
datat = { 1:"Real", 2:"Integer", 3:"Logical" }

levelt = { 0:"Unspecified", 1:"Rho", 2:"Theta", 3:"Pressure", 4:"Obsolete", 5:"Single", 6:"Deep Soil", 7:"Pot. temp." }

# Pseudo-levels, defined in UMDP C4 and UMUI atmos_STASH_Domain2.pan
pseudt = {0:'None', 
          1:'SW radiation bands', 
          2: 'LW radiation bands', 
          3: 'Atmospheric assimilation groups',
          8: 'HadCM2 Sulphate Loading Pattern Index',
          9: 'Land and vegetation surface types',
          10: 'Sea-ice categories',
          11: 'Snow layers over tiles',
          12: 'COSP radar reflectivity intervals',
          13: 'COSP hydrometeors',
          14: 'COSP lidar SR intervals',
          15: 'COSP tau bins',
          16: 'COSP subcolumns',
          101: 'Atmos User Defined Type 101',
          102: 'Atmos User Defined Type 102',
          103: 'Atmos User Defined Type 103' }


def read_stash(filename):
    f = open(filename)

    kount = 0
    last_section = 0
    stashd = {}
    for l in f.readlines():
        if l.startswith("H3"):
            s = l.split("=")
            version = s[1].strip()
        elif l.startswith("1|"):
            # Start of a new variable
            vard = {}
            s = l.split("|")
            model = int(s[1])
            if model == -1:
                break
            vard["model"] = model
            section = int(s[2])
            item = int(s[3])
            vard["section"] = int(s[2])
            vard["item"] = int(s[3])
            vard["name"] = s[4].strip()
            code = 1000*section+item
        elif l.startswith("2|"):
            s = l.split("|")
            vard["space"] = int(s[1])
            vard["point"] = int(s[2])
            vard["time"] = int(s[3])
            vard["grid"] = int(s[4])
            vard["levelt"] = int(s[5])
            vard["levelf"] = int(s[6])
            vard["levell"] = int(s[7])
            vard["pseudt"] = int(s[8])
            vard["pseudf"] = int(s[9])
            vard["pseudl"] = int(s[10])
            vard["levcom"] = int(s[11])
        elif l.startswith("3|"):
            s = l.split("|")
            vard["optioncode"] = s[1].strip()
            vard["version_mask"] = s[2].strip()
            vard["halo"] = int(s[3])
        elif l.startswith("4|"):
            s = l.split("|")
            vard["datat"] = int(s[1])
            vard["dumpp"] = int(s[2])
            vard["pc"] = [int(x) for x in s[3].split()]
            # print 'atm_stashvar[%d] = ["%s", "", "", ""]' % (code, long_name)
        elif l.startswith("5|"):
            # Last line
            s = l.split("|")
            vard["rotate"] = int(s[1])
            vard["ppfc"] = int(s[2])
            vard["user"] = int(s[3])
            vard["lbvc"] = int(s[4])
            vard["blev"] = int(s[5])
            vard["tlev"] = int(s[6])
            vard["rblevv"] = int(s[7])
            vard["cfll"] = int(s[8])
            vard["cfff"] = int(s[9])
            stashd[code] = vard

    return stashd

if __name__ == '__main__':
    stashd = read_stash("STASHmaster_A")
    print stashd[3328]
    print pseudt[stashd[3328]['pseudt']]
