from __future__ import print_function
import httplib2
import os

from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime
import json

from lxml import html
import requests
import pickle

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/MADWalkers-calendar-python.json
SEND_EMAILS = True
EMAIL_ADDRESS = 'thomaspreece10@gmail.com'

CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'MADWalkersCalendar'
CALENDAR = "iseo90qh8hj6o5lrj6mhrr0srg@group.calendar.google.com" 

if SEND_EMAILS == True:
	SCOPES = 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.send'
else:
	SCOPES = 'https://www.googleapis.com/auth/calendar'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join('./', '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'MADWalkers-calendar-email-python.json')

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

def SendMessage(sender, to, subject, msgPlain):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    message1 = CreateMessage(sender, to, subject, msgPlain)
    SendMessageInternal(service, "me", message1)

def SendMessageInternal(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except(errors.HttpError, error):
        print('An error occurred: %s' % error)

def CreateMessage(sender, to, subject, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    return {'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()}


def get_weekends():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)



    page = requests.get("https://www.madwalkers.org.uk/weekends/")
    tree = html.fromstring(page.content)
    
    weekends_xpath = "/html/body/div[7]/div[1]/div[2]/div|/html/body/div[7]/div[1]/div[2]/h3"
    
    weekends = tree.xpath(weekends_xpath)
    weekends_number = tree.xpath("count("+weekends_xpath+")")

    try:
        with open("weekends.pickle","rb") as input:
	        all_weekends_dict = pickle.load(input)
    except:
        all_weekends_dict = {}
    
    try: 
        weekend_title = ""
        weekends_dict = {}
        for i in range(int(weekends_number)):
            weekend = weekends[i]
            
			
            if(weekend.tag == "h3"):
                weekend_title = weekend.xpath(".//text()")[0]
                weekends_dict[weekend_title] = {"title": weekend_title}
            else: 
                row = weekend.xpath("./div[1]/p//text()")[0]
                rowContent = weekend.xpath("./div[2]/p//text()")[0]
                if(not "text" in weekends_dict[weekend_title]):
                    weekends_dict[weekend_title]["text"] = ""
                weekends_dict[weekend_title]["text"] = weekends_dict[weekend_title]["text"] + row + " " + rowContent
            
        print(weekends_dict)
    except:
        with open("weekends.pickle", "wb") as output:
            pickle.dump(all_weekends_dict, output, pickle.HIGHEST_PROTOCOL)       
        raise 

    with open("weekends.pickle", "wb") as output:
        pickle.dump(all_weekends_dict, output, pickle.HIGHEST_PROTOCOL)


def get_event(walk_dict):
    now = datetime.datetime.now()
    event = {
        'summary': 'WALK: ('+str(walk_dict['length'])+", "+str(walk_dict["ascent"])+", "+str(walk_dict['transport'])+") "+str(walk_dict['title']),
        'location': str(walk_dict['start']),
        'description': 'Link: '+walk_dict["web_link"]+'\nLength: '+str(walk_dict["length"])+' \nAscent: '+str(walk_dict["ascent"])+" \nTransport: "+str(walk_dict["transport"])+"\n"+str(walk_dict["full"])+"\n"+str(walk_dict["steps"])+"\n"+str(walk_dict["special"]),
        'start': {
            'date': str(walk_dict["year"])+'-'+str(walk_dict["month"])+'-'+str(walk_dict["day"]),
        },
        'end': {
            'date': str(walk_dict["year"])+'-'+str(walk_dict["month"])+'-'+str(walk_dict["day"]),
        },
        'colorId': walk_dict["colour_id"],
    }
    return event

def new_walk(walk_dict,service):
    print("Adding NEW Walk")
    print(walk_dict["title"])
    event_dict = get_event(walk_dict)
    event = service.events().insert(calendarId=CALENDAR, body=event_dict).execute()
    walk_dict['calendar_id'] = event.get("id")
    if (SEND_EMAILS == True and walk_dict["special"] != "") or (SEND_EMAILS == True and walk_dict["days_to_walk"] < 7 ):
        email_walk(walk_dict,"NEW")
    return 

def email_walk(walk_dict,new_or_update):
    subject = new_or_update+": "+walk_dict["title"]
    msg = ('Link: '+str(walk_dict["web_link"])+'\nDate:'+str(walk_dict["day"])+'/'+str(walk_dict["month"])+'/'+str(walk_dict["year"])+'\n'+"Brief: "+str(walk_dict["brief"])+'\nLength: '+str(walk_dict["length"])+' \nAscent: '+str(walk_dict["ascent"])+" \nTransport: "+str(walk_dict["transport"])+"\n"+str(walk_dict["full"].decode())+"\n"+str(walk_dict["steps"])+"\n"+str(walk_dict["special"]))
    print(msg)
    SendMessage(EMAIL_ADDRESS, EMAIL_ADDRESS , subject, msg)   

def changed_walk(walk_dict,service):
    print("Updating CHANGED walk")
    print(walk_dict['title'])
    event_dict = get_event(walk_dict)   
    event = service.events().update(calendarId=CALENDAR, eventId=walk_dict['calendar_id'], body=event_dict).execute()
    if (SEND_EMAILS == True and walk_dict["special"] != "") or (SEND_EMAILS == True and walk_dict["days_to_walk"] < 7 ):
        email_walk(walk_dict,"UPDATE")
    return 


if __name__ == "__main__":
    #get_colours()
    get_weekends()    	
