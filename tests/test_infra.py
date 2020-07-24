# Copyright 2020 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For further info, check https://github.com/canonical/charmcraft

import io
import itertools
import os
import re
import subprocess
from unittest.mock import patch

import pytest
from flake8.api.legacy import get_style_guide

from charmcraft import __version__

FLAKE8_OPTIONS = {'max_line_length': 99, 'select': ['E', 'W', 'F', 'C', 'N']}


def get_python_filepaths(*, roots=None, python_paths=None):
    """Helper to retrieve paths of Python files."""
    if python_paths is None:
        python_paths = ['setup.py']
    if roots is None:
        roots = ['charmcraft', 'tests']
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if filename.endswith(".py"):
                    python_paths.append(os.path.join(dirpath, filename))
    return python_paths


def test_pep8():
    """Verify all files are nicely styled."""
    pep8_test(get_python_filepaths())


def pep8_test(python_filepaths):
    style_guide = get_style_guide(**FLAKE8_OPTIONS)
    fake_stdout = io.StringIO()
    with patch('sys.stdout', fake_stdout):
        report = style_guide.check_files(python_filepaths)

    # if flake8 didnt' report anything, we're done
    if report.total_errors == 0:
        return

    # grab on which files we have issues
    flake8_issues = fake_stdout.getvalue().split('\n')

    if flake8_issues:
        msg = "Please fix the following flake8 issues!\n" + "\n".join(flake8_issues)
        pytest.fail(msg, pytrace=False)


def test_ensure_copyright():
    """Check that all non-empty Python files have copyright somewhere in the first 5 lines."""
    issues = []
    regex = re.compile(r"# Copyright \d{4}(-\d{4})? Canonical Ltd.$")
    for filepath in get_python_filepaths():
        if os.stat(filepath).st_size == 0:
            continue

        with open(filepath, "rt", encoding="utf8") as fh:
            for line in itertools.islice(fh, 5):
                if regex.match(line):
                    break
            else:
                issues.append(filepath)
    if issues:
        msg = "Please add copyright headers to the following files:\n" + "\n".join(issues)
        pytest.fail(msg, pytrace=False)


def test_setup_version():
    """Verify that setup.py is picking up the version correctly."""
    cmd = [os.path.abspath('setup.py'), '--version']
    proc = subprocess.run(cmd, stdout=subprocess.PIPE)
    output = proc.stdout.decode('utf8')
    assert output.strip() == __version__
