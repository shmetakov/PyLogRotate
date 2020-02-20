import json
import os
import zipfile
import shutil
import logging

from datetime import datetime
from datetime import timedelta


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler(datetime.now().strftime("%Y-%m-%d_%H.log"))
fh.setFormatter(formatter)

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)

config_list = []


def read_config():

    file_name = "config.json"

    try:
        with open(file_name, "r", encoding="utf-8") as json_file:
            global config_list
            config_list = json.load(json_file)
            logger.info(f"Read '{file_name}' config file")
            logger.info(f"Data :\n{json.dumps(config_list, indent=1)}")

    except BufferError as err:
        logger.error(err)
    except Exception as err:
        logger.error(err)
    else:
        return True

    return False


def compression(path_to_file, path_to_arch_dir):

    file = f"{path_to_file}.zip"

    try:
        with zipfile.ZipFile(f"{file}", 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(path_to_file, compresslevel=9)

    except BufferError as err:
        logger.error(err)
    except Exception as err:
        logger.error(err)
    else:
        logger.debug("Ok!!!")
        try:
            shutil.move(file, path_to_arch_dir)
        except shutil.Error as err:
            logger.warning(err)
        except BufferError as err:
            logger.error(err)
        except Exception as err:
            logger.error(err)

        try:
            os.remove(path_to_file)
        except OSError as err:
            logger.error(err)


def check_arch_dir(path_to_arch, size):

    os.chdir(path_to_arch)

    culc_size = lambda x: sum([os.path.getsize(f'{x}/{file}') for file in os.listdir(x)]) / 1000 / 1000
    total_size = culc_size(path_to_arch)

    logger.info(f"Total size of {path_to_arch}: {total_size:.3f} Mb")

    list_file = sorted(os.listdir(), key=os.path.getmtime)

    while total_size > size:

        try:
            os.remove(list_file[0])
        except OSError as err:
            logger.error(err)

        list_file.remove(list_file[0])
        total_size = culc_size(path_to_arch)


def rotate(dict_config):
    log_dir = dict_config.get('log_dir', None)
    target = dict_config.get('target', None)
    size_target = dict_config.get('size_target', 0)
    period = dict_config.get('period', 0)

    if not log_dir:
        logger.error("The param 'log_dir' not found in config file")
        return
    elif not os.path.exists(log_dir):
        logger.error(f"The path '{log_dir}' not found")
        return

    if not target:
        logger.error("The param 'target' not found in config file")
        return

    if not period:
        logger.error("The param 'period' not found in config file")
        return

    if not os.path.exists(target):
        logger.warning(f"{target} is not exist!")
        logger.info(f"Create {target}")

        try:
            os.makedirs(target)
        except OSError as err:
            logger.error(err)

    os.chdir(log_dir)

    for log_file in sorted(os.listdir(), key=os.path.getmtime):
        if not os.path.isfile(os.path.abspath(log_file)):
            continue

        mod_timestamp = datetime.now()

        try:
            mod_timestamp = datetime.fromtimestamp(os.stat(log_file).st_mtime)
        except OSError as err:
            logger.error(err)

        if (datetime.now() - mod_timestamp) > timedelta(days=period):
            logger.info(f"Compression: {mod_timestamp} {log_file} {datetime.now() - mod_timestamp}")
            compression(log_file, target)

    if size_target:
        check_arch_dir(target, size_target)


if __name__ == "__main__":

    logger.info('*' * 100)
    logger.info("Start program")

    if not read_config():
        logger.error("Can't open config file. Exit")
    else:
        for i in config_list:
            rotate(i)

    logger.info("Finish program!")
    logger.info('*' * 100)
