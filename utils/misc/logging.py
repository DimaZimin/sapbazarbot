import logging
import os

logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO, filename=os.getcwd() + '/sap_logs.log'
                    # level=logging.DEBUG,
                    )
