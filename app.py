import pandas as pd
import numpy as np
from flask import Flask, request, render_template, redirect, url_for, session, flash
import mysql.connector
import warnings
import  re
from datetime import date
import datetime
from datetime import timedelta, date
from utils import *
import smtplib
from email.message import Message
from email.mime.text import MIMEText
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)
app.secret_key = 'your secret key'

#database connection
mydb = mysql.connector.connect(
  host="sql6.freesqldatabase.com",
  port=3306,
  user="sql6688430",
  password="1uxLN2gtkY",
  database='sql6688430'
)
print(mydb)
mycursor = mydb.cursor()

#create table function:
# create_tables(mycursor)

mycursor = mydb.cursor(dictionary=True)

#flask code
@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'pass' in request.form:
        username = request.form['username']
        password = request.form['pass']
        sql="SELECT * FROM Patient_Master WHERE username = %s AND password = %s"
        mycursor.execute(sql,(username, password, ))
        userdata = mycursor.fetchone()
        if userdata:
            session['loggedin'] = True
            session['p_id'] = userdata['p_id']
            session['username'] = userdata['username']
            msg = session['username']
            return redirect(url_for('index'))
            return render_template('index.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
        
    return render_template('signin.html', msg = msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('p_id', None)
    session.pop('username', None)
    return redirect(url_for('signin'))


@app.route('/signup')
def signup():
    return redirect(url_for('register'))


@app.route('/signin')
def signin():
    return redirect(url_for('login'))


@app.route('/index', methods =['GET'])
def index(): 
    if 'username' not in session.keys():
        return redirect(url_for('login'))
    else:
        msg = session['username']
        return render_template('index.html',msg = msg)


@app.route('/bookappointmentpage', methods =['GET', 'POST'])
def bookappointmentpage():
    if 'username' not in session.keys():
        return redirect(url_for('login'))
    else:
        msg = session['username']
        mindate,maxdate = minmaxdate()
        #sql query
        sql="SELECT * FROM Time_Master"
        mycursor.execute(sql,)
        timedb = mycursor.fetchall()
        return render_template('bookappointment.html',msg = msg,mindate=mindate,maxdate=maxdate,timedb=timedb)


@app.route('/appointmentbooking', methods =['POST'])
def appointmentbooking():

    if 'username' not in session.keys():
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            a_date = request.form['appodate']
            sql="Select unavail_date FROM Dr_Unavailability WHERE unavail_date = %s"
            mycursor.execute(sql,(a_date,))
            unavaildatabase = mycursor.fetchall()
            mindate,maxdate = minmaxdate()
            msg = session['username']
            #sql query
            sql="SELECT * FROM Time_Master"
            mycursor.execute(sql,)
            timedb = mycursor.fetchall()
            if len(unavaildatabase) == 0:
                patient_id = session['p_id']
                fullname = request.form['fullname']
                age = request.form['age']
                gender = request.form['gender']
                mobileno = request.form['mobno']
                a_date = request.form['appodate']
                a_time = request.form['timing']
                a_status='active'
                sql="INSERT INTO Booked_Appointment VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)"
                mycursor.execute(sql, (patient_id, fullname, age, gender, mobileno, a_date, a_time, a_status,))
                mydb.commit()
                successmsg = "Appointment Booked Successfully"
                sql="SELECT emailid FROM Patient_Master WHERE p_id = %s"
                mycursor.execute(sql,(patient_id,))
                ab_database = mycursor.fetchone()
                ab_databaselist = ab_database.values()
                for i in list(ab_databaselist):
                    emailid = i
                    subject = "Appointment Booking"
                    textmsg = "Your Appointment Booked Successfully on Date: {} & Timing: {}".format(a_date,a_time)
                    send_email(textmsg,subject,emailid)
            else:
                successmsg = "Doctor Not Available (Select Another Day)"

            return render_template('bookappointment.html',msg = msg, successmsg = successmsg,mindate=mindate,maxdate=maxdate,timedb=timedb)


@app.route('/viewappointment', methods =['GET'])
def viewappointment(): 
    if 'username' not in session.keys():
        return redirect(url_for('login'))
    else:
        msg = session['username']
        patient_id = session['p_id']
        #sql query
        sql="SELECT booked_appointment.a_id,booked_appointment.p_id,booked_appointment.fullname,booked_appointment.age,booked_appointment.gender,booked_appointment.mobileno,booked_appointment.a_date,Booked_Appointment.a_time,doctor_prescription.dp_id FROM Booked_Appointment LEFT JOIN doctor_prescription ON doctor_prescription.a_id=booked_appointment.a_id WHERE booked_appointment.p_id = %s ORDER BY booked_appointment.a_id DESC"
        mycursor.execute(sql, (patient_id,))
        appointmentdata = mycursor.fetchall()

        return render_template('viewappointment.html',msg = msg, appointmentlist=appointmentdata)


@app.route('/statusupdate', methods=['POST'])
def statusupdate():
    if 'username' not in session.keys():
        return redirect(url_for('login'))
    else:
        msg = session['username']
        patient_id = session['p_id']
        if 'aId' in request.form:
            a_ID = request.form['aId']
            sql="DELETE FROM Booked_Appointment WHERE a_id = %s "
            mycursor.execute(sql, (a_ID,))
            mydb.commit()

        #sql query
        sql="SELECT * FROM Booked_Appointment WHERE p_id = %s ORDER BY a_id DESC"
        mycursor.execute(sql, (patient_id,))
        appointmentdata = mycursor.fetchall()
        return redirect(url_for('viewappointment'))
        return render_template('viewappointment.html',msg = msg, appointmentlist=appointmentdata)


@app.route('/viewprescription', methods=['POST'])
def viewprescription():
    if 'username' not in session.keys():
        return redirect(url_for('login'))
    else:
        msg = session['username']
        patient_id = session['p_id']
        if 'aId' in request.form:
            a_ID = request.form['aId']
            #sql query
            sql="SELECT Booked_Appointment.a_id,Booked_Appointment.p_id,Doctor_Prescription.dp_id,Booked_Appointment.fullname,Booked_Appointment.age,Booked_Appointment.gender,Doctor_Prescription.prescription,symptoms FROM Booked_Appointment LEFT JOIN Doctor_Prescription ON Booked_Appointment.a_id = Doctor_Prescription.a_id WHERE Doctor_Prescription.a_id = %s "
            mycursor.execute(sql, (a_ID,))
            viewpresc = mycursor.fetchone()
            if viewpresc is not None:
                successmssg="Check Your Prescription"
            else:
                successmssg="Your Prescription is Not Available"
        
        return render_template('viewprescription.html', msg = msg, viewpresc=viewpresc,successmssg=successmssg)


@app.route('/feedbackpage', methods =['GET'])
def feedbackpage(): 
    if 'username' not in session.keys():
        return redirect(url_for('login'))
    else:
        msg = session['username']
        return render_template('feedback.html',msg = msg)


@app.route('/feedbackform', methods =['POST'])
def feedbackform():
    if 'username' not in session.keys():
        return redirect(url_for('login'))
    else:
        msg = session['username']
        patient_id = session['p_id']
        if 'Message' in request.form:
            feedbackmssg = request.form['Message']
            if feedbackmssg is not None:
                todaydate = str(date.today())
                sql="INSERT INTO Feedback_m VALUES (NULL, %s, %s,%s)"
                mycursor.execute(sql, (patient_id, feedbackmssg,todaydate, ))
                mydb.commit()
                feedbackmsg="Feedback Recieved Successfully"
            else:
                feedbackmsg="Feedback Not Recieved Successfully"

        return render_template('feedback.html',msg = msg,feedbackmsg=feedbackmsg)


@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'pass' in request.form and 'emailid' in request.form and 'fullname' in request.form and 'mobileno' in request.form :
        username = request.form['username']
        password = request.form['pass']
        emailid = request.form['emailid']
        fullname = request.form['fullname']
        mobileno = request.form['mobileno']
        mycursor = mydb.cursor(dictionary=True)
        sql="SELECT * FROM Patient_Master WHERE username = %s"
        mycursor.execute(sql, (username, ))
        userdata = mycursor.fetchone()
        if userdata:
            msg = 'User already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', emailid):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not emailid or not fullname or not mobileno:
            msg = 'Please fill out the details properly !'
        else:
            sql="INSERT INTO Patient_Master VALUES (NULL, %s, %s, %s, %s, %s)"
            mycursor.execute(sql, (username, fullname, mobileno, emailid, password, ))
            mydb.commit()
            msg = 'You have successfully registered !'

    elif request.method == 'POST':
        msg = 'Please fill out the details !'
    return render_template('signup.html', msg = msg)


#adminpart
@app.route('/admin')
@app.route('/adminlogin', methods =['GET', 'POST'])
def adminlogin():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'pass' in request.form:
        username = request.form['username']
        password = request.form['pass']
        sql="SELECT * FROM Admin_Master WHERE username = %s AND password = %s"
        mycursor.execute(sql,(username, password, ))
        admindata = mycursor.fetchone()
        if admindata:
            session['loggedin'] = True
            session['admin_id'] = admindata['admin_id']
            session['username'] = 'Admin(Doctor)'
            cntlist = countfunc(mycursor)
            
            return redirect(url_for('dashboard'))
            return render_template('adminindex.html', msg = msg,cntlist=cntlist)
        else:
            msg = 'Incorrect username / password !'
    return render_template('admin/adminlogin.html', msg = msg)


@app.route('/adminlogout')
def adminlogout():
    session.pop('loggedin', None)
    session.pop('admin_id', None)
    session.pop('username', None)
    return redirect(url_for('adminlogin'))


@app.route('/dashboard', methods =['GET', 'POST'])
def dashboard(): 
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else:
        msg = session['username']
        cntlist = countfunc(mycursor)
        return render_template('admin/adminindex.html',msg = msg, cntlist = cntlist)


@app.route('/exploreusers', methods =['GET'])
def exploreusers():
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else:
        msg = session['username']
        sql="SELECT * FROM `patient_master` ORDER BY p_id ASC"
        mycursor.execute(sql,)
        userdatabase = mycursor.fetchall()

        return render_template('admin/exploreusers.html',msg = msg, userdatabase=userdatabase)


@app.route('/addprescriptionpage', methods =['POST'])
def addprescriptionpage():
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else:
        msg = session['username']
        if request.method == 'POST' and 'aId' in request.form:
            aId = request.form['aId']
            sql="SELECT * FROM Booked_Appointment WHERE a_id = %s"
            mycursor.execute(sql,(aId,))
            appointmentrecord = mycursor.fetchone()

        return render_template('admin/addprescription.html',msg = msg,appointmentrecord=appointmentrecord)


@app.route('/addprescription', methods =['POST'])
def addprescription(): 
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else:
        msg = session['username']
        if request.method == 'POST' and 'a_Id' in request.form and 'p_Id' in request.form and 'inputpresc' in request.form and 'symptoms' in request.form:
            a_Id = request.form['a_Id']
            p_Id = request.form['p_Id']
            inputpresc = request.form['inputpresc']
            inputsymptoms = request.form['symptoms']
            sql="INSERT INTO Doctor_Prescription VALUES (NULL, %s, %s, %s, %s)"
            mycursor.execute(sql, (a_Id, p_Id, inputsymptoms,inputpresc, ))
            mydb.commit()
            successmssg = 'Prescription Added Successfully'
        
        elif request.method == 'POST':
            successmssg = 'Prescription Not Added Successfully'

        return redirect(url_for('exploreprescription', msg=msg))


@app.route('/exploreappointment', methods =['GET'])
def exploreappointment():
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else: 
        msg = session['username']
        todaydate = str(date.today())
        sql=sql="SELECT Booked_Appointment.a_id,Booked_Appointment.p_id,dp_id,fullname,age,gender,mobileno,a_date,a_time,Doctor_Prescription.prescription,Time_Master.t_id FROM Booked_Appointment LEFT JOIN Doctor_Prescription ON Booked_Appointment.a_id = Doctor_Prescription.a_id LEFT JOIN Time_Master ON Time_Master.Timing = Booked_Appointment.a_time WHERE Doctor_Prescription.prescription IS NULL AND a_date= %s ORDER BY Time_Master.t_id ASC"
        mycursor.execute(sql,(todaydate,))
        appointmentdatabase = mycursor.fetchall()

        return render_template('admin/exploreappointments.html',msg = msg, appointmentdatabase=appointmentdatabase)


@app.route('/exploreprescription', methods =['GET'])
def exploreprescription():
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else:
        msg = session['username']
        sql="SELECT dp_id,fullname,age,symptoms,prescription,a_date FROM Doctor_Prescription LEFT JOIN booked_appointment ON Booked_Appointment.a_id = Doctor_Prescription.a_id ORDER BY a_date DESC"
        mycursor.execute(sql,)
        prescriptiondatabase = mycursor.fetchall()

        return render_template('admin/exploreprescription.html',msg = msg, prescriptiondatabase=prescriptiondatabase)


@app.route('/explorefeedback', methods =['GET'])
def explorefeedback():
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else:
        msg = session['username']
        sql="SELECT patient_master.fullname,f_date,feedback_message FROM Feedback_m LEFT JOIN patient_master ON patient_master.p_id = feedback_m.p_id ORDER BY f_date DESC"
        mycursor.execute(sql,)
        feedbackdatabase = mycursor.fetchall()

        return render_template('admin/explorefeedback.html',msg = msg, feedbackdatabase=feedbackdatabase)


@app.route('/drunavailability', methods =['GET'])
def drunavailability():
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else:
        msg = session['username']
        mindate,maxdate = minmaxdate()
        return render_template('admin/adddrunavailability.html',msg = msg, mindate=mindate, maxdate=maxdate)



@app.route('/addunavailability', methods =['POST'])
def addunavailability():
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else:
        msg = session['username']
        mindate,maxdate = minmaxdate()
        if request.method == 'POST' and 'appodate' in request.form:
            unavail_date = request.form['appodate']
            sql="Select unavail_date FROM Dr_Unavailability WHERE unavail_date = %s"
            mycursor.execute(sql,(unavail_date,))
            unavaildatabase = mycursor.fetchall()
            if len(unavaildatabase) == 0:
                sql="INSERT INTO Dr_Unavailability VALUES (NULL, %s)"
                mycursor.execute(sql, (unavail_date,))
                mydb.commit()
                successmssg = "Record Saved Successfully"
            else:
                successmssg = "Record Already Exist!"

        return render_template('admin/adddrunavailability.html',msg = msg, mindate=mindate, maxdate=maxdate, successmssg=successmssg)


@app.route('/sendreminder', methods =['POST'])
def sendreminder():
    if 'username' not in session.keys():
        return redirect(url_for('adminlogin'))
    else:
        msg = session['username']
        mindate = str(date.today())
        maxdate = str(date.today() + timedelta(days=1))
        sql="Select email_date FROM Email_Reminder WHERE email_date = %s"
        mycursor.execute(sql,(maxdate,))
        email_datedatabase = mycursor.fetchall()

        if len(email_datedatabase) == 0:
            sql="Select emailid,a_date,a_time FROM Booked_Appointment LEFT JOIN patient_master ON patient_master.p_id = booked_appointment.p_id WHERE a_date = %s"
            mycursor.execute(sql,(maxdate,))
            ar_database = mycursor.fetchall()
            for item in ar_database:
                emailid = item['emailid']
                a_date = item['a_date']
                a_time = item['a_time']
                subject = "Appointment Reminder Alert"
                textmsg = "You have Appointment Tomorrow on Date: {} & Timing: {}".format(a_date,a_time)
                send_email(textmsg,subject,emailid)
            sql="INSERT INTO Email_Reminder VALUES (NULL, %s)"
            mycursor.execute(sql, (maxdate,))
            mydb.commit()
            successmssg = "Mailed Send Successfully"
            flash(successmssg)

        else:
            successmssg = "Mailed Already Send"

        return redirect(url_for('dashboard'))



if __name__ == '__main__':
    # Run the application
    app.run(debug=False)




