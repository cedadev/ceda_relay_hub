
#Script to list LCD from GSS catalogue.  All producer/consumers listed in one file
#If email set will email reciepient if PUB_DELAY exceeded.
#Otherwise this script will output key/value pairs to STDOUT.  Use hourly on cron and write to a WEEKLY file.

#Use a summary script to summarise entries for inclusion in DHR KPI report.

import os
import sys
import datetime
import click
import smtplib

import psycopg2
import configparser

from get_product_details import analyse_delay, daily_report, get_delay

PUB_DELAY = 4 #hours!

def get_config(filename):

    try:
        config = configparser.RawConfigParser()
        config.read(filename)

    except Exception as ex:
        raise Exception("Could not extract configuration from %s (%s)" % (filename, ex))

    return config

def get_hub_creds(filename):
    user = None;
    password = None
    hub = None

    if os.path.exists(filename):

        config = get_config(filename)

        try:
            hub = config.get('default', 'hub')
        except:
            hub = None

        user = config.get('default', 'user')
        password = config.get('default', 'password')

        return hub, user, password

    else:
        raise Exception("No such file: %s" % filename)

def delay_warning(hrs):
    
    #Method to calculate what warning sent depending on values defined
    warning = None
    
    if hrs >= PUB_DELAY:
        warning = f"[WARNING! LCD threshold exceeded ({PUB_DELAY} hours)]"

    return warning

def get_all_lcd(host, port, database, user, password):
    #todo get connections from config
    connection = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
    query = 'select * from ingester_configuration order by ingester_name;'

    cursor = connection.cursor()
    #cursor.execute("SELECT count(*) FROM ingested_product where status='INGESTED' and creation_date > '2026-01-07T00:00:00' and creation_date < '2026-01-07T23:59:59' and product_name like 'S3%';")
    cursor.execute(query)
    record = cursor.fetchall()

    return record

def get_psql_conf(catalogue_config):

    config = get_config(catalogue_config)

    database = config.get('default', 'DATABASE')
    user = config.get('default', 'USER')
    password = config.get('default', 'PASSWORD')
    host = config.get('default', 'HOSTNAME')
    port   = config.get('default', 'PORT')

    return database, user, password, host, port    

def email_report(email, host, content):
    '''Method to send email'''
    
    if ',' in email:
        recipients = email.split(',')

    else:
        recipients = [email]

    try:
        from email.mime.text import MIMEText

        for recipient in recipients:
            msg = MIMEText(content)
            msg['Subject'] = f'GSS Catalogue ({host}) LCD delay ALERT!"'
            msg['From'] = recipient
            msg['To'] = recipient

            s = smtplib.SMTP('localhost')
            s.sendmail(msg['From'], msg['To'], msg.as_string())
            s.quit()

        sys.exit(0)

    except Exception as ex:
        print (f"\nERROR: Could not send email to: {email}")
        sys.exit(1)


@click.command()
@click.option('-c', '--catalogue-config', 'catalogue_config', type=str, required=True, help='Connection details to GSS postgres instance')
@click.option('-e', '--email', 'email', type=str, help='if supplied will email report ONLY if thresholds exceeded and not output to STDOUT. separate multiple emails with a comma "," ')
def main(email, catalogue_config):
    
    database, user, password, host, port = get_psql_conf(catalogue_config)

    try:
        producers = get_all_lcd(database=database, user=user, password=password, host=host, port=port)

    except Exception as ex:
        print ("catalogue not available")

    report = ''
    cnt = 0
    warning_flag = False
    
    report_struct = []

    #timestamp the report
    report_struct.append(f"time {datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S')}")
    
    if len(producers) != 0:

        if cnt!=0:
            report += "\n"

        #report += f"Synchroniser status: {status}\n"

        for line_id in range(0,len(producers)):

            name = producers[line_id][0]
            lcd = producers[line_id][1]

            hrs, mins, secs = analyse_delay(get_delay(datetime.datetime.now(), lcd))

            #check for any warning and flag up if one encountered
            warning_msg = delay_warning(hrs)

            if warning_msg:
                warning_flag = True

            #pretty print the delay
            delay_str = daily_report(hrs, mins, secs)

            #datetime.datetime.strftime(report_struct['Sentinel2-producer'], '%Y-%m-%dT%H:%M:%S.%f')
            report_struct.append(f"{name} {delay_str}")

            if warning_msg:
                #report += f"Label: {sync} (id = {synchronisers[sync]['id']}, source = {src_hub}, status = {synchronisers[sync]['status']}, publication_delay = {delay_str}, last creation date = {lcd}) {warning_msg}"
                report += f"Label: {name} publication_delay = {delay_str} EXCEEDS {PUB_DELAY} threshold (last creation date = {lcd})\n"

    cnt +=1
 
    #send email if requested - remember this will only happen if warning triggered
    if email and warning_flag:
        email_report(email, host, report)        

    else:
        #print out all product streams
        print(*[f"{i}," for i in report_struct])
        

if __name__ == '__main__':
    main()