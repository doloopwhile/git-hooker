#!/usr/bin/env python3
import sys
import os
import re
import shutil
import io
import types
import shlex
from subprocess import (
    check_output,
    call,
    CalledProcessError,
)
from os.path import (
    join,
    abspath,
    relpath,
    basename,
    dirname,
    isfile,
    isdir,
    getmtime,
)
from urllib.parse import urlparse
from urllib.request import urlretrieve
import posixpath
from abc import (
    ABCMeta,
    abstractmethod
)
from argparse import ArgumentParser

import requests
from allfiles import allfiles
Encoding = 'utf-8'


def timings():
    return '''
        applypatch-msg
        pre-applypatch
        post-applypatch
        pre-commit
        prepare-commit-msg
        commit-msg
        post-commit
        pre-rebase
        post-checkout
        post-merge
        pre-receive
        update
        post-update
        pre-auto-gc
        post-rewrite
    '''.split()

ROOT_HOOK_TEMPLATE = '''\
#!/bin/sh
git hooker test {timing} "$@"
'''


def git_dir_path():
    output = check_output(['git', 'rev-parse', '--git-dir'])
    path = output.decode(sys.getfilesystemencoding()).strip()
    return abspath(path)


def git_hooks_dir_path():
    return join(git_dir_path(), 'hooks')


def hook_root_script_path(timing):
    return join(git_dir_path(), 'hooks', timing)


def hook_list_file_path(timing):
    return join(git_dir_path(), 'hooks', timing + '.hooks')


def hook_subscripts_dir_path(timing):
    return join(git_hooks_dir_path(), timing + '.installed')


class HookParseError(ValueError):
    def __init__(self, hook_class, hook_str):
        super().__init__(hook_class, hook_str)
        self._hook_class = hook_class
        self._hook_str = hook_str


class AbstractHook(metaclass=ABCMeta):
    def __init__(self):
        self._options = {}

    @abstractmethod
    def parse(cls, arg_hook):
        pass

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def install(self, dest_path):
        pass

    def set_option(self, key, value):
        self._options[key] = value

    def get_option(self, key, default=None):
        return self._options.get(key, default)


class AbstractWebHook(AbstractHook):
    @abstractmethod
    def _url(self):
        pass

    def install(self, dest_path):
        res = requests.get(self._url())
        with io.open(dest_path, 'wb') as fp:
            fp.write(res.content)
        os.chmod(dest_path, 0o755)


class GistHook(AbstractWebHook):
    def __init__(self, number):
        super().__init__()
        self._number = number

    @classmethod
    def parse(cls, hook_str):
        m = re.match(r'gist:(\d+)', hook_str, re.I)
        if m is None:
            raise HookParseError(cls, hook_str)
        return cls(int(m.group(1)))

    def name(self):
        return "gist-{}".format(self._number)

    def _url(self):
        return "https://raw.github.com/gist/{}".format(self._number)

    def as_string(self):
        return "gist:{}".format(self._number)


class UrlHook(AbstractWebHook):
    def __init__(self, url):
        super().__init__()
        self._url_str = url

    @classmethod
    def parse(cls, hook_str):
        m = re.match(r'http://|https://', hook_str, re.I)
        if m is None:
            raise HookParseError(cls, hook_str)
        return cls(hook_str)

    def name(self):
        return posixpath.basename(urlparse(self._url()).path)

    def _url(self):
        return self._url_str

    def as_string(self):
        return self._url_str


class FileHook(AbstractHook):
    def __init__(self, path):
        super().__init__()
        self._path = path

    @classmethod
    def parse(cls, arg_hook):
        return cls(arg_hook)

    def name(self):
        return basename(self._path)

    def install(self, dest):
        if self.get_option('link'):
            os.symlink(self._path, dest)
        else:
            shutil.copy2(self._path, dest)
            os.chmod(dest, 0o755)

    def as_string(self):
        return '{} --link'.format(self._path)


def parse_hook_string(hook_str):
    for klass in [GistHook, UrlHook]:
        try:
            return klass.parse(hook_str)
        except HookParseError:
            pass
    return FileHook.parse(hook_str)


