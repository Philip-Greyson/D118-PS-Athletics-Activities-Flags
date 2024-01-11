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

print(f"DBUG: Username: {un} |Password: {pw} |Server: {cs}")  # debug so we can see where oracle is trying to connect to/with
print(f'D118 SFTP Username: {D118_SFTP_UN} | D118 SFTP Password: {D118_SFTP_PW} | D118 SFTP Server: {D118_SFTP_HOST}')  # debug so we can see what info sftp connection is using

if __name__ == '__main__':  # main file execution
    with oracledb.connect(user=un, password=pw, dsn=cs) as con:  # create the connecton to the database
        with con.cursor() as cur:  # start an entry cursor
            with open('activities_log.txt', 'w') as log:  # open the logging file
                with open('activities.txt', 'w') as output:  # open the output file
                    print("Connection established: " + con.version)
                    print("Connection established: " + con.version, file=log)
                    today = datetime.now()  # get todays date and store it for finding the correct term later
                    print("today = " + str(today))  # debug
                    print("today = " + str(today), file=log)  # debug

                    # # list of all activity names for debugging purposes on the spreadsheet, not needed in final output
                    # activityNames = ['ACTIVITIES.BOYS_BASKETBALL','ACTIVITIES.BOYS_SOCCER','ACTIVITIES.WRESTLING','ACTIVITIES.LACROSSE','ACTIVITIES.BOYS_BASEBALL','ACTIVITIES.BOYS_CROSS_COUNTRY','ACTIVITIES.BOYS_TENNIS','ACTIVITIES.BOYS_TRACK_FIELD','ACTIVITIES.CHEERLEADING','ACTIVITIES.FOOTBALL','ACTIVITIES.GIRLS_BASKETBALL','ACTIVITIES.GIRLS_BOWLING','ACTIVITIES.GIRLS_CROSS_COUNTRY','ACTIVITIES.GIRLS_GOLF','ACTIVITIES.GIRLS_SOCCER','ACTIVITIES.GIRLS_SOFTBALL','ACTIVITIES.GIRLS_TENNIS','ACTIVITIES.GIRLS_TRACK_FIELD','ACTIVITIES.GIRLS_VOLLEYBALL','ACTIVITIES.BOYS_GOLF','ACTIVITIES.POMS','ACTIVITIES.CROSS_COUNTRY','ACTIVITIES.TRACK_AND_FIELD','ACTIVITIES.VOLLEYBALL','ACTIVITIES.ESPORTS','ACTIVITIES.BOWLING','ACTIVITIES.WYSE','ACTIVITIES.ACADEMIC_TEAM','ACTIVITIES.BAND','ACTIVITIES.BEST_BUDDIES','ACTIVITIES.BOOK_CLUB','ACTIVITIES.CONCERT_BAND','ACTIVITIES.CONCERT_CHOIR','ACTIVITIES.CULINARY','ACTIVITIES.DRAMA','ACTIVITIES.FBLA','ACTIVITIES.FRENCH','ACTIVITIES.GREEN','ACTIVITIES.HEALTH_CARE_CLUB','ACTIVITIES.INTERNATIONAL','ACTIVITIES.MARCHING_BAND','ACTIVITIES.MATH_COUNTS','ACTIVITIES.MATH_TEAM','ACTIVITIES.MUSICAL','ACTIVITIES.NHS','ACTIVITIES.PEER','ACTIVITIES.PEP_BAND','ACTIVITIES.PLAY','ACTIVITIES.PROM','ACTIVITIES.SCHOLASTIC_BOWL','ACTIVITIES.SHOW_CHOIR','ACTIVITIES.SPANISH','ACTIVITIES.SPECIAL_OLYMPICS','ACTIVITIES.SPIRIT','ACTIVITIES.STUDENT_COUNCIL','ACTIVITIES.SWING_CHOIR','ACTIVITIES.POWERLIFTING','ACTIVITIES.DEBATE','ACTIVITIES.YEARBOOK','ACTIVITIES.NAHS','ACTIVITIES.VARSITY']
                    # print('STUDENTS.STUDENT_NUMBER,', end='', file=output)
                    # for i in range(len(activityNames)): #go through each element one at a time
                    #     print(activityNames[i], end='', file=output) # print the activities element without the newline at the end
                    #     if i != (len(activityNames) - 1): # if we are not on the final element
                    #         print(',', end='', file=output) # print a comma separator
                    #     else: # if we are on the final activity
                    #         print('', file=output) # print a newline

                    # do the sql query on students getting required info to get the course enrollments
                    cur.execute('SELECT student_number, dcid, id, schoolid, enroll_status, grade_level FROM students ORDER BY student_number DESC')
                    students = cur.fetchall()
                    for student in students:  # go through each student
                        try:
                            # define a huge dictionary of the course names as keys, and empty strings as the values. As the student courses are found these strings will update to a 1
                            activities = {'ATH-BOYS BASKETBALL':'','ATH-BOYS SOCCER':'','ATH-WRESTLING':'','ATH-LACROSSE':'','ATH-BOYS BASEBALL':'','ATH-BOYS CROSS COUNTRY':'','ATH-BOYS TENNIS':'','ATH-BOYS TRACK AND FIELD':'','ATH-CHEERLEADING':'','ATH-FOOTBALL':'','ATH-GIRLS BASKETBALL':'','ATH-GIRLS BOWLING':'','ATH-GIRLS CROSS-COUNTRY':'','ATH-GIRLS GOLF':'','ATH-GIRLS SOCCER':'','ATH-GIRLS SOFTBALL':'','ATH-GIRLS TENNIS':'','ATH-GIRLS TRACK AND FIELD':'','ATH-GIRLS VOLLEYBALL':'','ATH- BOYS GOLF':'','ATH-POMS':'','ATH-CROSS COUNTRY':'','ATH-TRACK TEAM':'','ATH-VOLLEYBALL':'','ATH-ESPORTS':'','ATH-BOWLING':'','ACT-ACADEMIC CHALLENGE-WYSE':'','ACT-ACADEMIC TEAM':'','ACT-BAND':'','ACT-BEST BUDDIES':'','ACT-BOOK CLUB':'','ACT-CONCERT BAND':'','ACT-CONCERT CHOIR':'','ACT-CULINARY ARTS CLUB':'','ACT-DRAMA CLUB':'','ACT-FBLA':'','ACT-FRENCH CLUB':'','ACT-GREEN CLUB':'','ACT-HEALTH CARE CLUB':'','ACT-INTERNATIONAL CLUB':'','ACT-MARCHING BAND':'','ACT-MATH COUNTS':'','ACT-MATH TEAM':'','ACT-MUSICAL':'','ACT-NATIONAL HONORS SOCIETY':'','ACT-PEER MEDIATION':'','ACT-PEP BAND':'','ACT-PLAY':'','ACT-PROM COMMITTEE':'','ACT-SCHOLASTIC BOWL':'','ACT-SHOW CHOIR':'','ACT-SPANISH CLUB':'','ACT-SPECIAL OLYMPICS':'','ACT-SPIRIT CLUB':'','ACT-STUDENT COUNCIL':'','ACT-SWING CHOIR':'','ACT-POWERLIFTING CLUB':'','ACT-DEBATE CLUB':'','ACT-YEARBOOK':'','ACT-NATIONAL ART HONOR SOCIETY':'','ACT-VARSITY CLUB':''}
                            idNum = str(int(student[0]))  # the student number usually referred to as their "id number"
                            stuDCID = str(student[1])  # the student dcid
                            internalID = int(student[2])  # get the internal id of the student that is referenced in the classes entries
                            status = str(student[4])  # enrollment status, 0 for active
                            schoolID = str(student[3])  # schoolcode
                            if status == '0':  # only active students will get processed, otherwise just blanked out
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
                                            print("Found good term for student " + str(idNum) + ": " + termid + " | " + termDCID, file=log)
                                            cur.execute("SELECT cc.schoolid, cc.course_number, cc.sectionid, cc.section_number, cc.expression, courses.course_name FROM cc LEFT JOIN courses ON cc.course_number = courses.course_number WHERE (instr(courses.course_name, 'ATH-') > 0 OR instr(courses.course_name, 'ACT-') > 0)AND cc.studentid = " + str(internalID) + " AND cc.termid = " + termid + " ORDER BY cc.course_number")
                                            userClasses = cur.fetchall()
                                            for entry in userClasses:  # go through each class that has the ath- or act- in the name
                                                # print(entry)
                                                className = entry[5]
                                                if className in activities:  # if the class has a matching activity flag
                                                    print(entry, file=log)
                                                    activities.update({className: '1'})  # update the students activities dictionary with a 1 as the value for the class name key
                                                else:  # if we dont have a matching activity flag for the class we dont want to do an update on the dictionary or it will add it to the end and throw off the import
                                                    print("ERROR: Found class with no matching activity flag defined: " + str(entry), file=log)

                                except Exception as er:
                                    print('Error getting courses on ' + str(idNum) + ': ' + str(er))

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
                            print('Error on ' + str(student[0]) + ': ' + str(er))
                print('')
                #after all the output file is done writing and now closed, open an sftp connection to the server and place the file on there
                with pysftp.Connection(D118_SFTP_HOST, username=D118_SFTP_UN, password=D118_SFTP_PW, cnopts=CNOPTS) as sftp:
                    print('SFTP connection established')
                    print('SFTP connection established', file=log)
                    # print(sftp.pwd)  # debug to show current directory
                    # print(sftp.listdir())  # debug to show files and directories in our location
                    sftp.chdir('/sftp/studentActivities/')
                    # print(sftp.pwd) # debug to show current directory
                    # print(sftp.listdir())  # debug to show files and directories in our location
                    sftp.put('activities.txt')  # upload the file onto the sftp server
                    print("Schedule file placed on remote server for " + str(today))
                    print("Schedule file placed on remote server for " + str(today), file=log)
