import string
import random
import os
import pwd 

def random_32_string():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))

#Read in list of users and keys
keys = []
with open("./key_list") as key_file:
    for line in key_file:
        l = line.split(":")
        user = l[0].strip()
        key = l[1].strip()
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
for pair in keys:
    with open("./sign_in.html.template", 'r') as template:
        rand_string = random_32_string()
        print("%s %s" % (pair[0], rand_string))
        with open("/var/www/html/%s" % rand_string, 'w') as html_file:
            for line in template:
                if not "{{" in line:
                    html_file.write(line)
                    continue
                #This line is a template line
                if "{{post_url}}" in line:
                    html_file.write(line.replace("{{post_url}}", "/cgi-bin/%s" % post_url))
                elif "{{params}}" in line:
                    html_file.write(line.replace("{{params}}", "name=%s&key=%s" % (pair[0], pair[1])))
                else:
                    print(line)
                    raise ValueError("Unexpected templating line")


