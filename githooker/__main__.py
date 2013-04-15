#!/usr/bin/env python3
from argparse import ArgumentParser
import githooker

def init_main(args):
    githooker.create_root_hook_scripts_and_config_files()


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    p = subparsers.add_parser('init')
    p.set_defaults(func=init_main)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
