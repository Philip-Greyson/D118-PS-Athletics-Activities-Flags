
# D118-PS-Athletics-Activities-Flags

Finds students that are enrolled in our athletic and activities courses in PowerSchool, and generates a comma delimited .txt file that lists all activities they are enrolled, which is then uploaded via SFTP to a local server to be imported via AutoComm to the Activities table.

## Overview

The script first does a query for all students in PowerSchool. For each student, a dictionary is constructed with all the activity course names and blanks as their values (which nullifies the flag in PowerSchool when uploaded).
If the student is active, we find the current active terms for them based on today's date and their building, then search for any currently enrolled sections whose course names contain "ACT-" or "ATH-".
If any are found that match one of the defined activities names, the value in the dictionary for that activity is changed to a 1.
Then the list of activities is output to a comma delimited .txt file with the student's student number as the first column. Any students who are inactive have a full row of blanks.
Once all students are processed, the .txt file is uploaded to a local SFTP server where it is then imported into PowerSchool via AutoComm. The AutoComm setup takes the values and puts them into fields in the Activities table which correlate to the activities and athletics offered at each building, and can be used for things such as custom alerts, easier search/filtering of sports across buildings, etc.

## Requirements

The following Environment Variables must be set on the machine running the script:

- POWERSCHOOL_READ_USER
- POWERSCHOOL_DB_PASSWORD
- POWERSCHOOL_PROD_DB
- D118_SFTP_USERNAME
- D118_SFTP_PASSWORD
- D118_SFTP_ADDRESS

These are fairly self explanatory, and just relate to the usernames, passwords, and host IP/URLs for PowerSchool and the local SFTP server. If you wish to directly edit the script and include these credentials, you can.

Additionally, the following Python libraries must be installed on the host machine (links to the installation guide):

- [Python-oracledb](https://python-oracledb.readthedocs.io/en/latest/user_guide/installation.html)
- [pysftp](https://pypi.org/project/pysftp/)

*As part of the pysftp connection to the output SFTP server, you must include the server host key in a file** with no extension named "known_hosts" in the same directory as the Python script. You can see [here](https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html#pysftp-cnopts) for details on how it is used, but the easiest way to include this I have found is to create an SSH connection from a linux machine using the login info and then find the key (the newest entry should be on the bottom) in ~/.ssh/known_hosts and copy and paste that into a new file named "known_hosts" in the script directory.

You will also need a SFTP server running and accessible that is able to have files written to it in the directory /sftp/studentActivities/ or you will need to customize the script (see below). That setup is a bit out of the scope of this readme.
In order to import the information into PowerSchool, a scheduled AutoComm job should be setup, that uses the managed connection to your SFTP server, and imports into student_number, and whichever Activity fields you need based on the data, using comma as a field delimiter, LF as the record delimiter with the UTF-8 character set. It is important to note that the order of the AutoComm fields must match the order of the course names as defined in the `ACTIVITIES_LIST` near the top of the script.
For instance, if the first course name in the `ACTIVITIES_LIST` is football, the first entry after student_number in the AutoComm should be Activities.football (or whatever your football field is in the Activities table)

## Customization

This script is pretty customized to our school district as it uses searches for specific course names which correlate to our activity and athletics. It will require a bit of coding to change this to work with your specific district, but some things you will likely want to change are listed below:

- `ACTIVITIES_LIST` is a list of the course names that are specifically searched for, and must correlate to courses in PowerSchool with the same name (case sensitive). These need to be entered in the same order that correlates to the order in the AutoComm import for their field in the Activities table.
  - Additionally, the script only does one SQL query for their classes to save time, and assumes that the activities and athletics courses contain the strings "ACT-" or "ATH-". If this is not the case, you will need to change the query that searches for courses are replace `WHERE (instr(courses.course_name, 'ATH-') > 0 OR instr(courses.course_name, 'ACT-') > 0)` with either relevant strings for your courses, or re-work it to search for each activities name from ACTIVITIES_LIST one at a time using a loop. When there are a lot of activities, these repeated SQL queries can start taking a bit of time, which is why I opted to do it the way I did.
- `OUTPUT_FILE_NAME` and `OUTPUT_FILE_DIRECTORY`define the file name and directory on the SFTP server that the file will be exported to. These combined will make up the path for the AutoComm import.
