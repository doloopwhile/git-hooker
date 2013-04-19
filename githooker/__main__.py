#!/usr/bin/env python3
from argparse import ArgumentParser, REMAINDER
import githooker

def init_main(args):
    githooker.create_root_hook_scripts_and_config_files()


def install_main(args):
    githooker.install_hook_subscripts(timing=args.timing)


def test_main(args):
    githooker.run_test(timing=args.timing, args=args.test_args)


def edit_main(args):
    githooker.run_edit(timing=args.timing)


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    p = subparsers.add_parser('init')
    p.set_defaults(func=init_main)

    p = subparsers.add_parser('install')
    p.add_argument('timing', action='store')
    p.set_defaults(func=install_main)

    p = subparsers.add_parser('test')
    p.add_argument('timing', action='store')
    p.add_argument('test_args', nargs=REMAINDER)
    p.set_defaults(func=test_main)

    p = subparsers.add_parser('edit')
    p.add_argument('timing', action='store')
    p.set_defaults(func=edit_main)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
