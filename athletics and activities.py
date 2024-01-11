"""Script to generate a .txt file containing student activities flags based on related course enrollment.

https://github.com/Philip-Greyson/D118-PS-Athletics-Activities-Flags

Finds all students in PS, then searches for the activities and athletics courses for each student.
If they are enrolled in a class, that activity is marked as a 1. Their activities are exported to a .txt file with one student per line.
That file is then uploaded via SFTP to a local server for AutoComm import into PS later.

Needs pysftp: pip install pysftp --upgrade
Needs oracledb: pip install oracledb --upgrade

See the following for table information
https://docs.powerschool.com/PSDD/powerschool-tables/cc-4-ver3-6-1
https://docs.powerschool.com/PSDD/powerschool-tables/terms-13-ver3-6-1
"""


# importing module
import datetime  # needed to get current date to check what term we are in
import os  # needed to get environment variables
from datetime import *

import oracledb  # needed for connection to PowerSchool (oracle database)
import pysftp  # needed for sftp file upload

# set up database connection info
un = os.environ.get('POWERSCHOOL_READ_USER')  # username for read-only database user
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD')  # the password for the database account
cs = os.environ.get('POWERSCHOOL_PROD_DB')  # the IP address, port, and database name to connect to

# set up sftp login info
D118_SFTP_UN = os.environ.get('D118_SFTP_USERNAME')  # username for the d118 sftp server
D118_SFTP_PW = os.environ.get('D118_SFTP_PASSWORD')  # password for the d118 sftp server
D118_SFTP_HOST = os.environ.get('D118_SFTP_ADDRESS')  # ip address/URL for the d118 sftp server
CNOPTS = pysftp.CnOpts(knownhosts='known_hosts')  # connection options to use the known_hosts file for key validation

# define the list of activities in the order they will be exported in the resulitng file. This should match the order of the AutoComm import config
ACTIVITIES_LIST = ['ATH-BOYS BASKETBALL','ATH-BOYS SOCCER','ATH-WRESTLING','ATH-LACROSSE','ATH-BOYS BASEBALL','ATH-BOYS CROSS COUNTRY','ATH-BOYS TENNIS','ATH-BOYS TRACK AND FIELD','ATH-CHEERLEADING','ATH-FOOTBALL','ATH-GIRLS BASKETBALL','ATH-GIRLS BOWLING','ATH-GIRLS CROSS-COUNTRY','ATH-GIRLS GOLF','ATH-GIRLS SOCCER','ATH-GIRLS SOFTBALL','ATH-GIRLS TENNIS','ATH-GIRLS TRACK AND FIELD','ATH-GIRLS VOLLEYBALL','ATH- BOYS GOLF','ATH-POMS','ATH-CROSS COUNTRY','ATH-TRACK TEAM','ATH-VOLLEYBALL','ATH-ESPORTS','ATH-BOWLING','ACT-ACADEMIC CHALLENGE-WYSE','ACT-ACADEMIC TEAM','ACT-BAND','ACT-BEST BUDDIES','ACT-BOOK CLUB','ACT-CONCERT BAND','ACT-CONCERT CHOIR','ACT-CULINARY ARTS CLUB','ACT-DRAMA CLUB','ACT-FBLA','ACT-FRENCH CLUB','ACT-GREEN CLUB','ACT-HEALTH CARE CLUB','ACT-INTERNATIONAL CLUB','ACT-MARCHING BAND','ACT-MATH COUNTS','ACT-MATH TEAM','ACT-MUSICAL','ACT-NATIONAL HONORS SOCIETY','ACT-PEER MEDIATION','ACT-PEP BAND','ACT-PLAY','ACT-PROM COMMITTEE','ACT-SCHOLASTIC BOWL','ACT-SHOW CHOIR','ACT-SPANISH CLUB','ACT-SPECIAL OLYMPICS','ACT-SPIRIT CLUB','ACT-STUDENT COUNCIL','ACT-SWING CHOIR','ACT-POWERLIFTING CLUB','ACT-DEBATE CLUB','ACT-YEARBOOK','ACT-NATIONAL ART HONOR SOCIETY','ACT-VARSITY CLUB', "ACT-STRATEGISTS' CLUB", 'ACT-BASS FISHING', 'ACT-JAZZ BAND', 'ACT-TECH CREW', 'ACT-VOCAL JAZZ ENSEMBLE', 'ACT-NATIONAL JUNIOR HONOR SOCIETY', 'ACT-ART CLUB', 'ACT-NEWSPAPER CLUB', 'ACT-MULTI-CULTURAL CLUB', 'ACT-SPECIAL OLYMPICS BOWLING', 'ACT-STEM CLUB', 'ACT-SAFE', 'ACT-HOMECOMING COM', 'ACT-Book Club', 'ACT-YOUNG INVESTORS CLUB', 'ACT-AUDITORIUM EVENTS CLUB', 'ACT-ANCHORED CLUB']

