#script to query CEDA GSS catalogue db and generate an rsync list
import os
import sys
import datetime
import click
import smtplib

import psycopg2
import configparser

class MutuallyExclusiveOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        help = kwargs.get('help', '')
        if self.mutually_exclusive:
            ex_str = ', '.join(self.mutually_exclusive)
            kwargs['help'] = help + (
                ' NOTE: This argument is mutually exclusive with '
                ' arguments: [' + ex_str + '].'
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`.".format(
                    self.name,
                    ', '.join(self.mutually_exclusive)
                )
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )

def get_config(filename):

    try:
        config = configparser.RawConfigParser()
        config.read(filename)

    except Exception as ex:
        raise Exception("Could not extract configuration from %s (%s)" % (filename, ex))

    return config

def get_psql_conf(catalogue_config):

    config = get_config(catalogue_config)

    database = config.get('default', 'DATABASE')
    user = config.get('default', 'USER')
    password = config.get('default', 'PASSWORD')
    host = config.get('default', 'HOSTNAME')
    port   = config.get('default', 'PORT')

    try:
        incoming = config.get('default', 'INCOMING')
    except:
        incoming = None

    return database, user, password, host, port, incoming

def get_records_from_db(host, port, database, user, password, product, date, limit):

    #todo get connections from config
    connection = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
    
    if limit is None:
        query = f"SELECT product_name,product_id,creation_date,checksum FROM ingested_product where status='INGESTED' and product_name like '{product}' and creation_date > '{date}T00:00:00' and creation_date < '{date}T23:59:59' order by creation_date ASC;"
    
    else:
        query = f"SELECT product_name,product_id,creation_date,checksum FROM ingested_product where status='INGESTED' and product_name like '{product}' and creation_date > '{date}T00:00:00' and creation_date < '{date}T23:59:59' order by creation_date ASC limit {limit};"

    cursor = connection.cursor()
    #cursor.execute("SELECT count(*) FROM ingested_product where status='INGESTED' and creation_date > '2026-01-07T00:00:00' and creation_date < '2026-01-07T23:59:59' and product_name like 'S3%';")
    cursor.execute(query)
    record = cursor.fetchall()

    return record
 


@click.command()
@click.option('-c', '--catalogue-config', 'catalogue_config', type=str, required=True, help='Connection details to GSS postgres instance')
@click.option('-d', '--target_download_dir', 'download_dir', type=str, required=True, help='Download dir for rsync script to pull data to')
@click.option('-U', '--rsync_user', 'rsync_user', type=str, required=True, help='Rsync user.  i.e. root (!)')
@click.option('-H', '--rsync_host', 'rsync_host', type=str, required=True, help='Host to rsync from (or which has access to incoming mount).  i.e. srh-services13.ceda.ac.uk')
@click.option('-P', '--product_string', 'product_string', type=str, required=True, help='Product Search string to submit to psql db i.e. S1%_IW_SLC%')
@click.option('-D', '--product_date', 'product_date', type=str, required=True, help='Single date on which to search (ranges not yet supported) i.e. 2026-02-05T00:00:00')
@click.option('-o', '--output', 'output_file', type=str, required=True, help='Output shell script containing list of rsync commands')
@click.option('-l', '--limit', 'limit', type=str,  cls=MutuallyExclusiveOption, mutually_exclusive=["how_many"], help='Limit number of records i.e. 10')
@click.option('-h', '--how-many', 'how_many',  is_flag=True, default=False, cls=MutuallyExclusiveOption, mutually_exclusive=["list"],help='How many records match query? (will only show how many available)')
def main(catalogue_config, download_dir, rsync_user, rsync_host, product_string, product_date, output_file, how_many=False, limit=None):
    
    database, user, password, host, port, incoming = get_psql_conf(catalogue_config)

    if incoming is None:
        print ("No incoming dir specified!")
        #todo: add as option?
        sys.exit()

    #rsync_cmd_base = "srh-services13.ceda.ac.uk:"
    #gss_incoming = "/srh_data_incoming_7/gss-CEDA/srh-services13.ceda.ac.uk/incoming1/"

    try:
        records = get_records_from_db(database=database, user=user, password=password, limit=limit,  \
                                      product=product_string, date=product_date, host=host, port=port)

    except Exception as ex:
        print(f"Catalogue not available {ex}")
        sys.exit()

    if how_many:
        print (f"Found {len(records)} data files...")

    else:
        with open(output_file, 'w') as fp:
            for file_to_rsync in records:
                incoming_folder = f"{incoming}/{file_to_rsync[1][0:2]}/{file_to_rsync[1][2:4]}/{file_to_rsync[1]}"
                data_file = f"{incoming_folder}/{file_to_rsync[0]}"
                checksum_file = f"{incoming_folder}/~checksum~"

                #construct rsync commands - do this by writing sequentially to a text file that can be run as a shell script
                fp.writelines(f"rsync -ssh {rsync_user}@{rsync_host}:{data_file} {download_dir}/{file_to_rsync[0]}\n")
                fp.writelines(f"rsync -ssh {rsync_user}@{rsync_host}:{checksum_file} {download_dir}/{os.path.splitext(file_to_rsync[0])[0]}:{file_to_rsync[1]}.md5\n")

                #generate a consistent format _checksum file
                fp.writelines(f"filename='{download_dir}/{os.path.splitext(file_to_rsync[0])[0]}:{file_to_rsync[1]}.md5'; name=`basename $filename | tr ':' '\t' | awk '{{print $1}}'`;uid=`basename $filename | tr ':' '\t' | awk '{{print $2}}' | tr '.' '\t' | awk '{{print $1}}'`; md5=`cat $filename | awk '{{print $2}}'`; echo \"${{md5}} ${{name}} ${{uid}}\" > {download_dir}/{os.path.splitext(file_to_rsync[0])[0]}_checksum\n" )

                #remove the original md5 file
                fp.writelines(f"rm -f {download_dir}/{os.path.splitext(file_to_rsync[0])[0]}:{file_to_rsync[1]}.md5\n")

        print (f"Finished writing {len(records)} to {output_file}")
        
if __name__ == '__main__':
    main()