def create_root_hook_scripts_and_config_files():
    for timing in timings():
        root_hook = ROOT_HOOK_TEMPLATE.format(timing=timing)
        files = [
            (hook_root_script_path(timing), root_hook, 0o755),
            (hook_list_file_path(timing), '', 0o655),
        ]
        for filename, content, flags in files:
            filepath = join(git_hooks_dir_path(), filename)
            if os.path.exists(filepath):
                continue
            with io.open(filepath, 'w', encoding=Encoding) as fp:
                fp.write(content)
            os.chmod(filepath, flags)


class HooksFileParsingError(Exception):
    def __init__(self, msg, line_string, line_number):
        self._msg = msg
        self._line_string = line_string
        self._line_number = line_number
        super().__init__(msg, line_string, line_number)

    def __str__(self):
        return '{}: At line {}: {}'.format(
            self._msg,
            self._line_number,
            repr(self._line_string),
        )


def singletonmethod(obj):
    """
    >>> class A(object): pass
    >>> a = A()
    >>> @singletonmethod(a)
    ... def hello(self):
    ...     print "hello world!"
    >>> a.hello()
    hello world!
    >>> type(a.hello)

    """
    def _singletonmethod(function):
        method = types.MethodType(function, obj)
        setattr(obj, function.__name__, method)
        return function
    return _singletonmethod


def parse_hook_list_file_line(line, line_number):
    argv = shlex.split(line, True)
    parser = ArgumentParser()
    parser.add_argument('hook_string', action='store')
    parser.add_argument('--link', action='store_true')

    @singletonmethod(parser)
    def error(self, msg):
        raise HooksFileParsingError(msg, line, line_number)

    args = parser.parse_args(argv)
    hook = parse_hook_string(args.hook_string)
    hook.set_option('link', args.link)
    return hook


def all_hooks(timing):
    with io.open(hook_list_file_path(timing), encoding=Encoding) as fp:
        for line_number, line in enumerate(fp, start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            yield parse_hook_list_file_line(line, line_number)


def update_all_hook_subscripts(timing):
    hooks = list(all_hooks(timing))

    dir_path = hook_subscripts_dir_path(timing)
    if not isdir(dir_path):
        os.makedirs(dir_path)
    else:
        shutil.rmtree(dir_path)

    for number, hook in enumerate(hooks):
        update_hook_subscript(number, hook, timing)


def update_hook_subscript(number, hook, timing):
    dir_path = hook_subscripts_dir_path(timing)
    if not isdir(dir_path):
        os.makedirs(dir_path)

    path = join(dir_path, '{}-{}'.format(number, hook.name()))
    if os.path.exists(path):
        os.remove(path)

    print('installing {} as {}'.format(hook.name(), path))
    hook.install(path)


def install_hook_subscripts(hook_strings, timing, link, comment):
    hooks = list(all_hooks(timing))
    for number, hook_string in enumerate(hook_strings, start=len(hooks)):
        new_hook = parse_hook_string(hook_string)
        new_hook.set_option('link', link)

        update_hook_subscript(number, new_hook, timing)

        path = hook_list_file_path(timing)
        with io.open(path, 'a+', encoding=Encoding) as fp:
            line = ''
            for line in fp:
                pass
            if line.endswith('\n'):
                print(file=fp)
            print(new_hook.as_string() + ' # ' + comment, file=fp)


def all_hook_subscript_paths(timing):
    return allfiles(hook_subscripts_dir_path(timing), single_level=True)


def run_test(timing, args):
    exit_codes = []
    for subscript in all_hook_subscript_paths(timing):
        cmd = [subscript] + args
        exit_codes.append(call(cmd))
    if any([c != 0 for c in exit_codes]):
        sys.exit(1)


def which_editor():
    editor = os.getenv('EDITOR') or os.getenv('VISUAL')
    if editor:
        return shlex.split(editor)
    return ['vi']


def run_edit(timing, update_after_edit):
    path = hook_list_file_path(timing)
    try:
        prev_mtime = getmtime(path)
    except OSError:
        prev_mtime = 0

    cmd = which_editor() + [path]
    retcode = call(cmd)
    print('Editor exited with code {}'.format(retcode))

    if retcode != 0:
        return

    if not update_after_edit:
        return

    try:
        curr_mtime = getmtime(path)
    except OSError:
        return

    if prev_mtime < curr_mtime:
        update_all_hook_subscripts(timing=timing)


def print_hook_list_file(timing):
    with io.open(hook_list_file_path(timing), encoding=Encoding) as fp:
        for line in fp:
            print(line, end='')
