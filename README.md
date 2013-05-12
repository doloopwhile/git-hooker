git-hooker
==========
Yet another simple command to manage git hook scripts.

Install
-------
git-hooker requires Git, Python >= 3.2 and virtualenvwrapper.

    $ mkvirtualenv -p python3.2 git-hooker
    $ git clone git://github.com/doloopwhile/git-hooker.git ~/.git-hooker
    $ cd ~/. git-hooker
    $ workon git-hooker
    $ python setup.py install
    $ echo 'export PATH="$HOME/.git-hooker/bin:$PATH"' >> ~/.bash_profile

Upgrade
-------

    $ git pull --git-dir ~/.git-hooker

Usage
-----
### initialize git repository to use git-hooker
    $ git hooker init

### install hook
    $ git hooker install pre-commit http://example.com/hook.sh # script on web
    $ git hooker install pre-rebase gist:0000 # gist
    $ git hooker install post-commit /path/to/your-hook # local script

### list hooks
    $ git hooker show pre-commit

### uninstall hook
    $ git hooker edit pre-commit
    text editor is opened...
    edit to delete the hook...

### test hook script
    $ git hooker test pre-commit args-for-hook-scripts

Lisence
-------
(The MIT License)

Copyright (c) 2013 OMOTO Kenji

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
