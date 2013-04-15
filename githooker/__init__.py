#!/usr/bin/env python3
import sys
import os
import re
import shutil
import io
from subprocess import (
    check_output,
    check_call,
    CalledProcessError,
)
from os.path import (
    join,
    abspath,
    relpath,
    basename,
    dirname,
    isfile,
)
from urllib.parse import urlparse
from urllib.request import urlretrieve
import posixpath
from abc import (
    ABCMeta,
    abstractmethod
)

from allfiles import allfiles

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
git hooker test -t {timing} "$@"
'''

def git_dir_path():
    output = check_output(['git', 'rev-parse', '--git-dir'])
    path = output.decode(sys.getfilesystemencoding()).strip()
    return abspath(path)


def create_root_hook_scripts_and_config_files():
    encoding = 'utf-8'
    for timing in timings():
        files = [
            (timing, ROOT_HOOK_TEMPLATE.format(timing=timing)),
            (timing + '.hooks', ''),
        ]
        for filename, content in files:
            filepath = join(git_dir_path(), 'hooks', filename)
            if os.path.exists(filepath):
                continue
            with io.open(filepath, 'w', encoding=encoding) as fp:
                fp.write(content)