OUTPUT_FILE_NAME = 'activities.txt'
OUTPUT_FILE_DIRECTORY = '/sftp/studentActivities/'

print(f"DBUG: Username: {un} |Password: {pw} |Server: {cs}")  # debug so we can see where oracle is trying to connect to/with
print(f'DBUG: D118 SFTP Username: {D118_SFTP_UN} | D118 SFTP Password: {D118_SFTP_PW} | D118 SFTP Server: {D118_SFTP_HOST}')  # debug so we can see what info sftp connection is using

if __name__ == '__main__':  # main file execution
    with open('activities_log.txt', 'w') as log:  # open the logging file
        startTime = datetime.now()
        startTime = startTime.strftime('%H:%M:%S')
        print(f'INFO: Execution started at {startTime}')
        print(f'INFO: Execution started at {startTime}', file=log)
        with oracledb.connect(user=un, password=pw, dsn=cs) as con:  # create the connecton to the database
            with con.cursor() as cur:  # start an entry cursor
                with open(OUTPUT_FILE_NAME, 'w') as output:  # open the output file
                    print(f'INFO: Connection established to PS database on version: {con.version}')
                    print(f'INFO: Connection established to PS database on version: {con.version}', file=log)
                    today = datetime.now()  # get todays date and store it for finding the correct term later
                    print(f"DBUG: today = {today}")  # debug
                    print(f"DBUG: today = {today}", file=log)  # debug

                    # do the sql query on students getting required info to get the course enrollments
                    cur.execute('SELECT student_number, dcid, id, schoolid, enroll_status, grade_level FROM students ORDER BY student_number DESC')
                    students = cur.fetchall()
                    activities = {}  # define an empty dictionary to hold the course names as keys and empty strings as values which will be replaced with a "1" if they are enrolled
                    for student in students:  # go through each student
                        try:
                            # define a huge dictionary of the course names as keys, and empty strings as the values. As the student courses are found these strings will update to a 1
                            for activity in ACTIVITIES_LIST:
                                activities.update({activity: ''})  # blank out each activity
                            idNum = str(int(student[0]))  # the student number usually referred to as their "id number"
                            stuDCID = str(student[1])  # the student dcid
                            internalID = int(student[2])  # get the internal id of the student that is referenced in the classes entries
                            status = str(student[4])  # enrollment status, 0 for active
                            schoolID = str(student[3])  # schoolcode
                            if status == '0':  # only active students will get processed further, otherwise they are left just blanked out
                                # do another query to get their classes, filter to just the current year and only course numbers that contain SH
                                try:
                                    cur.execute("SELECT id, firstday, lastday, schoolid, dcid FROM terms WHERE schoolid = :school ORDER BY dcid DESC", school = schoolID)  # get a list of terms for the school, filtering to not full years. # Use bind variables. https://python-oracledb.readthedocs.io/en/latest/user_guide/bind.html#bind
                                    terms = cur.fetchall()
                                    for termEntry in terms:  # go through every term result
                                        #compare todays date to the start and end dates with 2 days before start so it populates before the first day of the term
                                        if ((termEntry[1] - timedelta(days=2) < today) and (termEntry[2] + timedelta(days=1) > today)):
                                            termid = str(termEntry[0])
                                            termDCID = str(termEntry[4])
                                            # print(f"DBUG: Found good term for student {idNum} at building {schoolID} : {termid} | {termDCID}")  # debug
                                            # print(f"DBUG: Found good term for student {idNum} at building {schoolID} : {termid} | {termDCID}", file=log)  # debug
                                            print(f'DBUG: Starting student {idNum} at building {schoolID} in term {termid}')
                                            print(f'DBUG: Starting student {idNum} at building {schoolID} in term {termid}', file=log)
                                            # do a search for the current student in the current term for course names that contain ATH- or ACT-, the prefix for all our athletics and activities course sections
                                            cur.execute("SELECT cc.schoolid, cc.course_number, cc.sectionid, cc.section_number, cc.expression, courses.course_name FROM cc LEFT JOIN courses ON cc.course_number = courses.course_number WHERE (instr(courses.course_name, 'ATH-') > 0 OR instr(courses.course_name, 'ACT-') > 0) AND cc.studentid = :studentInternalID AND cc.termid = :term ORDER BY cc.course_number", studentInternalID = internalID, term = termid)
                                            userClasses = cur.fetchall()
                                            for entry in userClasses:  # go through each class that has the ath- or act- in the name
                                                # print(entry)
                                                className = entry[5]
                                                if className in activities:  # if the class has a matching activity flag
                                                    print(f'INFO: Student {idNum} is enrolled in {className} at building {entry[0]}')
                                                    print(f'INFO: Student {idNum} is enrolled in {className} at building {entry[0]}', file=log)
                                                    activities.update({className: '1'})  # update the students activities dictionary with a 1 as the value for the class name key
                                                else:  # if we dont have a matching activity flag for the class we dont want to do an update on the dictionary or it will add it to the end and throw off the import
                                                    print(f"ERROR: Found class with no matching activity flag defined: {entry}")
                                                    print(f"ERROR: Found class with no matching activity flag defined: {entry}", file=log)

                                except Exception as er:
                                    print(f'ERROR getting courses for {idNum}: {er}')
                                    print(f'ERROR getting courses for {idNum}: {er}', file=log)

                            # print the student's list of activities to the output file regardless of whether they were active or not
                            # print(activities, file=log)
                            # print(activities.values(), file=log)
                            # print(list(activities.values()), file=log)
                            activityFlags = list(activities.values())
                            print(idNum + ',', end='', file=output)  # print the student's ID number as the first element of the line
                            for i in range(len(activityFlags)):  # go through each element one at a time
                                print(activityFlags[i], end='', file=output)  # print the activities flag element without the newline at the end
                                if i != (len(activityFlags) - 1):  # if we are not on the final element
                                    print(',', end='', file=output)  # print a comma separator
                                else:  # if we are on the final element
                                    print('', file=output)  # print a newline
                            # print(activities)

                        except Exception as er:
                            print(f'ERROR on student {student[0]}: {er}')
                            print(f'ERROR on student {student[0]}: {er}', file=log)

                #after all the output file is done writing and now closed, open an sftp connection to the server and place the file on there
                with pysftp.Connection(D118_SFTP_HOST, username=D118_SFTP_UN, password=D118_SFTP_PW, cnopts=CNOPTS) as sftp:
                    print(f'INFO: SFTP connection established to {D118_SFTP_HOST}')
                    print(f'INFO: SFTP connection established to {D118_SFTP_HOST}', file=log)
                    # print(sftp.pwd)  # debug to show current directory
                    # print(sftp.listdir())  # debug to show files and directories in our location
                    sftp.chdir(OUTPUT_FILE_DIRECTORY)
                    # print(sftp.pwd) # debug to show current directory
                    # print(sftp.listdir())  # debug to show files and directories in our location
                    sftp.put(OUTPUT_FILE_NAME)  # upload the file onto the sftp server
                    print("Schedule file placed on remote server for " + str(today))
                    print("Schedule file placed on remote server for " + str(today), file=log)
