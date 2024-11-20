# From rcf_headaddress_mod.F90
# Also defined in UMDP F3

# Fixed length header constants

# Values that are array indices have had one subtraced so they work properly
# with python arrays

# Integers
FH_Version      = 0
FH_SubModel     = 1
FH_VertCoord    = 2
FH_HorizGrid    = 3
FH_Dataset      = 4
FH_RunId        = 5
FH_ExptNo       = 6
FH_CalendarType = 7
FH_GridStagger  = 8
FH_AncilDataId  = 9
FH_ProjNo       = 10
FH_OcnBndyConds = 10     # ocean boundary condition
FH_ModelVersion = 11
FH_OceanDynamics= 11
FH_ObsFileType  = 13

FH_DTYear    = 20
FH_DTMonth   = 21
FH_DTDay     = 22
FH_DTHour    = 23
FH_DTMinute  = 24
FH_DTSecond  = 25
FH_DTDayNo   = 26

FH_VTYear    = 27
FH_VTMonth   = 28
FH_VTDay     = 29
FH_VTHour    = 30
FH_VTMinute  = 31
FH_VTSecond  = 32
FH_VTDayNo   = 33

FH_CTYear    = 34
FH_CTMonth   = 35
FH_CTDay     = 36
FH_CTHour    = 37
FH_CTMinute  = 38
FH_CTSecond  = 39
FH_CTDayNo   = 40

FH_IntCStart      =  99
FH_IntCSize       = 100
FH_RealCStart     = 104
FH_RealCSize      = 105
FH_LevDepCStart   = 109
FH_LevDepCSize1   = 110
FH_LevDepCSize2   = 111
FH_RowDepCStart   = 114
FH_RowDepCSize1   = 115
FH_RowDepCSize2   = 116
FH_ColDepCStart   = 119
FH_ColDepCSize1   = 120
FH_ColDepCSize2   = 121
FH_FldsOfCStart   = 124
FH_FldsOfCSize1   = 125
FH_FldsOfCSize2   = 126
FH_ExtraCStart    = 129
FH_ExtraCSize     = 130
FH_HistStart      = 134
FH_HistSize       = 135
FH_CompFldI1Start = 139
FH_CompFldI1Size  = 140
FH_CompFldI2Start = 141
FH_CompFldI2Size  = 142
FH_CompFldI3Start = 143
FH_CompFldI3Size  = 144
FH_LookupStart    = 149
FH_LookupSize1    = 150
FH_LookupSize2    = 151
FH_NumProgFields  = 152
FH_DataStart      = 159
FH_DataSize       = 160
FH_MaxDataSize    = 161

# These are flags values rather than indices so are unchanged
FH_Version_Value     = 20
FH_SubModel_Atmos = 1
FH_SubModel_Ocean = 2
FH_SubModel_Wave  = 4

FH_VertCoord_Hybrid   = 1
FH_VertCoord_Sigma    = 2
FH_VertCoord_Pressure = 3
FH_VertCoord_Depth    = 4
FH_VertCoord_CP       = 5
FH_VertCoord_Wave     = 6

FH_HorizGrid_Global      = 0
FH_HorizGrid_NH          = 1
FH_HorizGrid_SH          = 2
FH_HorizGrid_LamNoWrap   = 3
FH_HorizGrid_LamWrap     = 4
FH_HorizGrid_Eq          = 100
FH_HorizGrid_LamNoWrapEq = 103
FH_HorizGrid_LamWrapEq   = 104

FH_GridStagger_A    = 1
FH_GridStagger_B    = 2
FH_GridStagger_C    = 3
FH_GridStagger_D    = 4
FH_GridStagger_E    = 5

FH_Dataset_InstDump = 1
FH_Dataset_MeanDump = 2
FH_Dataset_FF       = 3
FH_Dataset_Ancil    = 4
FH_Dataset_Boundary = 5
FH_Dataset_ACOBS    = 6
FH_Dataset_VAROBS   = 7
FH_Dataset_CX       = 8
FH_Dataset_COV      = 9
FH_Dataset_OBSTORE  = 10

FH_ObsFileType_Atmos = 1
FH_ObsFileType_Ocean = 2
FH_ObsFileType_SST   = 3
FH_ObsFileType_Wave  = 4

# Indices with one subtracted
IC_TorTheta      = 0   #location in header
IC_TorTheta_T      = 1 #value of above if T
IC_TorTheta_Theta  = 2 #value of above if Theta
IC_XLen          = 5
IC_YLen          = 6
IC_PLevels       = 7
IC_WetLevels     = 8
IC_SoilTLevels   = 9
IC_NoCloudLevels = 10 # ATMOS only
IC_NoSeaPts      = 10 # OCEAN only
IC_TracerLevs    = 11
IC_BLevels       = 12
IC_TracerVars    = 13
IC_HeightMethod  = 16 #method for creating heights
IC_RiverRowLength= 18 #river-routing row-length
IC_RiverRows     = 19 #river-routing rows
IC_MDI           = 20
IC_1stConstRho   = 23
IC_NumLandPoints = 24
IC_NumOzoneLevs  = 25
IC_SoilMoistLevs = 27
IC_NumObsTotal   = 27
IC_LenObCol      = 28
IC_LenCxCol      = 29 # Varobs, not acobs
IC_ObsGroup      = 30 # "
IC_ObsRelease    = 31 # "
IC_NumMetaMax    = 32 # "
IC_ConvectLevs   = 33
IC_NumItemMax    = 33 # "
IC_NumObVarMax   = 34
IC_NumObPItemMax = 35
IC_NumCxPItemMax = 36
IC_NumCxSFVarMax = 37
IC_NumCxUaVarMax = 38
IC_NumMeta       = 39
IC_NumItem       = 40
IC_NumObVar      = 41
IC_NumObPItem    = 42
IC_NumCxPItem    = 43
IC_NumCxSfVar    = 44
IC_NumCxUaVar    = 45
IC_NumObLev      = 46
IC_NumCxLev      = 47
IC_NumVarBatches = 48

