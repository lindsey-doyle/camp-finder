#!/usr/bin/env python

import requests
from datetime import date, datetime, timedelta
from dateutil import rrule
from fake_useragent import UserAgent 
import pprint

##################
# Helper Methods #
##################

# Query API (Get Raw Data)
def get_data(url, month_params, headers):
    '''
    Queries API and returns raw data for one campground (specified by url) 
    Returns a list of dictionaries for each calendar month in date range. 
    '''
    data = []
    for month in month_params:
    
        params = {"start_date": month}
        #LOG.debug("Querying for {} with these params: {}".format(campground_id, params))
        resp = send_request(url, params, headers)
        if resp:
            data.append(resp)
    return data

# Reformat date for API - (helper for 'params')
def format_date(date_object, format_string="%Y-%m-%dT00:00:00.000Z"):
    """
    Reformats the input date to be compatible with the API
    """
    reformatted = datetime.strftime(date_object, format_string)
    return reformatted


def send_request(url, params, headers):
    """
    Send API request, returns json response.
    """
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code == 200:   
        return resp.json()
    else:
        print(resp.status_code)
        return False


def get_campground_name(campground_id, headers):
    '''
    Returns campground name for given campground_id string. 
    '''
    url = "https://www.recreation.gov/api/camps/campgrounds/{}".format(campground_id)
    resp = send_request(url, {}, headers=headers)
    return resp["campground"]["facility_name"]


def filter_data(raw_data, start_date, end_date):
    '''
        Filters through raw_data extracting only the relevent availabilities (if any).
        (or, 'Collapse the data into the output format.')
        Returns a dictionary of campcampground_id's with corresponding list of dates for which they are available.
        Only includes campsite's with at least one 'Available' date. (Values are non-empty lists.)
        Ex. 
        {'<site1>': [<date>, <date>, ...],
         '<site2>': [<date>, ...]}
    '''
    data = {}
    for month_data in raw_data:
        # Check each site for availabilities
        for site_id, site_data in month_data["campsites"].items():
            
            dates = [] # collect dates with status == "Available"
            for date, status in site_data["availabilities"].items():
                # check valid date
                if not date_in_range(start_date, end_date, date):
                    continue
                # check status
                if status != "Available":
                    continue
                # [Insert optional filters (ex. by `campsite_type`) if necessary.]
                dates.append(date)
            # If any availabilities, add to dict
            if dates:
                curr_site = data.setdefault(site_id, [])
                curr_site += dates
    return data

def date_in_range(start_date, end_date, date_str):
    '''
    Returns true if date falls within range (inclusive).
    '''
    date = datetime.strptime(date_str, "%Y-%m-%dT00:00:00Z")
    if (end_date < date) or (start_date > date):
        return False
    else:
        return True
    
def page_link(campground_id):
    '''
    Returns link to relevant page on recreation.gov.
    '''
    return "https://www.recreation.gov/camping/campgrounds/{}/availability".format(campground_id)


##########
# DRIVER #
##########

def driver(campground_id, input_start_date, input_end_date, headers=None):
    '''
    Driver method. 
    '''

    # Set headers
    if not headers:
        headers = {"User-Agent": UserAgent().random}
    
    # Convert strings to datetimes
    start_date = datetime.strptime(input_start_date, "%Y-%m-%d")
    end_date = datetime.strptime(input_end_date, "%Y-%m-%d") 

    # Get list of months formatted for API params
    start_of_month = datetime(start_date.year, start_date.month, 1) 
    months = list(rrule.rrule(rrule.MONTHLY, dtstart=start_of_month, until=end_date))
    month_params = [format_date(month) for month in months]
    
    # Get campground url
    url = "https://www.recreation.gov/api/camps/availability/campground/{}/month?".format(campground_id)
    
    # Get Raw Data
    raw_data = get_data(url, month_params, headers)
    
    # Filter data
    filtered_data = filter_data(raw_data, start_date, end_date)
    
    print("{}: {} site(s) with availability between {} and {}"
      .format(get_campground_name(campground_id, headers), 
              len(filtered_data.keys()), 
              start_date, end_date))
    print("To make a reservation go to: {}".format(page_link(campground_id)))
    #pprint.pprint(filtered_data)
    return 

if __name__ == "__main__":

    campground_id = '232825'
    input_start_date = '2020-08-29'
    input_end_date = '2020-10-30'

    driver(campground_id, input_start_date, input_end_date)


