import re


def check_env_name(env_name, regex_list):

    match = False

    for regex in regex_list:
        mach = re.search(regex, env_name)
        if mach:
            match = match or True
        else:
            match = match or False
    
    return match
