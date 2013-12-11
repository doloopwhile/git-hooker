#!/usr/bin/env python3
from argparse import ArgumentParser, REMAINDER
import githooker


def init_main(args):
    githooker.create_root_hook_scripts_and_config_files()


def update_main(args):
    githooker.update_all_hook_subscripts(timing=args.timing)


def install_main(args):
    githooker.install_hook_subscripts(
        args.hook_string,
        timing=args.timing,
        link=args.link,
        comment=args.comment,
    )


def test_main(args):
    githooker.run_test(
        timing=args.timing,
        args=args.test_args,
        skip_in_rebase=githooker.get_git_config_bool('skipinrebase'),
    )


def edit_main(args):
    githooker.run_edit(
        timing=args.timing,
        update_after_edit=args.update,
    )


def show_main(args):
    githooker.print_hook_list_file(timing=args.timing)


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    p = subparsers.add_parser('init')
    p.set_defaults(func=init_main)

    p = subparsers.add_parser('update')
    p.add_argument('timing', action='store', choices=githooker.timings())
    p.set_defaults(func=update_main)

    p = subparsers.add_parser('install')
    p.add_argument('timing', action='store', choices=githooker.timings())
    p.add_argument(
        '--link',
        action='store_true',
        help='Create symbolic link instead of copy to install a local script'
    )
    p.add_argument(
        '--comment',
        action='store',
        help='Comment for the hooks on hooklist file'
    )
    p.add_argument('hook_string', action='store', nargs='+')
    p.set_defaults(func=install_main)

    p = subparsers.add_parser('test')
    p.add_argument('timing', action='store', choices=githooker.timings())
    p.add_argument('test_args', nargs=REMAINDER)
    p.set_defaults(func=test_main)

    p = subparsers.add_parser('edit')
    p.add_argument('timing', action='store', choices=githooker.timings())
    p.add_argument('--update', action='store_true', dest='update')
    p.add_argument('--no-update', action='store_false', dest='update')
    p.set_defaults(func=edit_main, update=True),

    p = subparsers.add_parser('show')
    p.add_argument('timing', action='store', choices=githooker.timings())
    p.set_defaults(func=show_main)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
