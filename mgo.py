#!/usr/bin/python3

from urllib import request
from urllib.error import HTTPError
import argparse
import os
import platform
import json
import re
import shutil
import subprocess
import tarfile
import zipfile

# Runs a go subprocess and get the installed version
def get_installed_go_version():
    out = subprocess.run(['go','version'], capture_output=True).stdout
    result = re.search('go(\d+)\.(\d+)\.?(\d+)?(\w+)*', out.decode('utf-8'))
    if result:
        return result[0]

# Get a list of go releases using Github api
def get_go_releases():
    URL = 'https://api.github.com/repos/golang/go/git/matching-refs/tags/go'
    req = request.urlopen(URL)
    jsonResponse = json.loads(req.read())
    tagCount = len(jsonResponse)
    if tagCount > 0:
        releases = [jsonResponse[x]['ref'] for x in range(tagCount)]
        releases = [x[x.rindex('/')+1:] for x in releases]
        return releases

# Returns the latest go version string available
# If allow_preview is True include betas and release candidates
def get_go_release(allow_preview=False):
    releases = get_go_releases()
    if releases:
        for version in releases[::-1]:
            ver_info = parse_version(version)
            if ver_info['is_beta'] or ver_info['is_release_candidate']:
                if allow_preview:
                    return version
            else:
                return version

# Returns a dictionary with fields version, major, minor, patch, is_beta and is_release_candidate
def parse_version(ver):
    matches = re.search('(\d+)\.(\d+)\.?(\d+)?(\w+)*', ver)
    if matches:
        version = matches[0]
        major = matches[1]
        minor = matches[2]
        patch = matches[3] or 0
        beta = None
        release_candidate = None
        if matches[4]:
            beta = True if matches[4].find('beta') >= 0 else False
            release_candidate = True if matches[4].find('rc') >= 0 else False
        return {
            'version': version,
            'major': int(major),
            'minor': int(minor),
            'patch': int(patch),
            'is_beta': beta,
            'is_release_candidate': release_candidate
        }

# Returns 0 if ver1 and ver2 match
# Returns a positive number if ver1 is newer than ver2
# Returns a negative number if ver2 is newer than ver1
def compare_versions(ver_info1, ver_info2):
    result = 0
    result += 100000 * (ver_info1['major'] - ver_info2['major'])
    result += 10 * (ver_info1['minor'] - ver_info2['minor'])
    result += ver_info1['patch'] - ver_info2['patch']
    if ver_info1['is_beta']: result += 1
    if ver_info1['is_release_candidate']: result += 2
    if ver_info2['is_beta']: result -= 1
    if ver_info2['is_release_candidate']: result -= 2
    return result

# Returns True if ver2 is newer than ver1. Returns False otherwise.
# If allow_preview is True release canditates and betas will count as valid
# to replace ver1.
def should_update(ver1, ver2, allow_preview=False):
    ver_info1 = parse_version(ver1)
    ver_info2 = parse_version(ver2)
    result = compare_versions(ver_info1, ver_info2)
    if result < 0:
        is_preview = ver_info2['is_beta'] or ver_info2['is_release_candidate']
        if is_preview:
            return allow_preview
        else:
            return True
    return False

def get_update_version(allow_preview):
    try:
        installed_version = get_installed_go_version()
        releases = get_go_releases()

        # Compute only later versions
        index = releases.index(installed_version)
        candidates = releases[index+1:]
        # Find latest version that is a suitable replacement
        for candidate in candidates[::-1]:
            if should_update(installed_version, candidate, allow_preview):
                return candidate
    except json.JSONDecodeError as e:
        print('Could not get release info from Github')
    except subprocess.CalledProcessError as e:
        print('Could not get installed go version')
    except ValueError as e:
        print('Error interpreting go version scheme')

def build_release_file_name(version):
    system = platform.system().lower()
    arch = archMap[platform.machine()]
    extension = extensionMap[system]
    version = version if version.find('go') == 0 else 'go' + version
    name = version + '.' + system + '-' + arch + extension
    return name

# Donwload file and show progress report
def donwload_file(name):
    request.urlretrieve(
        'https://go.dev/dl/' + name,
        name,
        progress_report
    )
    print() # New line after donwload is finished

