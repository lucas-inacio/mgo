#!/usr/bin/python3
from commands import *

def run():
    parser = build_parser()

    # Execute commands
    args = parser.parse_args()
    if args.cmd == 'status':
        status_command()
    elif args.cmd == 'check':
        check_command(args.preview)
    elif args.cmd == 'update':
        update_command(args.preview)
    elif args.cmd == 'install':
        install_command(args.path, args.version, args.preview)
    elif args.cmd == 'available':
        available_command(args.count)
    elif args.cmd == 'uninstall':
        uninstall_command()
    else:
        parser.print_help()

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print('Operation cancelled')
    except FileNotFoundError:
        print('Go not found')