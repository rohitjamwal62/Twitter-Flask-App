import os
import re
import traceback
from time import sleep
from datetime import datetime
from configparser import ConfigParser
from colored import fg, bg, attr

import contextlib
config_file = os.path.abspath('./dev_mode.ini' if os.path.exists('./dev_mode.ini') else './config.ini')
config = ConfigParser()
config.read(config_file)
DEBUG = True if os.path.exists('./dev_mode.ini')  else False
LOG_LEVEL = int(config['Setup'].get('log_level',"1"))

# region color setup
lgreen = fg("light_green")
bg_green = f'{bg("light_green")}{fg("white")}'
magenta = fg("magenta_3c")
white = fg("white")
cyan = fg("cyan")
red = fg("red")
light_grey = fg("grey_74")
med_grey = fg("grey_15")
bg_red = f'{bg("red")}{fg("white")}'
invert = f'{bg("white")}{fg("black")}'
yellow = fg("yellow")
bg_yellow = f'{bg("yellow")}{fg("black")}'
bold = attr("bold")
reset = attr("reset")

TYPE_DEF = {
    'info': f'   {bold}{white}INFO |  {yellow}ℹ{reset} ',
    'loading': f'{bold}{white}LOADING |  {yellow}⏳{reset} ',
    'warning': f'{bold}{yellow}WARNING{reset} {bold}| {red}⚠️{reset}  ',
    'success': f'{bold}{lgreen}SUCCESS{reset} {bold}| {lgreen}✔{reset} ',
    'error': f'  {bold}{bg_red}ERROR{reset} {bold}| {red}☠{white}{bold}  ',
    'subtle': f'{reset}             ',
    'tab': f'{reset}             \t',
    'tick': f'{reset}          ✅ ',
    'cross': f'{reset}          ❌ ',
    'exclamation': f'{reset}          ⚠️  ',
    'input': f'{reset}          ➖ {bold}',
    'alert': f'  {bold}{yellow}ALERT{reset} | {yellow}⚠️{reset}  ',
    'process': f'{bold}{white}PROCESS | {yellow}⌛{reset} ',
    'process_done': f'{bold}{white}   FIN. | {lgreen}✔{reset} ',
    'developer': f'{bold}{fg("aquamarine_3")}DEVMODE {reset}| 🐞 {white}{bold}',
    'default': f'{reset}'
}

colors_dict = {"colors": ['light_green', 'magenta_3c', 'white', 'cyan', 'red', 'grey_74', 'grey_15', 'black', 'yellow', 'aquamarine_3'],
               "attributes": ['bold', 'reset']}
# endregion


def sprint(string, Type='subtle', end="\n", disable_in_production=False, silent=False):
    if silent:
        return
    Type = Type.lower()
    if Type == 'developer':
        if not DEBUG and disable_in_production:
            return
    if type(string) == str:
        string = string.replace("\n", "\n             ")
    try:
        if Type == 'input':
            print()
        if LOG_LEVEL > 1:
            __log_to_file(string)
        string = f'{TYPE_DEF[Type]}{string}{reset}'
        t_width = os.get_terminal_size().columns
        print(f"{string:<{t_width}}", end="\r" if Type == "loading" else end)
    except KeyError:
        raise KeyError(
            f"Invalid type: {Type}. Valid types are: {list(TYPE_DEF.keys())}")



def __log_to_file(string, filepath='logs/debug.log', add_timestamp_to_filename=True, add_process_info=True):
    base_dir = os.path.dirname(filepath)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    if add_timestamp_to_filename:
        filepath = os.path.join(
            base_dir, f'{os.path.splitext(os.path.basename(filepath))[0]}.{datetime.now().strftime("%Y-%m-%d")}.log')
    if add_process_info:
        filepath = filepath[:-4]
    # iterate through  dictionary and get values of each key
    for color in colors_dict["colors"]:
        string = string.replace(fg(color), '')
        string = string.replace(bg(color), '')
    for color in colors_dict["attributes"]:
        string = string.replace(attr(color), '')

    with open(filepath, 'a', encoding="utf8") as f:
        f.write(f'{datetime.now()} | {string}\n')


def sprint_vars(*vars, var_color=magenta, newlines=False, dev_mode_check=True):
    if dev_mode_check and not DEBUG:
        return
    string = []
    sep = ', ' if not newlines else '\n'
    stack = traceback.extract_stack()
    filename, lineno, function_name, code = stack[-2]
    var_names = re.compile(
        r'\((.*?)\).*$').search(code).groups()[0].replace(' ', '').split(',')
    for i, var in enumerate(vars):
        string.append(
            f"{bold}{med_grey}{type(var).__name__} {var_color}{var_names[i]}{med_grey} :=> {reset}{light_grey}{var}{reset}")
    DEV1 = f'{TYPE_DEF["developer"]}{reset}{med_grey}[Line {lineno}]{white} '
    if newlines:
        DEV1 = f'{DEV1}\n'
    print(f'{DEV1}{sep.join(string)}{reset}', end='\n')



def sprintSaveCSV(df_input, OUTPUT_CSV, retry=True, silent=False,**args):
    sprint(f"Exporting CSV -> {cyan}{OUTPUT_CSV}{reset}",
           Type="info", end='\r', silent=silent)
    notifiedOnce = False
    while True:
        try:
            with open(OUTPUT_CSV, encoding='utf8', mode='w'):
                df_input.to_csv(OUTPUT_CSV, index=False,**args)
            break
        except PermissionError:
            if not notifiedOnce:
                sprint(
                    f'Unable to export CSV. File is in use {yellow}{OUTPUT_CSV}{reset}', Type="alert")
            if retry:
                sprint(
                    f'Kindly, close the file for script to continue...', Type="subtle")
                notifiedOnce = True
            else:
                break
        sleep(2)
    sprint(f'Exported CSV -> {cyan}{OUTPUT_CSV}{reset}',
           Type="success", end='\n', silent=silent)



def TIME(onlytime=False, am_pm=False):
    if onlytime:
        if am_pm:
            return datetime.now().strftime("%I:%M:%S %p")
        else:
            return datetime.now().strftime("%H:%M:%S")
    if am_pm:
        return datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    else:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def exit_handler(signum, frame):
    global driver
    print()
    sprint(f"{red}{bold}CTRL+C pressed!{reset} Exiting the script now!", Type='alert')
    with contextlib.suppress(Exception):
        driver.quit()  # if driver is defined
    exit(0)
