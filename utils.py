import pandas as pd
import numpy as np
import mysql.connector
import warnings
import  re
from datetime import date
import datetime
from datetime import timedelta, date
import smtplib
from email.message import Message
from email.mime.text import MIMEText
warnings.filterwarnings("ignore", category=UserWarning)

def create_tables(mycursor):
    #CREATE TABLES USING BELOW QUERY! (uncomment below line to create table in mysql)
    #--DELETE ALL RECORD FROM TABLE
    #mycursor.execute("truncate Patient_Master")   #uncomment this line to remove all record from database

    mycursor.execute("CREATE TABLE IF NOT EXISTS Patient_Master (p_id int(11) NOT NULL AUTO_INCREMENT, username VARCHAR(50), fullname VARCHAR(255), mobileno VARCHAR(50), emailid VARCHAR(255), password VARCHAR(100), PRIMARY KEY (p_id))")
    mycursor.execute("CREATE TABLE IF NOT EXISTS Booked_Appointment (a_id int(11) NOT NULL AUTO_INCREMENT, p_id int(11), fullname VARCHAR(255), age int, gender VARCHAR(50), mobileno VARCHAR(15), a_date VARCHAR(25), a_time VARCHAR(100), a_status VARCHAR(100), PRIMARY KEY (a_id))")
    mycursor.execute("CREATE TABLE IF NOT EXISTS Doctor_Prescription (dp_id int(11) NOT NULL AUTO_INCREMENT, a_id int(11),  p_id int(11), symptoms VARCHAR(100), prescription LONGTEXT, PRIMARY KEY (dp_id))")
    mycursor.execute("CREATE TABLE IF NOT EXISTS Feedback_m (fb_id int(11) NOT NULL AUTO_INCREMENT,  p_id int(11), feedback_message LONGTEXT, f_date VARCHAR(25), PRIMARY KEY (fb_id))")
    mycursor.execute("CREATE TABLE IF NOT EXISTS Admin_Master (admin_id int(11) NOT NULL AUTO_INCREMENT,  username VARCHAR(50), password VARCHAR(100), PRIMARY KEY (admin_id))")
    mycursor.execute("CREATE TABLE IF NOT EXISTS Time_Master (t_id int(11) NOT NULL AUTO_INCREMENT,  Timing VARCHAR(255), PRIMARY KEY (t_id))")
    mycursor.execute("CREATE TABLE IF NOT EXISTS Dr_Unavailability (uav_id int(11) NOT NULL AUTO_INCREMENT,  unavail_date VARCHAR(25), PRIMARY KEY (uav_id))")
    mycursor.execute("CREATE TABLE IF NOT EXISTS Email_Reminder (er_id int(11) NOT NULL AUTO_INCREMENT,  email_date VARCHAR(25), PRIMARY KEY (er_id))")


def minmaxdate():
    mindate = str(date.today())
    maxdate = date.today() + timedelta(days=7)
    maxdate = str(maxdate)
    return mindate,maxdate


def countfunc(mycursor):
    sql="SELECT COUNT(*) AS 'COUNT' FROM Patient_Master"
    mycursor.execute(sql,)
    p_count = mycursor.fetchone()
    today = str(date.today())
    sql="SELECT COUNT(*) AS 'COUNT' FROM Booked_Appointment WHERE a_date = %s"
    mycursor.execute(sql,(today,))
    tap_count = mycursor.fetchone()
    sql="SELECT COUNT(*) AS 'COUNT' FROM Booked_Appointment LEFT JOIN Doctor_Prescription ON Booked_Appointment.a_id = Doctor_Prescription.a_id WHERE Doctor_Prescription.prescription IS NULL"
    mycursor.execute(sql,)
    ap_count = mycursor.fetchone()
    sql="SELECT COUNT(*) AS 'COUNT' FROM Feedback_m"
    mycursor.execute(sql,)
    fd_count = mycursor.fetchone()

    return [p_count['COUNT'],tap_count['COUNT'],ap_count['COUNT'],fd_count['COUNT']]


def send_email(textmsg,subject,emailid):
    sender = "projectmailnew2122@gmail.com"
    username = "projectmailnew2122@gmail.com"
    password = "nkqfgqnqbezrgmrn"
    msg = MIMEText(str(textmsg))
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = emailid
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.starttls()
    server.login(username, password)
    server.sendmail(sender, emailid, msg.as_string())
    server.quit()
    print("mail send successfully")