RC_LongSpacing = 0
RC_LatSpacing  = 1
RC_FirstLat    = 2
RC_FirstLong   = 3
RC_PoleLat     = 4
RC_PoleLong    = 5
RC_SWLDEG      = 6     # Ocean - lat of South wall
RC_WEDGEDEG    = 7     #   "   = long of West bdy
RC_ModelTop    = 15
RC_PressureTop = 16

# Not sure what these are

## CC_Meta_Latitude  = 1 # Used in varobs
## CC_Meta_Longitude = 2 #      "
## CC_Meta_Time      = 3 #      "
## CC_Meta_Type      = 4 #      "
## CC_Meta_Call      = 5 #      "
## CC_Meta_Level     = 6 #      "
## CC_Meta_RepPGE    = 7 #      "

## CC_Item_Value = 1 # Used in varobs
## CC_Item_Error = 2 #      "
## CC_Item_PGE   = 3 #      "

## LDC_EtaTheta  = 1
## LDC_Pressure  = 1
## LDC_MLIndex   = 1
## LDC_EtaRho    = 2
## LDC_RHCrit    = 3
## SoilDepths    = 4
## LDC_ZseaTheta = 5
## LDC_CkTheta   = 6
## LDC_ZseaRho   = 7
## LDC_CkRho     = 8

# From clookadd.h
#!*L------------------ COMDECK LOOKADD ----------------------------------
#!LL
#!LL Purpose : Contains information about the format
#!LL           of the PP header

# Validity time
LBYR   =0   # Year
LBMON  =1   # Month
LBDAT  =2   # Day of month
LBHR   =3   # Hour
LBMIN  =4   # Minute
LBDAY  =5   # Day number
LBSEC  =5   # Seconds (if LBREL >= 3)

# Data time
LBYRD  =6   # Year
LBMOND =7   # Month
LBDATD =8   # Day of month
LBHRD  =9  # Hour
LBMIND =10  # Minute
LBDAYD =11  # Day number
LBSECD =11  # Seconds (if LBREL >= 3)

LBTIM  =12  # Time indicator
LBFT   =13  # Forcast period (hours)
LBLREC =14  # Length of data record
LBCODE =15  # Grid type code
LBHEM  =16  # Hemisphere indicator
LBROW  =17  # Number of rows in grid
LBNPT  =18  # Number of points per row
LBEXT  =19  # Length of extra data
LBPACK =20  # Packing method indicator
LBREL  =21  # Header release number
LBFC   =22  # Field code
LBCFC  =23  # Second field code
LBPROC =24  # Processing code
LBVC   =25  # Vertical coordinate type
LBRVC  =26  # Coordinate type for reference level

LBEXP  =27  # Experiment number
LBEGIN =28  # Start record
LBNREC =29  # No of records-Direct access only
LBPROJ =30  # Met-O-8 projection number
LBTYP  =31  # Met-O-8 field type
LBLEV  =32  # Met-O-8 level code
LBRSVD1=33  # Reserved for future PP-package use
LBRSVD2=34  # Reserved for future PP-package use
LBRSVD3=35  # Reserved for future PP-package use
LBRSVD4=36  # Reserved for future PP-package use
LBSRCE =37  # =1111 to indicate following apply to UM
DATA_TYPE =38  # Indicator for real/int or timeseries
NADDR  =39  # Start address in DATA_REAL or DATA_INT
LBUSER3=40  # Free for user-defined function
ITEM_CODE =41  #Stash code
LBPLEV =42  # Pseudo-level indicator (if defined)
LBUSER6=43  # Free for user-defined function
MODEL_CODE =44 # internal model identifier

BULEV  =45  # Upper level boundary
BHULEV =46  # Upper level boundary
BRSVD3 =47  # Reserved for future PP-package use
BRSVD4 =48  # Reserved for future PP-package use
BDATUM =49  # Datum value
BACC   =50  # (Packed fields) Packing accuracy
BLEV   =51  # Level
BRLEV  =52  # Lower level boundary
BHLEV  =53  # (Hybrid levels) A-level of value
BHRLEV =54  # Lower level boundary
BPLAT  =55  # Real latitude of 'pseudo' N Pole
BPLON  =56  # Real longitude of 'pseudo' N Pole
BGOR   =57  # Grid orientation
BZY    =58  # Zeroth latitude
BDY    =59  # Latitude interval
BZX    =60  # Zeroth longitude
BDX    =61  # Longitude interval
BMDI   =62  # Missing data indicator
BMKS   =63  # M,K,S scaling factor

## LBCC_LBYR   = 1  # Year
## LBCC_LBMON  = 2  # Month
## LBCC_LBDAT  = 3  # Day of the month
## LBCC_LBHR   = 4  # Hour
## LBCC_LBMIN  = 5  # Minute
## LBCC_LBDAY  = 6  # Day number
## LBCC_LBEGIN = 7  # Start record
## LBCC_NADDR  = 8  # Start address of DATA
