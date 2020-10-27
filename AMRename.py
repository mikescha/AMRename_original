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
import pytz
from pytz import timezone

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
    print('   -a               Rename all files in all subfolders starting in the current folder')
    print('   -f <foldername>  Rename all files in just the folder <foldername>')
    print('   -s <sitename>    When renaming, use the site <sitename>')
    print('   -l               When renaming, use local time (default)')
    print('   -u               When renaming, use UTC time')
    print('   -t               Tesy mode, do not rename anything, but write to a file what would be done')
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
                        dest = os.path.join(to_dir, basename).replace('\\', '/')
                        try:
                            actions += add_action("Copying: {0} to {1}".format(full_path_filename, dest))
                            if test_mode:
                                #In test mode, just make empty files
                                test_filename = os.path.join(to_dir, basename).replace('\\', '/')
                                f = open(test_filename, "w")
                                f.close()
                            else:
                                shutil.copy2(full_path_filename, to_dir)

                        except shutil.SameFileError:
                            actions += add_action("Error! {0} has the same source and destination!".format(full_path_filename))
                            result = False
                            
                        except shutil.Error as why:
                            actions += add_action("Error! {0} at {1}".format(why, full_path_filename))
                            result = False
                            
                        except OSError as why:
                            actions += add_action(("Error! OS error: {0} at {1}".format(why, full_path_filename)))
                            result = False
    else:
        result = False
        actions += add_action("Error! Source directory is empty, no files found.")
    
    #Print the results if there was an error somewhere so the user knows whether to try to continue
    if result == False:
        print(actions)
    results_file.write(actions)

    return result


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
                file_OK = True

                # Split off file name and convert. If it's valid hex then convert to decimal to calculate date string
                am_format = os.path.split(file)[1]
                if ishex(am_format):
                    debug('Filename is hex: ' + am_format)
                    hex_str = '0x' + am_format

                    # Get a datetime object with the time in UTC
                    dt = datetime.utcfromtimestamp(int(hex_str,16)).replace(tzinfo=pytz.utc)

                else:
                    # file name not hex
                    debug('Filename is not hex: ' + am_format)

                    # Confirm that the filename is in this format: YYYYMMDD_HHMMSS
                    if is_valid_filename(am_format):
                        dt = pytz.utc.localize(datetime.strptime(am_format, "%Y%m%d_%H%M%S"))
                    else:
                        msg = "Error! Filename is not valid, file not renamed: {0}  ".format(absolute_path)
                        print(msg)
                        actions += add_action(msg)
                        result = False
                        file_OK = False

                if file_OK:  
                    #Since dt object above is in UTC, need to convert it to correct tz if necessary
                    if  target_tz.zone != pytz.utc.zone:
                        dt = dt.astimezone(target_tz)

                    time_str = dt.strftime('%Y-%m-%d_%H-%M')
                    
                    # rebuild the file name and rename
                    if test_mode:
                        new_file_name = am_format + " --to-- " + site_name + '-' + time_str + '.WAV'
                    else:
                        new_file_name = site_name + '-' + time_str + '.WAV'
                    
                    src = to_dir + '\\' + item
                    dst = to_dir + '\\' + new_file_name
                
                    i = 1
                    while os.path.exists(dst):
                        # Error -- file already exists, could be because two files are just a few seconds apart so the names, 
                        # when rounded to the nearest minute, are the same. Create a special error name and continue.
                        msg = 'Tried to rename ' + src + ' to ' + dst + ' but that file already exists. Trying new name.'
                        print(msg)
                        actions += add_action(msg)
                        result = False
                    
                        new_file_name = site_name + '-' + time_str + ' RENAME ERROR ' + str(i) + '.WAV'
                        dst = to_dir + '\\' + new_file_name    
                        i += 1

                        actions += add_action("Trying {0}".format(dst))

                    actions += add_action("Renaming: {0} > {1}".format(item, new_file_name))

                    os.rename(src, dst)

            else: 
                # filename not valid type
                msg = "Error! Wrong file type, file not renamed: {0}".format(absolute_path)
                print(msg)
                actions += add_action(msg)
                result = False

    else:
        #there was nothing in to_dir
        actions = add_action("Error! No files found in {0}".format(to_dir))
        result = False

    results_file.write(actions)
    return result

