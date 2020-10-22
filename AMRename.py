"""
This script takes .WAV files which are named with a Unix hex timestamp and renames them using the audiomoth date format
in UTC time.
Original Author: Sara Schmunk

Additional code by Mike Schackwitz
 - accept parameters
 - validate file and folder structure
 - walk file tree and convert entire tree

"""

import time
from datetime import datetime
from pytz import timezone
import pytz
from pytz import all_timezones_set, common_timezones_set


import os
import shutil
import fnmatch
import sys, getopt
import string


#### For turning debug output on/off, just set debug=True/False
def debug(message):
    debug = False
    if debug == True:
        print(message)


#### function to print the usage message
def print_usage_message():
    print('Time converter script options:')
    print('   No parameters:   User is prompted for all options')
    print('   -a               Rename all files in all subfolders')
    print('   -f <foldername>  Rename all files in just the folder <foldername>')
    print('   -s <sitename>    When renaming, use the site <sitename>')
    print('   -l               When renaming, use local time (default)')
    print('   -u               When renaming, use UTC time')
    print('   -t               Do not rename anything, but write to a file what would be done')
    print('   -h               Display this help screen')

#### Copy files to new directory
#### Return True if it worked, False if at least one error happened
def copy_files_to_new_dir(from_dir, to_dir, test_mode, results_file):
    result = True
    actions = ""

    original_dir = os.listdir(from_dir)
    #Check if we found any files or not
    if original_dir:
        for item in original_dir:
            for root, dirs, files in os.walk(from_dir):
                for basename in files:
                    if fnmatch.fnmatch(basename, item):
                        full_path_filename = os.path.join(root, basename).replace('\\', '/')
                        try:
                            actions += "{0} >>> {1}".format(full_path_filename, to_dir)
                            if not test_mode:
                                shutil.copy2(full_path_filename, to_dir)

                        except shutil.SameFileError:
                            actions += "Error! {0} has the same source and destination!".format(full_path_filename)
                            result = False
                            
                        except shutil.Error as why:
                            actions += "Error! {0} at {1}".format(why, full_path_filename)
                            result = False
                            
                        except OSError as why:
                            actions += ("Error! OS error: {0} at {1}".format(why, full_path_filename))
                            result = False
    else:
        result = False
        actions += "Error! Source directory is empty, no files found."
        print(actions)
    
    results_file.write(actions)
    return result



    '''
    TODO:
    0) Look for TODO and make sure I addressed them all
    1) Make a function called "Add_actions(x)" that returns X with a newline after it
    2) Implement this in all the appropriate places
    3) CODE REVIEW. Especially, make sure that any action is hidden behind the 
        if not test_mode... line
    4) Testing time!
    '''

#### Go through a folder and rename all the files
def rename_files(to_dir, site_name, target_tz, test_mode, results_file):
    result = True
    actions = ""

    new_dir = os.listdir(to_dir)
    
    if new_dir:
        for item in new_dir:
            for root, dirs, files in os.walk(to_dir):
                for basename in files:
                    if fnmatch.fnmatch(basename, item):
                        absolute_path = os.path.join(root, basename).replace('\\', '/')

            # get the full file name
            debug('Test and then rename ' + absolute_path)
            if iswavfile(absolute_path): 
                file = os.path.splitext(absolute_path)[0]
                
                # Split off file name and convert. If it's valid hex then convert before renaming
                am_format = os.path.split(file)[1]
                if ishex(am_format):
                    debug('Filename is hex: ' + am_format)
                    hex_str = '0x' + am_format

                    # Get a datetime object with the time in UTC
                    dt = datetime.utcfromtimestamp(int(hex_str,16)).replace(tzinfo=pytz.utc)

                else:
                    # file name not hex
                    debug('Filename is not hex: ' + am_format)

                    # file time is always in this format: YYYYMMDD_HHMMSS
                    # TODO check that the filename is in this format
                    dt = pytz.utc.localize(datetime.strptime(am_format, "%Y%m%d_%H%M%S"))

                #Since dt object above is in UTC, need to convert it to correct tz if necessary
                if  target_tz.zone != pytz.utc.zone:
                    dt = dt.astimezone(target_tz)

                time_str = dt.strftime('%Y-%m-%d_%H-%M')
                    
                # rebuild the file name and rename
                new_file_name = site_name + '-' + time_str + '.WAV'
                src = to_dir + '\\' + item
                dst = to_dir + '\\' + new_file_name
                
                i = 1
                while os.path.exists(dst):
                    # Error -- file already exists, could be because two files are just a few seconds apart so the names, 
                    # when rounded to the nearest minute, are the same. Create a special error name and continue.
                    err_msg = 'Tried to rename ' + src + ' to ' + dst + ' but that file already exists.'
                    print(err_msg)
                    actions += err_msg
                    
                    new_file_name = site_name + '-' + time_str + ' RENAME ERROR ' + str(i) + '.WAV'
                    dst = to_dir + '\\' + new_file_name    
                    i += 1

                    actions += "Trying {0}".format(dst)

                actions += "Renaming {0} to {1}".format(src, dst)

                if not test_mode:
                    os.rename(src, dst)


            else: 
                # filename not valid type
                actions += "Wrong file type: {0}".format(absolute_path)
                debug('Wrong file type: ' + absolute_path)

    else:
        #there was nothing in to_dir
        actions = "Error! No files found in {0}".format(to_dir)
        result = False

    results_file.write(actions)
    return result

