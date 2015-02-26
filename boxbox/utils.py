
try:
    input = raw_input
except:
    pass

import logging


def yesno(question, yes=None, no=None, imax=10):
    yes = yes if yes else 'y'
    no = no if no else 'n'
    iteration = 0
    responses = [yes, no]
    answer = ''
    unknown = ''
    while answer not in responses and iteration < imax:
        qfmt = '{0}{1} ({2}/{3}): '
        answer = input(qfmt.format(unknown, question, yes, no))
        if answer == yes:
            return True
        elif answer == no:
            return False
        else:
            unknown = 'invalid response, please try again.\n\n'
        iteration += 1


def nl(level=None):
    level = level if level else 'info'
    getattr(logging, level)('')


def log(message, error=False, *args, **kwargs):
    if not message:
        return
    if error:
        logging.error(message, *args, **kwargs)
    else:
        logging.info(message, *args, **kwargs)


def warning(message, *args, **kwargs):
    logging.warning(message, *args, **kwargs)


def debug(message, *args, **kwargs):
    logging.debug(message, *args, **kwargs)


def task(header):
    out = '\\\\\\\\\\\\\\\\\nTASK: {header}\n////////'
    logging.info(out.format(header=header))