#### Make a copy of the specified folder and rename all files in it
def copy_and_rename_folder(from_dir, new_folder_modifier, site_name, target_tz, test_mode, results_file):
    actions = ""

    # determine directory name
    to_dir = from_dir + new_folder_modifier
    actions += add_action('Files will be saved here:' + to_dir)
    print(actions)

    # If the folder already exists, then prompt how to continue
    if os.path.exists(to_dir):
        print("The destination folder {0} already exists! Copy files from the source folder into it and rename everything? ".format(to_dir))
        choice = input('s = Skip to next folder, c = Continue copying this folder ')
        if  choice.lower() == 's':
            actions += add_action("Skipping folder:" + to_dir)
            results_file.write(actions)
            return
        #Anything besides 's' will just continue copying
    else:
        actions += add_action("Making folder: " + to_dir)
        os.mkdir(to_dir)

    results_file.write(actions)

    # copy files to new directory
    if copy_files_to_new_dir(from_dir, to_dir, test_mode, results_file) == False:
        if input("An error occurred, see above! s = Stop now, c = Attempt to rename files: ").lower() == "s":
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

#### Confirm string matches this format: YYYYMMDD_HHMMSS
# This could get a little more complete (check that the month is 01-12) but 
# this is probably good enough considering where the files come from
def is_valid_filename(filename):
    #Strip the extension if there is one
    filename = os.path.splitext(filename)[0]

    if len(filename) == 15 and filename[0:8].isnumeric() and filename[9:15].isnumeric() and filename[8] == "_":
        return True
    else:
        return False

#### Validate a string is proper hex
def ishex(name):
    return(all(c in string.hexdigits for c in name))
    

#### Validate that the file contains a proper hex name
def ishexfile(filename):
    name = os.path.splitext(filename)[0].lower()
    debug('File: ' + name)
    return(ishex(name))


def validate_all_files(files, results_file):
    for filename in files:
        if iswavfile(filename) == False: 
            if input('Folder contains %s, which is not a WAV file! a=abort, c=continue ' % filename).lower() == 'a':
                exit_app(results_file, 1)
        
        if not ishexfile(filename) and not is_valid_filename(filename):
            msg = 'Folder contains {0}, which is neither a hex-named file nor a valid date-named file! a=abort, c=continue '.format(filename)
            if input(msg).lower() == 'a':
                exit_app(results_file, 1)


def add_action(message):
    return message + "\n"

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
        if user_zone[0].lower() == "o":
            print("Time zone not supported. App will exit.")
            local_tz = False
        else:
            for z in timezone_dict:
                if z[0].lower() == user_zone[0].lower():
                    local_tz = timezone(timezone_dict[z])

        if local_tz == "":
            print("Invalid zone entered, try again.")
            continue            

        break
    
    return local_tz

def exit_app(results_file, code):
    results_file.close()
    sys.exit(code)


