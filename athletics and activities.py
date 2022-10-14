# See the following for table information
# https://docs.powerschool.com/PSDD/powerschool-tables/cc-4-ver3-6-1
# https://docs.powerschool.com/PSDD/powerschool-tables/terms-13-ver3-6-1


# importing module
import oracledb # needed for connection to PowerSchool (oracle database)
import sys # needed for non scrolling text output
import datetime # needed to get current date to check what term we are in
import os # needed to get environment variables
import pysftp # needed for sftp file upload
from datetime import *

# set up database connection info
un = 'PSNavigator' #PSNavigator is read only, PS is read/write
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD') #the password for the PSNavigator account
cs = os.environ.get('POWERSCHOOL_PROD_DB') #the IP address, port, and database name to connect to

# set up sftp login info
sftpUN = os.environ.get('D118_SFTP_USERNAME')
sftpPW = os.environ.get('D118_SFTP_PASSWORD')
sftpHOST = os.environ.get('D118_SFTP_ADDRESS')
cnopts = pysftp.CnOpts(knownhosts='known_hosts') # connection options to use the known_hosts file for key validation

print("Username: " + str(un) + " |Password: " + str(pw) + " |Server: " + str(cs)) #debug so we can see where oracle is trying to connect to/with
print("SFTP Username: " + str(sftpUN) + " |SFTP Password: " + str(sftpPW) + " |SFTP Server: " + str(sftpHOST)) #debug so we can see what credentials are being used

# create the connecton to the database
with oracledb.connect(user=un, password=pw, dsn=cs) as con:
    with con.cursor() as cur:  # start an entry cursor
        with open('activities_log.txt', 'w') as outputLog:  # open the logging file
            with open('activities.txt', 'w') as output: # open the output file
                print("Connection established: " + con.version)
                print("Connection established: " + con.version, file=outputLog)
                today = datetime.now() #get todays date and store it for finding the correct term later
                print("today = " + str(today))  # debug
                print("today = " + str(today), file=outputLog)  # debug
                
                # fieldnames = []

                # cur.execute('SELECT * FROM activities')
                # for column in cur.description:
                #     print(column)
                #     fieldnames.append(column[0])
                # activityRows = cur.fetchall()
                # for student in activityRows:
                #     activities = []
                #     for i, field in enumerate(student):
                #         if field:
                #             activities.append(str(fieldnames[i]) + ': ' + str(field))
                #             # print(str(fieldnames[i]) + ': ' + str(field))
                #     if (len(activities) > 5):
                #         print(activities)
                cur.execute('SELECT student_number, dcid, id, schoolid, enroll_status, grade_level FROM students ORDER BY student_number DESC')
                rows = cur.fetchall()
                for count, student in enumerate(rows):
                    try:
                        # sys.stdout.write('\rProccessing student entry %i' % count) # sort of fancy text to display progress of how many students are being processed without making newlines
                        # sys.stdout.flush()
                        idNum = str(int(student[0]))
                        stuDCID = str(student[1])
                        internalID = int(student[2]) #get the internal id of the student that is referenced in the classes entries
                        status = str(student[4])
                        schoolID = str(student[3])
                        if status == '0': # only active students will get processed, otherwise just blanked out
                            #do another query to get their classes, filter to just the current year and only course numbers that contain SH
                            try:
                                cur.execute("SELECT id, firstday, lastday, schoolid, dcid FROM terms WHERE schoolid = " + schoolID + " ORDER BY dcid DESC")  # get a list of terms for the school, filtering to not full years
                                terms = cur.fetchall()
                                for termEntry in terms:  # go through every term result
                                    #compare todays date to the start and end dates with 2 days before start so it populates before the first day of the term
                                    if ((termEntry[1] - timedelta(days=2) < today) and (termEntry[2] + timedelta(days=1) > today)):
                                        termid = str(termEntry[0])
                                        termDCID = str(termEntry[4])
                                        # print("Found good term for student " + str(idNum) + ": " + termid + " | " + termDCID)
                                        print("Found good term for student " + str(idNum) + ": " + termid + " | " + termDCID, file=outputLog)
                                        cur.execute("SELECT cc.schoolid, cc.course_number, cc.sectionid, cc.section_number, cc.expression, courses.course_name FROM cc LEFT JOIN courses ON cc.course_number = courses.course_number WHERE (instr(courses.course_name, 'ATH-') > 0 OR instr(courses.course_name, 'ACT-') > 0)AND cc.studentid = " + str(internalID) + " AND cc.termid = " + termid + " ORDER BY cc.course_number")
                                        userClasses = cur.fetchall()
                                        for entry in userClasses:
                                            print(entry)
                            except Exception as er:
                                print('Error getting courses on ' + str(idNum) + ': ' + str(er))
                        else: # they are not active
                            print(idNum + ',,,,,,,,,', file=output) # output all blanks as they are not in any activities
                    except Exception as er:
                        print('Error on ' + str(student[0]) + ': ' + str(er))