#Script to list sychronisers on a given SRH hub

import sys
import datetime
import click
import smtplib
from get_product_details import analyse_delay, daily_report, get_delay

from dhus_odata_api import *

PUB_DELAY = 4 #hours!
SYNC_STATUS = ['RUNNING', 'PENDING', 'STOPPED'] #in order we want them appearing in the log

#todo: do we need to send a warning if a synchroniser is stopped?  Yes? - long term should be deleted....
def delay_warning(hrs):
    
    #Method to calculate what warning sent depending on values defined
    warning = None
    
    if hrs > PUB_DELAY:
        warning = f"[WARNING! LCD threshold exceeded ({PUB_DELAY} hours)]"

    return warning

@click.command()
@click.option('-c', '--hub-config', 'hub_config', type=str, required=True, help='Location of hub admin credos')
@click.option('-e', '--email', 'email', type=str, help='if supplied will email report ONLY if thresholds exceeded and not output to STDOUT. separate multiple emails with a comma "," ')
def main(hub_config, email):

    synchronisers = synchroniser_summary(get_synchronisers(hub_config))

    report = ''
    cnt = 0
    warning_flag = False
    #order report by current synchroniser status
    for status in SYNC_STATUS:

        sync_by_status = [i for i in synchronisers.keys() if synchronisers[i]['status'] == status]

        if len(sync_by_status) != 0:

            if cnt!=0:
                report += "\n"

            report += f"Synchroniser status: {status}\n"

            for sync in sync_by_status:

                lcd = synchronisers[sync]['lcd']

                hrs, mins, secs = analyse_delay(get_delay(datetime.datetime.now(), datetime.datetime.strptime(lcd, '%Y-%m-%dT%H:%M:%S.%f')))

                #check for any warning and flag up if one encountered
                warning_msg = delay_warning(hrs)

                if warning_msg:
                    warning_flag = True

                #pretty print the delay
                delay_str = daily_report(hrs, mins, secs)

                #whats the source hub
                src_hub = synchronisers[sync]['url'].replace('https://','').replace('http://','').split('.')[0]

                if warning_msg:
                    report += f"Label: {sync} (id = {synchronisers[sync]['id']}, source = {src_hub}, status = {synchronisers[sync]['status']}, publication_delay = {delay_str}, last creation date = {lcd}) {warning_msg}"

                else:
                    report += f"Label: {sync} (id = {synchronisers[sync]['id']}, source = {src_hub}, status = {synchronisers[sync]['status']}, publication_delay = {delay_str}, last creation date = {lcd})"

                report +="\n"

        cnt +=1

    report += f"\nFound {len(synchronisers.keys())} dhus for hub {hub_config} at {datetime.datetime.now()}"

    #send email if requested
    if email:

        if warning_flag:

            hub, user, pw = get_hub_creds(hub_config)
            del user, pw
            from urllib.parse import urlparse
            hubname = urlparse(hub).netloc

            if ',' in email:
                recipients = email.split(',')

            else:
                recipients = [email]

            try:
                from email.mime.text import MIMEText

                for recipient in recipients:
                    msg = MIMEText(report)
                    msg['Subject'] = f'Relay Hub ({hubname}) Publication delay Synchroniser ALERT!"'
                    msg['From'] = recipient
                    msg['To'] = recipient

                    s = smtplib.SMTP('localhost')
                    s.sendmail(msg['From'], msg['To'], msg.as_string())
                    s.quit()

                sys.exit(0)

            except Exception as ex:
                print (f"\nERROR: Could not send email to: {email}")
                sys.exit(1)

    else:
        print(report)
        sys.exit(0)

if __name__ == '__main__':
    main()
