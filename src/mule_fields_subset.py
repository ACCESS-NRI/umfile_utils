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

    # Define input/output file paths and the fields you want to remove
    input_file = "/home/198/lo9311/access-esm1.5/preindustrial+concentrations/archive/restart000/atmosphere/restart_dump_old_perturb.astart"
    output_file = "/home/198/lo9311/access-esm1.5/preindustrial+concentrations/archive/restart000/atmosphere/modified_file.astart"
    fields_to_remove = [155,156,3100, 3101, 33001, 33002]  # Example list of STASH codes or section numbers to remove

    um_file = mule.UMfile.from_file(input_file)
    

    remove_fields(um_file, output_file, fields_to_remove)

if __name == "__main__":
    main()