#### Make a copy of the specified folder and rename all files in it
def copy_and_rename_folder(from_dir, new_folder_modifier, site_name, target_tz, test_mode, results_file):
    actions = ""

    # determine directory name
    to_dir = from_dir + new_folder_modifier
    actions += 'Files will be saved here:' + to_dir
    print(actions)

    # If the folder already exists, then prompt how to continue
    if os.path.exists(to_dir):
        choice = input('This folder already exists! s = Skip to next folder, c = Continue copying this folder ')
        if  choice.lower() == 's':
            actions += "skipping folder"
            results_file.write(actions)
            return
        # anything besides 's' will just continue copying
    else:
        if test_mode:
            actions += "Making folder " + to_dir
        else:
            os.mkdir(to_dir)

    results_file.write(actions)

    # copy files to new directory
    if copy_files_to_new_dir(from_dir, to_dir, test_mode, results_file) == False:
        if input("An error occurred, check the log file. s = Stop now, c = Continue and rename files ").lower() == "s":
            return

    # go through the new directory and rename files
    rename_files(to_dir, site_name, target_tz, test_mode, results_file)


#### Validate that the file is a .WAV file
def iswavfile(filename):
    ext = os.path.splitext(filename)[-1].lower()
    debug('File: ' + filename + ',  Extension: ' + ext)
    if ext == ".wav":
        return(True)
    else:
        return(False)


#### Validate a string is proper hex
def ishex(name):
    return(all(c in string.hexdigits for c in name))
    

#### Validate that the file contains a proper hex name
def ishexfile(filename):
    name = os.path.splitext(filename)[0].lower()
    debug('File: ' + name)
    return(ishex(name))


#### Ask the user for their time zone and return it. Return False if they want a TZ we don't offer.
def getUserTimezone():
    timezone_dict = {"Eastern":"America/New_York",
                     "Central":"America/Chicago",
                     "Mountain":"America/Denver", 
                     "Pacific":"America/Los_Angeles",
                     "Arizona (no DST)":"America/Phoenix",
                     "Other":"Other",
                     }
    
    print("Which of these is your local time zone?")
    for z in timezone_dict:
        print(z)

    while True:
        user_zone = input("\nType the first letter of your zone and press ENTER: ")
            
        local_tz = ""
        for z in timezone_dict:
            if z[0].lower() == user_zone[0].lower():
                if z[0].lower() == "o":
                    print("Time zone not supported. App will exit.")
                    local_tz = False
                else:
                    print("Using time zone: " + z)
                    local_tz = timezone(timezone_dict[z])

        if local_tz == "":
            print("Invalid zone entered, try again.")
            continue            

        break
    
    return local_tz



