from util import *
import argparse
from urllib.error import HTTPError

def build_parser():
    parser = argparse.ArgumentParser(description='Manage go installation')
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

    # Uninstall go installation
    uninstall_parser = subparsers.add_parser('uninstall', help='remove go installation')

    return parser

def status_command():
    version = get_installed_go_version()
    if version:
        print(get_installed_go_version())
    else:
        print('Could not find a valid go installation')

def check_command(allow_preview):
    version = get_update_version(allow_preview)
    if version:
        print(version)
    else:
        print('No update available')

def update_command(allow_preview):
    try:
        update_go_version(allow_preview)
    except PermissionError as e:
        print('Failed. Need privileged permission.')

def install_command(install_path, version, allow_preview):
    try:
        install_go_version(install_path, version, allow_preview)
    except PermissionError as e:
        print('Failed. Need privileged permission.')
    except HTTPError as e:
        print(e)
    except RuntimeError as e:
        print(e)

def available_command(count):
    releases = get_go_releases()
    if releases:
        total = len(releases)
        list_size = 10
        if count:
            list_size = int(count)
        for release in releases[:total - list_size - 1:-1]:
            print(release)

def uninstall_command():
    print('Removing go installation...')
    location = remove_installation()
    if location:
        print('Go removed succesfully from ' + location)
    else:
        print('Go not found')