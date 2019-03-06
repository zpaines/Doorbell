import string
import random
import os
import pwd 
import base64
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import mimetypes

def random_32_string():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))

def send_email(to_address, text):
    userId = 'me'
    message = MIMEText(text)
    message['to'] = to_address
    message['from'] = config['server_address']
    message['subject'] = "New buzzer URL"
    b64bytes = base64.urlsafe_b64encode(message.as_bytes())
    b64_string = b64bytes.decode()
    msg = {'raw' : b64_string}
    message = (service.users().messages().send(userId='me', body=msg).execute())
    print('Message Id: %s' % message['id'])
    return message

config = {}
with open('CONFIG', 'r') as config_file:
    for line in config_file:
        l = line.split(":")
        config[l[0].strip()] = l[1].strip()

creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server()
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('gmail', 'v1', credentials=creds)

#Read in list of users and keys
keys = []
with open("./key_list") as key_file:
    for line in key_file:
        l = line.split(":")
        user = l[0].strip()
        key = l[1].strip()
        if len(l) > 2:
            email = l[2].strip()
            keys.append((user, key, email))
        else:
            keys.append((user, key))

#Clear out cgi-bin directory
[ os.unlink(f.path) for f in os.scandir("/usr/lib/cgi-bin/") ]

post_url = random_32_string()
#Build the manager file and publish to /usr/lib/cgi-bin/random-token
with open("./manager.py.template", 'r') as template:
    with open("/usr/lib/cgi-bin/%s" % post_url, "w") as cgi_file:
        for line in template:
            if not "{{" in line:
                cgi_file.write(line)
                continue
            #This line is a template line
            if "{{key_list}}" in line:
                for pair in keys:
                    cgi_file.write("pw_list['%s'] = '%s'\n" % (pair[0], pair[1]))
            else:
                raise ValueError("Unexpected templating line")

os.chmod("/usr/lib/cgi-bin/%s" % post_url, 0o544)
os.chown("/usr/lib/cgi-bin/%s" % post_url, int(pwd.getpwnam('pi').pw_uid), -1)

#Clear out html directory
[ os.unlink(f.path) for f in os.scandir("/var/www/html/") ]

#Then build an html file for each user and publish to /var/www/html/random-string
for user in keys:
    with open("./sign_in.html.template", 'r') as template:
        rand_string = random_32_string()
        print("%s %s" % (user[0], rand_string))
        with open("/var/www/html/%s" % rand_string, 'w') as html_file:
            for line in template:
                if not "{{" in line:
                    html_file.write(line)
                    continue
                #This line is a template line
                if "{{post_url}}" in line:
                    html_file.write(line.replace("{{post_url}}", "/cgi-bin/%s" % post_url))
                elif "{{params}}" in line:
                    html_file.write(line.replace("{{params}}", "name=%s&key=%s" % (user[0], user[1])))
                else:
                    print(line)
                    raise ValueError("Unexpected templating line")
        if (len(user) > 2): #They have an email for notifications
            send_email(user[2], "New URL: %s:%s/%s\n This is an automated email, replies will not be read." % (config['ip_address'], config['port'], rand_string))
