import os
os.sys.path.append(os.getcwd())

from util.logger import Logger

Logger.d('this is debug log.')
Logger.i('this is info log.')
Logger.w('this is warning log.')
Logger.e('this is error log.')
Logger.c('this is critical log.')

zero = 0
invalid = 32 / zero
