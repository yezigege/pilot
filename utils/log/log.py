# -*- coding: utf-8 -*-
"""
This Code From Someplace
"""

import time
import os
import fcntl
import logging
from logging.handlers import TimedRotatingFileHandler

from .config import LogName, _MIDNIGHT, LOCAL_LOG_DIR


class MultiProcessTimedRotatingFileHandler(TimedRotatingFileHandler):

    _stream_lock = None

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        dfn = self.baseFilename + '.' + time.strftime(self.suffix, timeTuple)

        # 加锁保证rename的进程安全
        if os.path.exists(self.baseFilename) and not self.is_baseFile_renamed(dfn):
            fcntl.lockf(self.stream_lock, fcntl.LOCK_EX)
            try:
                if os.path.exists(self.baseFilename) and not self.is_baseFile_renamed(dfn):
                    os.rename(self.baseFilename, dfn)
                    self.clear_lock_file()
                    self.write_lock_file(dfn)
            finally:
                fcntl.lockf(self.stream_lock, fcntl.LOCK_UN)

        # 加锁保证删除文件的进程安全
        if self.backupCount > 0:
            if self.getFilesToDelete():
                fcntl.lockf(self.stream_lock, fcntl.LOCK_EX)
                try:
                    files_to_delete = self.getFilesToDelete()
                    if files_to_delete:
                        for s in files_to_delete:
                            os.remove(s)
                finally:
                    fcntl.lockf(self.stream_lock, fcntl.LOCK_UN)

        if not self.delay:
            # _open默认是以‘a'的方式打开，是进程安全的
            self.stream = self._open()

        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

    def computeRollover(self, currentTime):
        """
        Work out the rollover time based on the specified time.
        """
        result = currentTime + self.interval
        # If we are rolling over at midnight or weekly, then the interval is already known.
        # What we need to figure out is WHEN the next interval is.  In other words,
        # if you are rolling over at midnight, then your base interval is 1 day,
        # but you want to start that one day clock at midnight, not now.  So, we
        # have to fudge the rolloverAt value in order to trigger the first rollover
        # at the right time.  After that, the regular interval will take care of
        # the rest.  Note that this code doesn't care about leap seconds. :)
        if self.when in ['MIDNIGHT', 'M', 'H'] or self.when.startswith('W'):
            # This could be done with less code, but I wanted it to be clear
            if self.utc:
                t = time.gmtime(currentTime)
            else:
                t = time.localtime(currentTime)
            currentHour = t[3]
            currentMinute = t[4]
            currentSecond = t[5]
            # r is the number of seconds left between now and midnight
            if self.when == 'MIDNIGHT' or self.when.startswith('W'):
                r = _MIDNIGHT - \
                    ((currentHour * 60 + currentMinute) * 60 + currentSecond)
            elif self.when == 'M':
                r = 60 - currentSecond
            elif self.when == 'H':
                r = 60 * 60 - (currentMinute * 60 + currentSecond)

            result = currentTime + r
            # If we are rolling over on a certain day, add in the number of days until
            # the next rollover, but offset by 1 since we just calculated the time
            # until the next day starts.  There are three cases:
            # Case 1) The day to rollover is today; in this case, do nothing
            # Case 2) The day to rollover is further in the interval (i.e., today is
            #         day 2 (Wednesday) and rollover is on day 6 (Sunday).  Days to
            #         next rollover is simply 6 - 2 - 1, or 3.
            # Case 3) The day to rollover is behind us in the interval (i.e., today
            #         is day 5 (Saturday) and rollover is on day 3 (Thursday).
            #         Days to rollover is 6 - 5 + 3, or 4.  In this case, it's the
            #         number of days left in the current week (1) plus the number
            #         of days in the next week until the rollover day (3).
            # The calculations described in 2) and 3) above need to have a day added.
            # This is because the above time calculation takes us to midnight on this
            # day, i.e. the start of the next day.
            if self.when.startswith('W'):
                day = t[6]  # 0 is Monday
                if day != self.dayOfWeek:
                    if day < self.dayOfWeek:
                        daysToWait = self.dayOfWeek - day
                    else:
                        daysToWait = 6 - day + self.dayOfWeek + 1
                    newRolloverAt = result + (daysToWait * (60 * 60 * 24))
                    if not self.utc:
                        dstNow = t[-1]
                        dstAtRollover = time.localtime(newRolloverAt)[-1]
                        if dstNow != dstAtRollover:
                            if not dstNow:
                                addend = -3600
                            else:  # DST bows out before next rollover, so we need to add an hour
                                addend = 3600
                            newRolloverAt += addend
                    result = newRolloverAt
        return result

    @property
    def stream_lock(self):
        if not self._stream_lock:
            self._stream_lock = self._open_lock_file()
        return self._stream_lock

    def _get_lock_file(self):
        # Use 'file.lock' and not 'file.log.lock' (Only handles the normal "*.log" case.)
        if self.baseFilename.endswith('.log'):
            lock_file = self.baseFilename[:-4]
        else:
            lock_file = self.baseFilename
        lock_file += '.lock'
        return lock_file

    def _open_lock_file(self):
        lock_file = self._get_lock_file()
        return open(lock_file, 'a+')

    def clear_lock_file(self):
        self.stream_lock.seek(0)
        self.stream_lock.truncate()

    def write_lock_file(self, content):
        self.stream_lock.write(content)
        self.stream_lock.flush()

    def read_lock_file(self):
        self.stream_lock.seek(0)
        return self.stream_lock.read()

    def is_baseFile_renamed(self, dfn):
        # dfn可能比记录在lock文件中的dfn字符串小。因为dfn的名字不是依据当前时间确定的。
        # dfn依据进程当前存储的rolloverAt。如果该进程在上一个时间周期内没有轮转[极端情况下才可能发生]。
        # 它的rolloverAt值是落后的，从而生成的dfn文件名字也是一个落后版本。这种情况，不能轮转。
        return self.read_lock_file() >= dfn


class PilotLoggerAdapter(logging.LoggerAdapter):

    def __init__(self, logger, extra=None):
        super().__init__(logger, extra)
        self.logger = logger
        self.extra = extra

    def process(self, msg, kwargs):
        if self.extra:
            kwargs['extra'] = self.extra
        msg = '^_^|' + msg

        return msg, kwargs


formatter = logging.Formatter(
    fmt='[%(asctime)s][%(name)s][%(levelname)s] => %(message)s',
    datefmt="%Y-%m-%d  %H:%M:%S %a"
)


def get_logger(name, extra=None):
    return PilotLoggerAdapter(logging.getLogger(name), extra=extra)


def make_handler(log_name, when='MIDNIGHT'):
    if not os.path.exists(LOCAL_LOG_DIR):
        os.makedirs(LOCAL_LOG_DIR)
    logfile = os.path.join(LOCAL_LOG_DIR, (log_name + '.log'))
    handler = MultiProcessTimedRotatingFileHandler(
        filename=logfile,
        when=when,
        interval=1,
        backupCount=30,
        encoding='utf-8',
        delay=False,
        utc=True)
    handler.setFormatter(formatter)
    return handler


pilot_handler = make_handler(LogName.pilot.name)
