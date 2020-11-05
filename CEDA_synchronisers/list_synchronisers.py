#Script to list sychronisers on a given SRH hub

import os, sys
import datetime
import click
import smtplib
from get_product_details import analyse_delay, daily_report
from synchroniser import *

PUB_DELAY = 4 #hours!
WARN_DELAY = 2 #hours  Setup warning if this exceeded
SYNC_STATUS = ['RUNNING', 'PENDING', 'STOPPED'] #in order we want them appearing in the log

#todo: do we need to send a warning if a synchroniser is stopped?  Yes? - long term should be deleted....
def delay_warning(days, hrs, mins, secs):
    #Method to calculate what warning sent depending on values defined
    warning = None
    if days > 1 or hrs > PUB_DELAY:
        warning = f"[WARNING! Publication delay {PUB_DELAY} hrs EXCEEDED!]"

    elif hrs < PUB_DELAY and hrs > WARN_DELAY:
        warning = f"[WARNING! Warning threshold exceeded {WARN_DELAY} (Publication delay {PUB_DELAY} hrs NOT exceeded!)]"

    return warning

@click.command()
@click.option('-c', '--hub-config', 'hub_config', type=str, required=True, help='Location of hub admin credos')
@click.option('-e', '--list', 'email', type=str, help='List of UIDs to submit to hub to extract publication delay info on')
def main(hub_config, email):
    try:
        #Synchronizers
        synchronisers = synchroniser_summary(get_synchronisers(hub_config))

    except Exception as ex:
        print (f"Could not list synchronisers for hub: {hub_config} ({ex})")
        sys.exit()

    report = ''
    cnt = 0
    #order report by current synchroniser status
    for status in SYNC_STATUS:

        sync_by_status = [i for i in synchronisers.keys() if synchronisers[i]['status'] == status]

        if len(sync_by_status) != 0:

            if cnt!=0:
                report += "\n"

            report += f"Synchroniser status: {status}\n"

            for sync in sync_by_status:

                lcd = synchronisers[sync]['lcd']

                days, hrs, mins, secs = analyse_delay(datetime.datetime.now() - datetime.datetime.strptime(lcd, '%Y-%m-%dT%H:%M:%S.%f'))

                #check for any warning
                warning_msg = delay_warning( days, hrs, mins, secs)

                #pretty print the delay
                delay_str = daily_report(days, hrs, mins, secs)

                if warning_msg:
                    report += f"Label: {sync} (id = {synchronisers[sync]['id']}, status = {synchronisers[sync]['status']}, publication_delay = {delay_str}, last creation date = {lcd}) {warning_msg}"

                else:
                    report += f"Label: {sync} (id = {synchronisers[sync]['id']}, status = {synchronisers[sync]['status']}, publication_delay = {delay_str}, last creation date = {lcd})"

                report +="\n"

        cnt +=1

    report += f"\nFound {len(synchronisers.keys())} synchronisers for hub {hub_config} at {datetime.datetime.now()}"

    print (report)

    #send email if requested
    if email and warning_msg:
        try:
            from email.mime.text import MIMEText
            msg = MIMEText(report)
            msg['Subject'] = 'Relay Hub Publication delay Synchroniser ALERT!"'
            msg['From'] = email
            msg['To'] = email

            s = smtplib.SMTP('localhost')
            s.sendmail(email, email, report)
            s.quit()

        except Exception as ex:
            print (f"\nERROR: Could not send email: {ex}")


if __name__ == '__main__':
    main()
