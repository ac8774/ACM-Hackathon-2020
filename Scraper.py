from html.parser import HTMLParser

def strip(s):
    x = s.split('\n')[-2]
    if(x[-1]==' '):
        return x[:-1]
    return x
    

class ScheduleHTMLParser(HTMLParser):

    # 0 - waiting for start of table
    # 1 - waiting for first <tr>
    # 2 - waiting for title, and second <tr>
    # 3,4,5,6 - waiting for span to end
    # 4,6,8,10 - getting data piece
    # 11,12,13,14 - getting data piece
    # 15 - getting link
    # 16,18,20,22,24,26,28 - waiting for td
    # 17,19,21,23,25,27,29 - getting data
    # 30 - checking for multiple time slots
    # 31 - done
    # -1 - DONE done
    
    def __init__(self):
        super().__init__()
        self.classes = [{}]
        self.thisclass = self.classes[0]
        self.state = 0
        self.depth = 0
        
    def handle_starttag(self, tag, attrs):
        if(tag=="br" or tag=="img"):
            return
        self.depth += 1
        if(tag == 'tr' and self.depth == 1):
            if(self.state == 16): # no scheduled meeting times! ignore
                self.thisclass = {}
                self.state = 2
                return
            self.state += 1
            if(self.state == 31):
                self.classes.append({})
                self.thisclass = self.classes[-1]
                self.state = 2
            return
        if(tag == 'a' and self.state == 15):
            self.thisclass['catalog url'] = attrs[0][1]
            self.state += 1
            return
        if(tag == 'td' and self.state in [16,18,20,22,24,26,28]):
            self.state += 1
            return
        if(tag == 'tr' and self.state == 30):
            # class has multiple times
            self.classes.append(self.thisclass.copy())
            self.thisclass = self.classes[-1]
            self.state = 16
            return
        #print(" "*self.depth+tag)
        

    def handle_endtag(self, tag):
        self.depth -= 1
        if(tag == 'span' and self.state in [3,5,7,9]):
            self.state += 1
            return

    def handle_startendtag(self, tag):
        pass

    def handle_data(self, data):
        if(data == '\n'):
            return
        if(self.state == 0 and data == "Sections Found"):
            self.state = 1
            self.depth = 0
            return
        if(self.state == 2):
            x = data.split(' - ')
            if(x[0] == "Return to Previous"):
                self.state = -1
                self.classes.pop()
                return
            if(len(x)==4):
                self.thisclass['name'], self.thisclass['crn'], self.thisclass['course'], self.thisclass['section'] = data.split(' - ')
            else:
                self.thisclass['section'] = x[-1]
                self.thisclass['course'] = x[-2]
                self.thisclass['crn'] = x[-3]
                self.thisclass['name'] = " - ".join(x[0:-4])
            self.thisclass['department'], self.thisclass['number'] = self.thisclass['course'].split()
            self.thisclass['name'] = self.thisclass['name'].replace(",",";")
            return
        if(self.state == 4):
            self.thisclass['term'] = strip(data)
            self.state += 1
            return
        if(self.state == 6):
            self.thisclass['registration dates'] = strip(data)
            self.state += 1
            return
        if(self.state == 8):
            self.thisclass['levels'] = strip(data)
            self.state += 1
            return
        if(self.state == 10):
            self.thisclass['attributes'] = strip(data).split(', ')
            self.state += 1
            return
        if(self.state == 11):
            self.thisclass['campus'] = strip(data)
            self.state += 1
            return
        if(self.state == 9 and data=="\nMain Campus\n"): # risky quick fix for courses without attribute lists
            self.thisclass['campus'] = "Main Campus"
            self.thisclass['attributes'] = []
            self.state = 12
            return
        if(self.state == 12):
            self.thisclass['schedule type'] = strip(data)
            self.state += 1
            return
        if(self.state == 13):
            self.thisclass['instructional method'] = strip(data)
            if(strip(data)[-7:] == "Credits"): # random class is missing intstructional method line ???
                self.thisclass['instructional method'] = '???'
                try:
                    self.thisclass['credits'] = int(float(strip(data)[:-7]))
                except:
                    self.thisclass['credits'] = -1
                self.state = 15
                return
            self.state += 1
            return
        if(self.state == 14):
            try:
                self.thisclass['credits'] = int(float(strip(data)[:-7]))
            except:
                self.thisclass['credits'] = -1
            self.state += 1
            return
        if(self.state == 17):
            self.thisclass['type'] = data
            self.state += 1
            return
        if(self.state == 19):
            self.thisclass['time'] = data
            if(not data=='TBA'):
                self.thisclass['start time'], self.thisclass['end time'] = data.split(' - ')
            else:
                self.thisclass['start time'] = 'TBA'
                self.thisclass['end time'] = 'TBA'
            self.state += 1
            return
        if(self.state == 21):
            self.thisclass['days'] = data
            self.state += 1
            return
        if(self.state == 23):
            self.thisclass['location'] = data
            loc = data.split()
            self.thisclass['room number'] = loc[-1]
            if(data=='TBA'):
                self.thisclass['building'] = 'TBA'
            else:
                self.thisclass['building'] = " ".join(loc[0:-1])
            self.state += 1
            return
        if(self.state == 25):
            self.thisclass['date range'] = data
            self.thisclass['start date'], self.thisclass['end date'] = data.split(' - ')
            self.state += 1
            return
        if(self.state == 27):
            self.thisclass['schedule type'] = data
            self.state += 1
            return
        if(self.state == 29):
            self.thisclass['instructor'] = data[:-2]
            self.state = 30
            return
        #print(" "*self.depth+" "+str(len(data)))


names = ['Fall 2019','Spring 2020','Summer 2020','Fall 2020']

include = ['name','crn','department','number','section','term','credits','start time','end time','days','start date','end date','building','room number','instructor']

attrs = set()

with open('output.csv','w') as outfile:
    outfile.write(",".join(include)+'\n') #header (optional)
    for name in names:
        with open('Class Schedule Listing '+name+'.html') as file:
            content = file.read()
        parser = ScheduleHTMLParser()
        parser.feed(content)
        classes = parser.classes
        print(len(classes), "classes in", name)
        for c in classes:
            for attr in c['attributes']:
                attrs.add(attr)
            try:
                if(c['instructor'] == 'T'):
                    c['instructor'] = 'TBA'
                if(c['days'] == '\xa0'):
                    c['days'] = 'TBA'
                c['start date'] = " ".join(c['start date'].split(', '))
                c['end date'] = " ".join(c['end date'].split(', '))
                line = ",".join([str(c[i]) for i in include])
                outfile.write(line.replace("   "," ").replace("  "," ").replace(", ",",").replace(" ,",",")+'\n')
            except:
                pass

