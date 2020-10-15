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
import datetime
import pytz
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
    print('   -h               Display this help screen')

#### Copy files to new directory
def copy_files_to_new_dir(from_dir, to_dir):
    original_dir = os.listdir(from_dir)
    #Check if we found any files or not
    #TODO Return True if it worked, False if an error happened
    if original_dir:
        for item in original_dir:
            for root, dirs, files in os.walk(from_dir):
                for basename in files:
                    if fnmatch.fnmatch(basename, item):
                        full_path_filename = os.path.join(root, basename).replace('\\', '/')
                        try:
                            shutil.copy2(full_path_filename, to_dir)
                        except shutil.SameFileError:
                            pass
    else:
        print("Error! Source directory is empty, no files found.")

#### Go through a folder and rename all the files
def convert_files(to_dir, site_name, use_local_time):
    new_dir = os.listdir(to_dir)
    #TODO Validate that there are files to rename
    for item in new_dir:
        for root, dirs, files in os.walk(to_dir):
            for basename in files:
                if fnmatch.fnmatch(basename, item):
                    absolute_path = os.path.join(root, basename).replace('\\', '/')

      # get the full file name
        debug('Test and then rename ' + absolute_path)
        if iswavfile(absolute_path): 
            file = os.path.splitext(absolute_path)[0]

          # split off file name and convert, but only if it's valid hex
            am_format = os.path.split(file)[1]
            if ishex(am_format):
                py_hex = '0x' + am_format

                # based on user's choice, convert the time
                if use_local_time == True:
                    time_str = time.strftime('%Y-%m-%d_%H-%M', time.localtime(int(py_hex, 16)))
                else:
                    time_str = time.strftime('%Y-%m-%d_%H-%M', time.gmtime(int(py_hex, 16)))  
    
                # rebuild the file name and rename
                new_file_name = site_name + '-' + time_str + '.WAV'
                dst = to_dir + '\\' + new_file_name
                src = to_dir + '\\' + item
                
                i = 1
                while os.path.exists(dst):
                    # Error -- file already exists, could be because two files are just a few seconds apart so the names, 
                    # when rounded to the nearest minute, are the same. Create a special error name and continue.
                    print('Tried to rename ' + src + ' to ' + dst + ' but that file already exists.')
                    
                    new_file_name = site_name + '-' + time_str + ' RENAME ERROR ' + str(i) + '.WAV'
                    dst = to_dir + '\\' + new_file_name    
                    i += 1

                os.rename(src, dst)

            else:
                # file name not hex
                debug('Filename is not hex: ' + am_format)

                # file is always UTC. May or may not need to convert it to local time
                utc_time = datetime.datetime.strptime(am_format,"%Y%m%d_%H%M%S")


        else: 
            # filename not valid type
            debug('Wrong file type: ' + absolute_path)


#### Make a copy of the specified folder and rename all files in it
def copy_and_rename_folder(from_dir, new_folder_modifier, site_name, use_local_time):
  # determine directory name
    to_dir = from_dir + new_folder_modifier
    print('Files will be saved here:', to_dir)

  # If the folder already exists, then prompt how to continue
    if os.path.exists(to_dir):
        choice = input('This folder already exists! s = Skip to next folder, c = Continue copying this folder ')
        if  choice == 's':
            return
        # anything besides 's' will just continue copying
    else:
        os.mkdir(to_dir)
   
  # copy files to new directory
    copy_files_to_new_dir(from_dir, to_dir)

  # go through the new directory and rename files
    convert_files(to_dir, site_name, use_local_time)


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


#### Main
def main(argv):

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
    
    # if no action_msg set yet, then the user didn't enter one of the valid params, so let them manually type folder name
    if from_dir == '' and all_subfolders == False:
        from_dir = input('Directory to copy from: ')
        action_msg += 'Convert all files in folder:' + from_dir + '\n'
        #TODO Validate that from_dir exists

    # append time type to action msg to confirm we are doing what they want
    if convert_to_local_time == True:
        new_folder_modifier = local_time
        action_msg += 'Use local time' + '\n'
    else:
        new_folder_modifier = UTC_time
        action_msg += 'Use UTC time' + '\n'

    # User didn't pass a site name, so need to ask for it
    if site_name == '':
        site_name = input('Site name (no spaces): ')
        # The 'am' is to show that these are Audiomoth files. Remove this code if we ever want to rename other files
        site_name += 'am'
        action_msg += 'Rename using site name:' + site_name + '\n'
 

    # confirm what they want before we do it   
    print(action_msg)
    if input('Correct? (y = Yes) ').lower() != 'y':
        print('Cancelling, user did not enter y to confirm.')
        sys.exit()
        
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
                    if input('SD Card Folder contains subfolders! a=abort, c=continue ') == 'a':
                        sys.exit()
                for filename in files:
                    if iswavfile(filename) == False: 
                        if input('Folder contains %s, which is not a WAV file! a=abort, c=continue ' % filename) == 'a':
                            sys.exit()
                    if ishexfile(filename) == False:
                        if input('Folder contains %s, which is not a hex-named file! a=abort, c=continue ' % filename) == 'a':
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
            copy_and_rename_folder(dir_name, new_folder_modifier, site_name, convert_to_local_time)        
    
    else:
        copy_and_rename_folder(from_dir, new_folder_modifier, site_name, convert_to_local_time)


main(sys.argv[1:])