# Remove current go installtion
def remove_installation():
    go_location = shutil.which('go')
    go_location = go_location[:go_location.rindex(os.sep + 'bin')]
    parent_location = go_location[:go_location.rindex(os.sep + 'go')]
    if go_location:
        shutil.rmtree(go_location)
    return parent_location

def extract_file(name, location):
    if name.endswith('.tar.gz'):
        compressed_file = tarfile.open(name, mode='r:gz')
        compressed_file.extractall(path=location)
    elif name.endswith('.zip'):
        compressed_file = zipfile.ZipFile(name)
        compressed_file.extractall(path=location)


def progress_report(count, blocksize, totalsize):
    print('\rProgress: ' + str(round((count * blocksize) * 100 / totalsize)) + '%', end='')

archMap = {
    'AMD64': 'amd64',
    'x86_64': 'amd64'
}
extensionMap = {
    'linux': '.tar.gz',
    'windows': '.zip',
    'darwin': '.pkg'
}
def update_go_version(allow_preview):
    # Check if there is an update available
    version = get_update_version(allow_preview)
    if version:
        print('Version ' + version + ' available')
        print('Downloading file...')
        # Build release name based on platform
        name = build_release_file_name(version)

        # Download go release
        donwload_file(name)

        # Remove current installtion
        print('Removing current installation...')
        go_location = remove_installation()
        print(go_location)

        # Extract new version
        print('Extracting file...')
        extract_file(name, go_location)

        # Remove downloaded file
        print('Removing temporary file...')
        os.remove(name)

        print('Go version updated')
    else:
        print('Your already have the latest version')

def install_go_version(install_path, version, allow_preview):
    target_version = version
    if not target_version:
        release = get_go_release(allow_preview)
        if release:
            target_version = release
        else:
            raise RuntimeError('Could not find a go release')

    if parse_version(target_version):
        name = build_release_file_name(target_version)

        print('Downloading go version ' + target_version)
        donwload_file(name)

        # Create directory if it does not exist
        if not os.path.isdir(install_path):
            os.mkdir(install_path)

        print('Extracting file...')
        extract_file(name, install_path)

        # Remove downloaded file
        print('Removing temporary file...')
        os.remove(name)
        print('Installation complete')

def run():
    parser = argparse.ArgumentParser(description='manage go installation')
    # Subparser for each command
    subparsers = parser.add_subparsers(dest='cmd')

    # Show current version
    status_parser = subparsers.add_parser('status', help='show installed go version')

    # Check for new version
    check_parser = subparsers.add_parser('check', help='check if there is an update')
    check_parser.add_argument('-p', '--preview', help='include beta or release candidates', action='store_true')

    # Update version
    update_parser = subparsers.add_parser('update', help='update go version')
    update_parser.add_argument('-p', '--preview', help='include beta or release candidates', action='store_true')

    # Install specific version
    install_parser = subparsers.add_parser('install', help='install go')
    install_parser.add_argument('path', help='installation directory')
    install_parser.add_argument('-v', '--version', help='specify go version to install (defaults to latest stable if not provided)')
    install_parser.add_argument('-p', '--preview', help='include beta or release candidates', action='store_true')

    # List available versions
    available_parser = subparsers.add_parser('available', help='list available go versions')
    available_parser.add_argument('-c', '--count', help='limit list size (defaults to 10)')

    # Execute commands
    args = parser.parse_args()
    if args.cmd == 'status':
        version = get_installed_go_version()
        if version:
            print(get_installed_go_version())
        else:
            print('Could not find a valid go installation')
    elif args.cmd == 'check':
        version = get_update_version(args.preview)
        if version:
            print(version)
        else:
            print('No update available')
    elif args.cmd == 'update':
        try:
            update_go_version(args.preview)
        except PermissionError as e:
            print('Failed. Need privileged permission.')
    elif args.cmd == 'install':
        try:
            install_go_version(args.path, args.version, args.preview)
        except PermissionError as e:
            print('Failed. Need privileged permission.')
        except HTTPError as e:
            print(e)
        except RuntimeError as e:
            print(e)
    elif args.cmd == 'available':
        releases = get_go_releases()
        if releases:
            total = len(releases)
            count = int(args.count) or 10
            for release in releases[:total - count - 1:-1]:
                print(release)
    else:
        parser.print_help()

if __name__ == '__main__':
    run()