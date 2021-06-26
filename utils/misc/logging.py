import logging
# filename='logs.log',filemode='a',
logging.basicConfig(filename='logs.log',filemode='a',
                    format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO,
                    )
