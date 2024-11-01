import mule
import numpy as np

def remove_fields(umfile, output_file, fields_to_remove):
    """
    This function so far does all of the work 
    """ 
    # Iterate over a copy of `um_file.fields` to avoid modifying the list while looping
    for field in um_file.fields[:]:
    
        if field.lbuser4 in fields_to_remove:
        #if field.stash in fields_to_remove:
    
            um_file.fields.remove(field)  # Directly remove the field if it matches

    # Save the modified UM file
    um_file.to_file(output_file)

def main()

    try:
    optlist, args = getopt.getopt(sys.argv[1:], 'i:n:o:psv:x:')
    for opt in optlist:
        if opt[0] == '-i':
            ifile = opt[1]
        elif opt[0] == '-n':
            nfields = int(opt[1])
        elif opt[0] == '-o':
            ofile = opt[1]
        elif opt[0] == '-p':
            prognostic = True
        elif opt[0] == '-s':
            section = True
        elif opt[0] == '-v':
            # Allow comma separated lists
            for v in opt[1].split(","):
                vlist.append(int(v))
        elif opt[0] == '-x':
            for v in opt[1].split(","):
                xlist.append(int(v))
    fields_to_remove = [155,156,3100, 3101, 33001, 33002]  # Example list of STASH codes or section numbers to remove

    um_file = mule.UMfile.from_file(input_file)
    

    remove_fields(um_file, output_file, fields_to_remove)

if __name == "__main__":
    main()
