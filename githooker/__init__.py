#!/usr/bin/env python3
import sys
import os
import re
import shutil
import io
import shlex
from subprocess import (
    check_output,
    check_call,
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
)
from urllib.parse import urlparse
from urllib.request import urlretrieve
import posixpath
from abc import (
    ABCMeta,
    abstractmethod
)

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
    @abstractmethod
    def parse(cls, arg_hook):
        pass

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def install(self, dest_path):
        pass


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
        shutil.copy2(self._path, dest)

    def as_string(self):
        return self._path


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


def all_hooks(timing):
    with io.open(hook_list_file_path(timing), encoding=Encoding) as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            yield parse_hook_string(line)


def update_all_hook_subscripts(timing):
    dir_path = hook_subscripts_dir_path(timing)
    if not isdir(dir_path):
        os.makedirs(dir_path)
    else:
        shutil.rmtree(dir_path)

    for number, hook in enumerate(all_hooks(timing)):
        update_hook_subscript(number, hook, timing)


def update_hook_subscript(number, hook, timing):
    dir_path = hook_subscripts_dir_path(timing)
    if not isdir(dir_path):
        os.makedirs(dir_path)

    path = join(dir_path, '{}-{}'.format(number, hook.name()))
    print('installing {} as {}'.format(hook.name(), path))
    hook.install(path)


def install_hook_subscripts(hook_strings, timing):
    hooks = list(all_hooks(timing))
    new_hooks = []
    for number, hook_string in enumerate(hook_strings, start=len(hooks)):
        new_hook = parse_hook_string(hook_string)
        new_hooks.append(new_hook)

        update_hook_subscript(number, new_hook, timing)

        path = hook_list_file_path(timing)
        with io.open(path, 'a+', encoding=Encoding) as fp:
            line = ''
            for line in fp:
                pass
            if line.endswith('\n'):
                print(file=fp)
            print(new_hook.as_string(), file=fp)


def all_hook_subscript_paths(timing):
    return allfiles(hook_subscripts_dir_path(timing), single_level=True)


def run_test(timing, args):
    for subscript in all_hook_subscript_paths(timing):
        cmd = [subscript] + args
        try:
            check_call(cmd)
        except CalledProcessError as e:
            sys.exit(e.returncode)


def which_editor():
    editor = os.getenv('EDITOR') or os.getenv('VISUAL')
    if editor:
        return shlex.split(editor)
    return ['vi']


def run_edit(timing):
    cmd = which_editor() + [hook_list_file_path(timing)]
    retcode = call(cmd)
    print('Editor exited with code {}'.format(retcode))


def print_hook_list_file(timing):
    with io.open(hook_list_file_path(timing), encoding=Encoding) as fp:
        for line in fp:
            print(line, end='')