#### Main
def main(argv):
    
    # Create the results file, erasing one if it was there before
    results_file = open("amresults.txt", "w+")

    # User messages
    action_msg = '\n\n--> Please confirm:\n'

    # Directional variables
    all_subfolders = False
    convert_to_local_time = True

    # Naming strings
    from_dir = ''
    local_time = '_lt'
    UTC_time = '_utc'
    new_folder_modifier = ''
    site_name = '' 

    # Parse the command line to decide what to do
    # First, check that we don't have too many or the wrong options
    try:
        opts, args = getopt.getopt(argv,"hulaf:s:",["fdir="])
    except getopt.GetoptError:
        print('Error! Wrong arguments were entered')
        print_usage_message()
        sys.exit(2)
    
    if len(argv) > 7:
        print('Error! Too many arguments were entered')
        print_usage_message()
        sys.exit(2)
    
    # Options appear to be valid, so parse them	
    test_mode = False
    for opt, arg in opts:
        if opt == '-h':
            print('Help message requested:')
            print_usage_message()
            sys.exit()
        elif opt == '-f':
            from_dir = arg
            action_msg += 'Convert all files in folder: ' + os.path.abspath(from_dir) + '\n'
        elif opt == '-a':
            all_subfolders = True
            action_msg += 'Convert ALL files in ALL subfolders under ' + os.path.abspath('.') + '\n'
        elif opt == '-s':
            site_name = arg 
            # The 'am' is to show that these are Audiomoth files. Remove this code if we ever want to rename other files
            site_name += 'am'
            action_msg += 'Rename using site name: ' + arg + '\n'
        elif opt == '-l':
            convert_to_local_time = True
        elif opt == '-u':
            convert_to_local_time = False
        elif opt == '-t':
            test_mode = True
            action_msg += 'Don\'t rename, just create output file results.txt with what would be done\n'
       
    # if no action_msg set yet, then the user didn't enter one of the valid params, so let them manually type folder name
    if from_dir == '' and all_subfolders == False:
        #Get source directory and validate that it exists
        while True:
            from_dir = input('Directory to copy from: ')
            source_dir = os.path.abspath('.') + "\\" + from_dir
            if os.path.isdir(source_dir):
                break
            print("Directory " + source_dir + "does not exist, try again")

        action_msg += 'Convert all files in folder:' + source_dir + '\n'

    # append time type to action msg to confirm we are doing what they want
    if convert_to_local_time == True:
        target_tz = getUserTimezone()
        if target_tz == False:
            sys.exit()
        new_folder_modifier = local_time
        action_msg += 'Use local time' + '\n'
    else:
        new_folder_modifier = UTC_time
        target_tz = pytz.utc
        action_msg += 'Use UTC time' + '\n'

    # User didn't pass a site name, so need to ask for it
    if site_name == '':
        site_name = input('Site name (no spaces, to be used in file names): ')
        # The 'am' is to show that these are Audiomoth files. Remove this code if we ever want to rename other files
        site_name += 'am'
        action_msg += 'Rename using site name:' + site_name + '\n'
 
    # confirm what they want before we do it   
    print(action_msg)
    if input('Correct? (y = Yes) ').lower() != 'y':
        print('Cancelling, user did not enter y to confirm.')
        sys.exit()
    
    # Log the result, so we have it for the record
    results_file.write(action_msg + "\n\n\n")

    # Do the copying and renaming in three steps
    # 1) Get the folder list (it could be just one folder)
    # 2) For each folder, make a new directory and copy all files into it
    # 3) Walk through the new directory and rename each file
  
    # If we are going through all subfolders, then start walking    
    if all_subfolders == True:
        # Go through file system starting at current folder and validate all conditions
        root_dir = os.path.abspath('.')
        for dir_name, sub_dir_list, files in os.walk(root_dir):
            debug('Found directory: %s' % dir_name)
            
            # If the root dir, check that it doesn't contain files
            if dir_name == root_dir:
                debug('Root dir, count of files = %s' % len(files))
                if len(files) > 0:
                    if input('Site directory contains files! a=abort, c=continue ') == 'a':
                        sys.exit()

            # This is not the root dir, but a subfolder. Ensure that there are no subfolders, and only .WAV files    
            else:
                debug('Count of subfolders = %s' % len(sub_dir_list))
                if len(sub_dir_list) > 0:
                    if input('Folder contains subfolders! a=abort, c=continue ').lower() == 'a':
                        sys.exit()
                for filename in files:
                    if iswavfile(filename) == False: 
                        if input('Folder contains %s, which is not a WAV file! a=abort, c=continue ' % filename).lower() == 'a':
                            sys.exit()
                    if ishexfile(filename) == False:
                        if input('Folder contains %s, which is not a hex-named file! a=abort, c=continue ' % filename).lower() == 'a':
                            sys.exit()

        debug('User has validated all options, continuing')

        # Assuming all is well, then do the copying and renaming
        print('All is well, starting to copy and rename')
        
        # Note that we are only going to walk through the top-level folders, to avoid any subfolders that might erroneously be left around
        for dir_name in next(os.walk(root_dir))[1]:
        # for dir_name, sub_dir_list, files in os.walk(root_dir):
            print('Found directory: %s' % dir_name)
            #if dir_name == root_dir:
            #    debug('Skipping any files in root')
            #else:
                # be sure to skip subfolders in case the user hasn't cleaned them up
            #    if len(sub_dir_list) == 0:
            #        debug('Copying and renaming %s' % dir_name)
            copy_and_rename_folder(dir_name, new_folder_modifier, site_name, target_tz, test_mode, results_file)      
            
    else:
        copy_and_rename_folder(from_dir, new_folder_modifier, site_name, target_tz, test_mode, results_file)

    results_file.close()


main(sys.argv[1:])