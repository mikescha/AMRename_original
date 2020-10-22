
import time
from datetime import datetime
from pytz import timezone
import pytz
from pytz import all_timezones_set, common_timezones_set

# see also http://pytz.sourceforge.net/#localized-times-and-date-arithmetic

def main(): 
    date_list = ["20190101_010130", "20190515_231545", "20191130_123059"]
    timezone_dict = {"Eastern":"America/New_York",
                     "Central":"America/Chicago",
                     "Mountain":"America/Denver", 
                     "Pacific":"America/Los_Angeles",
                     "Arizona (no DST)":"America/Phoenix",
                     }
    
    print("Which of these is your local time zone?")
    for z in timezone_dict:
        print(z)

    while True:
        user_zone = input("Type the first letter of your zone and press ENTER: ")
            
        local_tz = ""
        for z in timezone_dict:
            if z[0].lower() == user_zone[0].lower():
                print("Using time zone: " + z)
                local_tz = timezone(timezone_dict[z])

        if local_tz == "":
            print("Invalid zone entered, try again.")
            continue            

        break
    

    for choice in date_list:
        utc = pytz.utc
        utc_time = utc.localize(datetime.strptime(choice,"%Y%m%d_%H%M%S"))
        for z in timezone_dict:
            local_tz = timezone(timezone_dict[z])
            local_dt = utc_time.astimezone(local_tz)
            filename = "site_" + time.strftime("%Y-%m-%d_%H-%M", local_dt.timetuple()) + ".wav"
            print("\nOriginal time: " + utc_time.strftime("%d-%b-%Y (%H:%M:%S)"))
            print("Local time   : " + local_dt.strftime("%d-%b-%Y (%H:%M:%S)") + " (" + z + ")")
            print("New filename : " + filename)
        input("\nPress ENTER to continue")

if __name__ == '__main__': 
    main() 