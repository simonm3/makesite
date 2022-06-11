import logging
from logging import Formatter, StreamHandler, getLogger


def getlog():
    """
    configure logging
    :return: configured root logger
    """
    fmt = Formatter(
        fmt="[{module}:{lineno}:{levelname}]:{message} (time={asctime} {processName})",
        datefmt="%b-%d %H:%M",
        style="{",
    )
    # root log
    log = getLogger()
    stream = StreamHandler()
    stream.setFormatter(fmt)
    log.handlers.clear()
    log.addHandler(stream)
    log.setLevel(logging.DEBUG)
    log.info(f"logging started from {__file__}")

    return log


log = getlog()
