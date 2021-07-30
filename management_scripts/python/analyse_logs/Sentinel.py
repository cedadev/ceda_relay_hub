from datetime import datetime

'''
Utilities method to allow various manipulation and extraction of Sentinel dates etc from filenames.
'''

class Sentinel_Product(object):
    '''
    Class dedicated to definition of Sentinel products and operations on Sentinel product names
    '''

    MISSIONS = ['S1A', 'S1B', 'S2A', 'S2B', 'S3A', 'S3B', 'S5P']

    #S5P_NRTI_L2__CLOUD__20210521T020651_20210521T021151_18666_01_020104_20210521T024

    #sensing date string indices by mission
    #updated - dict as value indicates where different naming structures used for same mission.  Thats you S2A.. (PIA).
    SENSING_DATE_PARAMS = {'S1A':'17:32', 'S1B':'17:32', 'S2A':{'S2A_OPER_PRD_MSIL1C':'25:40', 'S2A_MSIL1C':'11:26','S2A_MSIL2A':'11:26'},\
                           'S2B':{'S2B_OPER_PRD_MSIL1C':'25:40', 'S2B_MSIL1C':'11:26','S2A_MSIL2A':'11:26', 'S2B_MSIL2A':'11:26'}, 'S3A':'16:30', 'S3B':'16:30', 'S5P':'20:35'}

    #product type string indices by mission.  Follow convention used for SENSING_DATA_PARAMS
    #S1 See https://sentinel.esa.int/web/sentinel/user-guides/sentinel-1-sar/naming-conventions
    #S2 See
    #S3 See
    #PRODUCT_NAME_PARAMS = {'S1A':'0:11', 'S1B':'0:11', 'S2A':'0:19'}
    PRODUCT_NAME_PARAMS = {'S1A':'0:11', 'S1B':'0:11', 'S2A':{'S2A_OPER_PRD_MSIL1C':'0:19', 'S2A_MSIL1C':'0:10', 'S2A_MSIL2A':'0:10'}, \
                           'S2B':{'S2B_OPER_PRD_MSIL1C':'0:19', 'S2B_MSIL1C':'0:10', 'S2B_MSIL2A':'0:10'}, 'S3A':'0:11', 'S3B':'0:11', 'S5P':'0:20'}


    def get_product_date(self, date=False):
        '''
        Method to work out the product sensing date based on filename.  Return as simple date if date is true
        :return:product date (datetime object)
        '''

        #if legal get the date range values from the product name
        if type(self.SENSING_DATE_PARAMS[self.mission]) is dict:
            for sub_type in self.PRODUCT_NAME_PARAMS[self.mission].keys():
                if sub_type in self.product_name:
                    daterangeindex = self.SENSING_DATE_PARAMS[self.mission][sub_type].split(":")
        else:
            daterangeindex = self.SENSING_DATE_PARAMS[self.mission].split(":")

        try:
            product_datestamp = self.product_name[int(daterangeindex[0]):int(daterangeindex[1])]

        except Exception as ex:
            raise Exception ("ERROR: Unable to extract daterange for %s (%s)" %(self.product_name,ex))

        #convert to datetime format
        try:
            #"%Y-%m-%dT%H:%M:%S
            datestamp =  datetime.strptime(product_datestamp, "%Y%m%dT%H%M%S")
            if not date:
                return datestamp

            else:
                return datetime.strptime(datestamp.strftime('%Y%m%d'),'%Y%m%d')

        except Exception as ex:
            raise Exception ("ERROR: Unable to convert '%s' to datetime (%s)" %(self.product_name,ex))


    def __init__(self,product_name):
        '''
        Initialise class by returning a product type - needed for use elsewhere

        :param product_name:
        :return:
        '''

        self.product_name = product_name
        self.mission = None
        self.product_type = None

        #what mission are we in?
        try:
            if self.product_name[0:3] in self.MISSIONS:
                self.mission = self.product_name[0:3]
            else:
                raise Exception("Mission not supported: %s" %self.product_name[0:4])

            #work out product type
            if type(self.PRODUCT_NAME_PARAMS[self.mission]) is dict:

                for sub_type in self.PRODUCT_NAME_PARAMS[self.mission].keys():
                    if sub_type in self.product_name:
                        self.product_type = \
                            self.product_name[int(self.PRODUCT_NAME_PARAMS[self.mission][sub_type].split(':')[0]):int(self.PRODUCT_NAME_PARAMS[self.mission][sub_type].split(':')[1])]
            else:
                self.product_type = self.product_name[int(self.PRODUCT_NAME_PARAMS[self.mission].split(':')[0]):int(self.PRODUCT_NAME_PARAMS[self.mission].split(':')[1])]

            if self.product_type[-1] == '_':
                self.product_type = self.product_type[:-1]

            if self.product_type is None:
                raise Exception ("Could not assign product type")

        except Exception as ex:
            raise Exception("Error: %s" %ex)
