#!/usr/bin/env python3
from os.path import basename, dirname, abspath
import time
import logging
import functools
from util.defaults import set_params

PROJECT_ROOT_PATH = dirname(dirname(abspath(__file__)))


class CustomFormatter(logging.Formatter):
    white = "\x1b[m"
    italic_white = "\x1b[3m"
    underline_white = "\x1b[4m"

    muted = "\x1b[38;2;2;20;5m"
    debug = "\x1b[38;50;2;2;5m"
    black = "\x1b[30m"
    lightgrey = "\x1b[37m"
    grey = "\x1b[38;20m"
    midgrey = "\x1b[90m"

    gold = "\x1b[33m"
    yellow = "\x1b[93m"
    yellow2 = "\x1b[33;20m"
    yellow3 = "\x1b[33;1m"
    lightyellow = "\x1b[38;2;250;250;150m"

    green = "\x1b[32m"
    mintgreen = "\x1b[38;2;150;250;150m"
    lightgreen = "\x1b[92m"
    othergreen = "\x1b[32;1m"
    drabgreen = "\x1b[38;2;150;200;150m"

    skyblue = "\x1b[38;2;150;250;250m"
    iceblue = "\x1b[38;2;59;142;200m"
    blue = "\x1b[34m"
    magenta = "\x1b[35m"
    purple = "\x1b[38;2;150;150;250m"
    cyan = "\x1b[36m"

    lightblue = "\x1b[96m"
    lightcyan = "\x1b[96m"

    pink = "\x1b[95m"
    lightred = "\x1b[91m"
    red = "\x1b[31;20m"
    red2 = "\x1b[31m"
    bold_red = "\x1b[31;1m"

    table = "\x1b[37m"
    status = "\x1b[94m"
    debug = "\x1b[30;1m"
    reset = "\x1b[0m"

    format = (
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
    )
    datefmt = "%d-%b-%y %H:%M:%S"

    FORMATS = {
        logging.DEBUG: debug + format + reset,
        logging.INFO: lightgreen + format + reset,
        logging.WARNING: red + format + reset,
        logging.ERROR: lightred + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        if record.levelname == "STOPWATCH":
            log_fmt = (
                self.yellow
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            )
        elif record.levelname == "QUERY":
            log_fmt = (
                self.lightyellow
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            )
        elif record.levelname == "LOOP":
            log_fmt = (
                self.purple
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            )
        elif record.levelname == "MUTED":
            log_fmt = (
                self.muted
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            )
        elif record.levelname == "CALC":
            log_fmt = (
                self.lightcyan
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            )
        elif record.levelname == "DEBUG":
            log_fmt = (
                self.debug
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            )
        elif record.levelname == "MERGE":
            log_fmt = (
                self.mintgreen
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            )
        elif record.levelname == "DEXRPC":
            log_fmt = (
                self.skyblue
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            )
        elif record.levelname == "REQUEST":
            log_fmt = (
                self.lightyellow
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            )
        elif record.levelname == "UPDATED":
            log_fmt = (
                self.skyblue
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
            )
        elif record.levelname == "PAIR":
            log_fmt = (
                self.skyblue
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
            )
        elif record.levelname == "SAVE":
            log_fmt = (
                self.drabgreen
                + "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
                + self.reset
            ) + self.reset
        else:
            log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def addLoggingLevel(levelName, levelNum, methodName=None):
    # From https://stackoverflow.com/questions/2183233/
    # how-to-add-a-custom-loglevel-to-pythons-logging-facility/

    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError("{} already defined in logging module".format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError("{} already defined in logging module".format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError("{} already defined in logger class".format(methodName))

    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


logger = logging.getLogger("defi-stats")
# create console handler with a higher log level
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)

# Shows DB imports
addLoggingLevel("PAIR", logging.DEBUG + 11)
logger.setLevel("PAIR")

# Shows DB imports
addLoggingLevel("MERGE", logging.DEBUG + 9)
logger.setLevel("MERGE")

# Shows cache updates
addLoggingLevel("UPDATED", logging.DEBUG + 8)
logger.setLevel("UPDATED")

# Shows database req/resp
addLoggingLevel("QUERY", logging.DEBUG + 7)
logger.setLevel("QUERY")

# Shows dex api req/resp
addLoggingLevel("DEXRPC", logging.DEBUG + 6)
logger.setLevel("DEXRPC")

# Shows cache loop updates
addLoggingLevel("LOOP", logging.DEBUG + 5)
logger.setLevel("LOOP")

# Shows cache loop updates
addLoggingLevel("CALC", logging.DEBUG + 4)
logger.setLevel("CALC")

# Shows cache loop updates
addLoggingLevel("SAVE", logging.DEBUG + 3)
logger.setLevel("SAVE")


# Shows generally ignorable errors, e.g. CoinConfigNotFound
addLoggingLevel("MUTED", logging.DEBUG - 1)
logger.setLevel("MUTED")

# Shows cache loop updates
addLoggingLevel("REQUEST", logging.DEBUG + 2)
logger.setLevel("REQUEST")


def send_log(loglevel, msg):
    match loglevel:
        case "info":
            logger.info(f"   {msg}")
        case "muted":
            pass
        case "save":
            logger.save(f"   {msg}")
        case "merge":
            logger.merge(f"  {msg}")
        case "merge":
            logger.merge(f"  {msg}")
        case "updated":
            logger.updated(f"{msg}")
        case "calc":
            logger.calc(f"   {msg}")
        case "warning":
            logger.warning(f"{msg}")
        case "error":
            logger.error(f"  {msg}")
        case "debug":
            logger.debug(f"  {msg}")
        case "error":
            logger.error(f"  {msg}")
        case "loop":
            logger.loop(f"   {msg}")
        case "pair":
            logger.pair(f"   {msg}")
        case "query":
            logger.query(f"  {msg}")
        case "request":
            logger.request(f"{msg}")
        case _:
            logger.debug(f"   {msg}")


class StopWatch:
    def __init__(self, start_time, **kwargs) -> None:
        self.start_time = start_time
        self.get_stopwatch(**kwargs)

    def get_stopwatch(self, **kwargs):
        options = ["trigger", "msg", "loglevel"]
        set_params(self, kwargs, options)
        duration = int(time.time()) - int(self.start_time)
        if self.trigger == 0:
            self.trigger = 10
        self.trigger = 0

        # if duration < 5
        #       and not (self.error
        #       or self.debug or self.warning or self.loop):
        #    self.muted = True
        if duration >= self.trigger:
            if not isinstance(self.msg, str):
                self.msg = str(self.msg)
            lineno = self.trace["lineno"]
            filename = self.trace["file"]
            func = self.trace["function"]
            if PROJECT_ROOT_PATH in self.msg:
                self.msg = self.msg.replace(f"{PROJECT_ROOT_PATH}/", "")
            self.msg = f"|{duration:>4} sec | {func:<20} | {str(self.msg):<70} "
            self.msg += f"| {basename(filename)}:{lineno}"

            send_log(loglevel=self.loglevel, msg=self.msg)


def get_trace(func, error=None):
    msg = {
        "function": func.__name__,
        "file": func.__code__.co_filename,
        "lineno": func.__code__.co_firstlineno,
        "vars": func.__code__.co_varnames,
    }
    if error is not None:
        msg.update({"error": error})
    return msg


# Returns console colors for customising
def show_pallete():
    logger.info("info")
    logger.debug("debug")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")
    logger.updated("updated")
    logger.merge("merge")
    logger.save("save")
    logger.calc("calc")
    logger.dexrpc("dexrpc")
    logger.loop("loop")
    logger.muted("muted")
    logger.query("query")
    logger.request("request")


# A decorator for returning runtime of functions:def timed(func):
def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = int(time.time())
        duration = int(time.time()) - start_time
        trace = get_trace(func)
        msg = "<<< no msg provided >>>"
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            ignore_until = 0
            loglevel = "error"
            if isinstance(e, ValueError):
                # Custom logic here
                pass
            msg = f"{type(e)}: {e}"
            StopWatch(start_time, trace=trace, loglevel=loglevel, msg=msg)
        else:
            send = False
            msg = ""
            ignore_until = 0
            loglevel = "info"
            if isinstance(result, dict):
                if "loglevel" in result:
                    loglevel = result["loglevel"]
                    send = True
                else:
                    # if not using `default_result`
                    return result
                if "message" in result:
                    msg = result["message"]
                    send = True
                if "ignore_until" in result:
                    ignore_until = result["ignore_until"]
                    send = True
                if duration >= ignore_until and send:
                    StopWatch(start_time, trace=trace, loglevel=loglevel, msg=msg)
                # Using `default_result`, with actual data to return
                if "data" in result:
                    if result["data"] is not None:
                        result = result["data"]
            return result

    return wrapper


if __name__ == "__main__":
    show_pallete()
