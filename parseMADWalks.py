from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

from lxml import html
import requests
import pickle

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/MADWalkers-calendar-python.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'MADWalkersCalendar'
CALENDAR = "iseo90qh8hj6o5lrj6mhrr0srg@group.calendar.google.com" 

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'MADWalkers-calendar-python.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_colours():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    colors = service.colors().get().execute()

    # Print available calendarListEntry colors.
    print("Calendar Colours")
    for id, color in colors['calendar'].items():
        print('colorId: %s' % id)
        print('  Background: %s' % color['background'])
        print('  Foreground: %s' % color['foreground'])
    # Print available event colors.
    print("Event Colours")
    for id, color in colors['event'].items():
        print('colorId: %s' % id)
        print('  Background: %s' % color['background'])
        print('  Foreground: %s' % color['foreground'])

def get_walks():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)



    page = requests.get("http://madwalkers.org.uk/walks/")
    tree = html.fromstring(page.content)
    
    walks_xpath = "/html/body/div[1]/table/tr[2]/td[3]/div[1]/div[position()>1]"
    
    walks = tree.xpath(walks_xpath)
    walks_number = tree.xpath("count("+walks_xpath+")")

    try:
        with open("walks.pickle","rb") as input:
	        all_walks_dict = pickle.load(input)
    except:
        all_walks_dict = {}
    
    try:
        for i in range(int(walks_number)):
            walk = walks[i]
            walk_dict = {}
        
            walk_id = walk.xpath("@id")[0]
            walk_dict["web_id"] = walk_id
            walk_dict["colour_id"] = 3
        
            walk_day = walk.xpath(".//p[@class='pIconDay']/text()")[0]
            walk_month_node = walk.xpath(".//td[starts-with(@class, 'imgMon')]")
            walk_month = walk_month_node[0].xpath("@class")[0].replace("imgMon","")
            
            walk_dict["day"] = walk_day
            walk_dict["month"]= walk_month
        
            walk_title = walk.xpath(".//a[@class='pWalkTitle']/text()")[0]
            walk_dict["title"] = walk_title
        
            walk_brief = "".join(walk.xpath(".//p[@class='pHdr']/text()"))
            walk_dict["brief"] = walk_brief.encode('utf-8')
        
            if "Public Transport" in walk_brief:
                walk_dict["transport"] = "Public"
            else:
                walk_dict["transport"] = "Direct"
        
            walk_full = ("".join(walk.xpath(".//table[@class='walkTableGD'][1]/tr[2]/td[2]//text()"))).replace("\t","")
        
            walk_dict["full"] = walk_full.encode('utf-8')

            try:    
                walk_special_notes = walk.xpath(".//span[contains(@style,'color:#ff0000')]//text()")
                walk_special_notes = " ".join(walk_special_notes)
            except:
                walk_special_notes = "" 
 
            walk_dict["special"] = walk_special_notes.encode('utf-8')    
                
        
            try:
                walk_length = walk.xpath(".//p[@class='pIconPanel']/text()")[0]
            except:
                walk_length = "TBD"
        
            walk_dict["length"] = walk_length
        
            try:
                walk_ascent = walk.xpath(".//p[@class='pIconAscent']/text()")[0]
            except:
                walk_ascent = "TBD"
        
            walk_dict["ascent"] = walk_ascent
        
            try:
                time = walk.xpath(".//td[@class='tdMeetTm']/p/text()")[0]
                first_step = "".join(walk.xpath(".//td[@class='tdMeetDt']")[0].xpath(".//text()"))
                walk_start = time+": "+first_step
            except:
                walk_start = "TBD"
       
            walk_dict["start"] = walk_start.encode('utf-8')

            step_text = ""
            try:
                single_step = walk.xpath(".//table[@class='walkTableGD'][2]/tr[2]/td[2]/table/tr")
                

                steps = walk.xpath(".//td[@class='tdMeetDt']")

                for i in range(len(single_step)):
                    step_text += "".join(single_step[i].xpath(".//td[@class='tdMeetTm']//text()"))+"\n"
                    step_text += "".join(single_step[i].xpath(".//td[@class='tdMeetDt']//text()"))+"\n"

            except:
               step_text = ""

            walk_dict["steps"] = step_text.encode('utf-8')
   
            if not walk_dict['web_id'] in all_walks_dict:
                new_walk(walk_dict,service)
                all_walks_dict[walk_dict["web_id"]] = walk_dict
                print(walk_dict['calendar_id'])
            else:
                walk_dict['calendar_id'] = all_walks_dict[walk_dict["web_id"]]['calendar_id']
                if not all_walks_dict[walk_dict["web_id"]] == walk_dict:
                    changed_walk(walk_dict,service)
                    all_walks_dict[walk_dict["web_id"]] = walk_dict    
    except:
        with open("walks.pickle", "wb") as output:
            pickle.dump(all_walks_dict, output, pickle.HIGHEST_PROTOCOL)       
        raise 

    with open("walks.pickle", "wb") as output:
        pickle.dump(all_walks_dict, output, pickle.HIGHEST_PROTOCOL)


def get_event(walk_dict):
    now = datetime.datetime.now()
    event = {
        'summary': 'WALK: ('+str(walk_dict['length'])+", "+str(walk_dict["ascent"])+", "+str(walk_dict['transport'])+") "+str(walk_dict['title']),
        'location': walk_dict['start'],
        'description': 'Length: '+str(walk_dict["length"])+' \nAscent: '+str(walk_dict["ascent"])+" \nTransport: "+str(walk_dict["transport"])+"\n"+str(walk_dict["full"])+"\n"+str(walk_dict["steps"])+"\n"+str(walk_dict["special"]),
        'start': {
            'date': str(now.year)+'-'+str(walk_dict["month"])+'-'+str(walk_dict["day"]),
        },
        'end': {
            'date': str(now.year)+'-'+str(walk_dict["month"])+'-'+str(walk_dict["day"]),
        },
        'colorId': walk_dict["colour_id"],
    }
    return event

def new_walk(walk_dict,service):
    print("Adding NEW Walk")
    event_dict = get_event(walk_dict)
    event = service.events().insert(calendarId=CALENDAR, body=event_dict).execute()
    walk_dict['calendar_id'] = event.get("id")
    return 

def changed_walk(walk_dict,service):
    print("Updating CHANGED walk")
    event_dict = get_event(walk_dict)
    print(walk_dict['calendar_id'])
    event = service.events().update(calendarId=CALENDAR, eventId=walk_dict['calendar_id'], body=event_dict).execute()
    return 


if __name__ == "__main__":
    #get_colours()
    get_walks()    
	