#### Main
def main(argv):
    
    # Create the results file, erasing one if it was there before
    results_file = open("amresults.txt", "w+")

    # User messages
    action_msg = '\n---> Please confirm! <---\n'

    # Directional variables
    all_subfolders = False
    convert_to_local_time = True

    # Naming strings
    from_dir = ''
    local_time = '_lt'
    UTC_time = '_utc'
    new_folder_modifier = '_'
    site_name = '' 

    # Parse the command line to decide what to do
    # First, check that we don't have too many or the wrong options
    try:
        opts, args = getopt.getopt(argv,"thulaf:s:",["fdir="])
    except getopt.GetoptError:
        print('Error! Wrong arguments were entered')
        print_usage_message()
        exit_app(results_file, 2)
    
    if len(argv) > 7:
        print('Error! Too many arguments were entered')
        print_usage_message()
        exit_app(results_file, 3)
    
    # Options appear to be valid, so parse them	
    test_mode = False

    #####TODO: Make sure that when we add to the action message, it happens regardless of whether the instruction
    #####      was typed by the user or came in on the command line!

    for opt, arg in opts:
        if opt == '-h':
            print('Help message requested:')
            print_usage_message()
            exit_app(results_file, 0)
        elif opt == '-f':
            from_dir = arg
            action_msg += add_action('Convert all files in folder: ' + os.path.abspath(from_dir))
        elif opt == '-a':
            all_subfolders = True
            action_msg += add_action('Convert ALL files in ALL subfolders under ' + os.path.abspath('.'))
        elif opt == '-s':
            site_name = arg 
            # The 'am' is to show that these are Audiomoth files. Remove this codef we ever want to rename other files
            site_name += 'am'
        elif opt == '-l':
            convert_to_local_time = True
            action_msg += add_action("Convert times to local time.")
        elif opt == '-u':
            convert_to_local_time = False
            action_msg += add_action("Leave times in UTC.")
        elif opt == '-t':
            test_mode = True
            action_msg += add_action("Don\'t copy actual files, just make empty ones with the same name, and rename using both before and after names.")

    # append time type to action msg to confirm we are doing what they want
    if convert_to_local_time == True:
        target_tz = getUserTimezone()
        if target_tz == False:
            exit_app(results_file, 0)
        new_folder_modifier += datetime.now(target_tz).tzname()
        action_msg += add_action('Use same local time as ' + target_tz.zone)
    else:
        target_tz = pytz.utc
        new_folder_modifier += datetime.now(target_tz).tzname()
        action_msg += add_action('Use UTC time')

    # if the user didn't tell us where to copy from, let them manually type folder name
    if from_dir == '' and all_subfolders == False:
        #Get source directory and validate that it exists
        while True:
            from_dir = input('Directory to copy from: ')
            from_dir_fullpath = os.path.abspath('.') + "\\" + from_dir
            if os.path.isdir(from_dir_fullpath):
                break
            print("Directory " + from_dir_fullpath + "does not exist, try again.\n")

        action_msg += add_action('Copy all files from: ' + from_dir_fullpath)

    # User didn't pass a site name, so need to ask for it
    if site_name == '':
        while True:
            site_name = input('Site name (no spaces, to be used in file names): ')
            # The 'am' is to show that these are Audiomoth files. Remove this code if we ever want to rename other files
            site_name += 'am'
            confirm = input("Rename files using site name \"{0}\". (c) continue with this, (r) re-type name ".format(site_name))
            if confirm[0].lower() == "c":
                break

        action_msg += add_action("Copy files to:       " + from_dir_fullpath + new_folder_modifier)
    
    action_msg += add_action('Rename files using site name: ' + site_name)
    action_msg += add_action("For example, 20200605_003000.WAV will be renamed to " + site_name + "-2020-06-04_17-30.WAV")
    if not all_subfolders:
        action_msg += add_action("Only copy files from the top-level folder, not in subfolders.")
    
    # confirm what they want before we do it   
    print(action_msg)
    if input('Correct? (c = continue, anything else quits) ').lower() != 'c':
        print('Cancelling, user did not enter y to confirm.')
        exit_app(results_file, 0)

    
    # Log the result, so we have it for the record
    results_file.write(action_msg + "\n\n\n")

    # Do the copying and renaming in three steps
    # 1) Get the folder list (it could be just one folder)
    # 2) For each folder, make a new directory and copy all files into it
    # 3) Walk through the new directory and rename each file
  
    # If we are going through all subfolders, then start walking
    # TODO: I haven't tested this in a while, is anybody going to use it?    
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
                        exit_app(results_file, 1)

            # This is not the root dir, but a subfolder. Ensure that there are no subfolders, and only .WAV files    
            else:
                debug('Count of subfolders = %s' % len(sub_dir_list))
                if len(sub_dir_list) > 0:
                    if input('Folder contains subfolders! a=abort, c=continue ').lower() == 'a':
                        exit_app(results_file, 1)
                validate_all_files(files, results_file)

        # Assuming all is well, then do the copying and renaming
        print('You have validated all the choices and confirmed any errors, so starting to copy and rename')
        
        # Note that we are only going to walk through the top-level folders, to avoid any subfolders that might erroneously be left around
        for dir_name in next(os.walk(root_dir))[1]:
        # for dir_name, sub_dir_list, files in os.walk(root_dir):
            results_file.write('Found directory: %s' % dir_name)
            print('Found directory: %s' % dir_name)
            #if dir_name == root_dir:
            #    debug('Skipping any files in root')
            #else:
                # be sure to skip subfolders in case the user hasn't cleaned them up
            #    if len(sub_dir_list) == 0:
            #        debug('Copying and renaming %s' % dir_name)
            copy_and_rename_folder(dir_name, new_folder_modifier, site_name, target_tz, test_mode, results_file)      
            
    else:
        for dir, subdirlist, files in os.walk(from_dir_fullpath):
            validate_all_files(files, results_file)
        copy_and_rename_folder(from_dir, new_folder_modifier, site_name, target_tz, test_mode, results_file)

    print("\n\n------------\nFinished! Look in file amresults.txt for a report on what was done.\n------------\n")
    exit_app(results_file, 0)


main(sys.argv[1:])