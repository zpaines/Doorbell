#!/usr/bin/python3.5
#on my machine this lives at /usr/lib/cgi-bin/
import cgi
import cgitb
import datetime
cgitb.enable(display=0, logdir="/var/log/post_test")

pw_list = {}
#Insert user key pairs here

with open("/var/log/post_data", 'a') as logfile:
    print("Content-Type: text/html")    # HTML is following
    print()                             # blank line, end of headers
    form = cgi.FieldStorage()
    if 'name' not in form or 'key' not in form:
        logfile.write("Invalid fields in POST Request\n")
        raise KeyError('Fields are not valid in POST Request')
    name = form['name'].value
    if form['key'].value != pw_list[name]:
        logfile.write("Invalid key for user %s" % name)
        raise RuntimeError("Invalid key for user %s" % name)
    logfile.write("Opened door at %s for user %s\n" % (datetime.datetime.now(), name))

