from __future__ import print_function
import httplib2
import os

from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

from lxml import html
import requests
import pickle

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

def get_credentials(offline=True):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_path = 'MADWalkers-credentials.json'

    store = Storage(credential_path)
    credentials = store.get()
    if offline == True:
        if not credentials or credentials.invalid:
            raise ValueError("Credentials Not Found. Run authenticate.py to generate them.")
        else:
            return credentials
    else:
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            flow.params['access_type'] = 'offline'         # offline access
            flow.params['include_granted_scopes'] = "true"   # incremental auth
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
    except errors.HttpError, error:
        print('An error occurred: %s' % error)

def CreateMessage(sender, to, subject, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    return {'raw': base64.urlsafe_b64encode(msg.as_string())}


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
            walk_dict["web_link"] = "http://www.madwalkers.org.uk/walks/walk.php?id="+walk_id[5:]
            walk_dict["colour_id"] = 3

            walk_day = walk.xpath(".//p[@class='pIconDay']/text()")[0]
            walk_month_node = walk.xpath(".//td[starts-with(@class, 'imgMon')]")
            walk_month = walk_month_node[0].xpath("@class")[0].replace("imgMon","")

            today = datetime.date.today()

            if int(today.month) > 9 and int(walk_month) < 5:
                walk_year = int(today.year)+1
            else:
                walk_year = int(today.year)

            walk_dict["day"] = int(walk_day)
            walk_dict["month"]= int(walk_month)
            walk_dict["year"] = int(walk_year)

            walk_date = datetime.date(walk_dict["year"],walk_dict["month"],walk_dict["day"])

            walk_dict["days_to_walk"] = (walk_date-today).days

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
    msg = 'Link: '+walk_dict["web_link"]+'\nDate:'+str(walk_dict["day"])+'/'+str(walk_dict["month"])+'/'+str(walk_dict["year"])+'\n'+"Brief: "+walk_dict["brief"]+'\nLength: '+str(walk_dict["length"])+' \nAscent: '+str(walk_dict["ascent"])+" \nTransport: "+str(walk_dict["transport"])+"\n"+str(walk_dict["full"])+"\n"+str(walk_dict["steps"])+"\n"+str(walk_dict["special"])
    SendMessage(EMAIL_ADDRESS, EMAIL_ADDRESS , subject, msg)

def changed_walk(walk_dict,service):
    print("Updating CHANGED walk")
    event_dict = get_event(walk_dict)
    print(walk_dict['calendar_id'])
    event = service.events().update(calendarId=CALENDAR, eventId=walk_dict['calendar_id'], body=event_dict).execute()
    if (SEND_EMAILS == True and walk_dict["special"] != "") or (SEND_EMAILS == True and walk_dict["days_to_walk"] < 7 ):
        email_walk(walk_dict,"UPDATE")
    return


if __name__ == "__main__":
    #get_colours()
    get_walks()
