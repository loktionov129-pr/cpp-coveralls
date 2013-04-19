# Copyright 2013 (c) Lei Xu <eddyxu@gmail.com>

import os
import subprocess
from coveralls import gitrepo


def is_source_file(filepath):
    """Returns true if it is a C++ source file
    """
    return os.path.splitext(filepath)[1] in ['.h', '.hpp', '.cpp', '.cc', '.c']


def exclude_paths(args):
    """Returns the absolute paths for excluded path.
    """
    results = []
    if args.exclude:
        for excl_path in args.exclude + ['.git', '.svn']:
            results.append(os.path.abspath(os.path.join(args.root, excl_path)))
    return results


def run_gcov(args):
    excl_paths = exclude_paths(args)
    for root, dirs, files in os.walk(args.root):
        filtered_dirs = []
        for dirpath in dirs:
            abspath = os.path.abspath(os.path.join(root, dirpath))
            if not abspath in excl_paths:
                filtered_dirs.append(dirpath)
        dirs[:] = filtered_dirs
        for filepath in files:
            basename, ext = os.path.splitext(filepath)
            if ext == '.gcno':
                subprocess.call('cd %s && %s %s' % (root, args.gcov, basename),
                                shell=True)


def collect(args):
    """Collect coverage reports.
    """
    excl_paths = exclude_paths(args)

    report = {}
    report['service_name'] = args.service_name
    report['service_job_id'] = args.service_job_id
    report['source_files'] = []
    for root, dirs, files in os.walk(args.root):
        filtered_dirs = []
        for dirpath in dirs:
            abspath = os.path.abspath(os.path.join(root, dirpath))
            if not abspath in excl_paths:
                filtered_dirs.append(dirpath)
        dirs[:] = filtered_dirs

        for filepath in files:
            if is_source_file(filepath):
                src_path = os.path.relpath(os.path.join(root, filepath),
                                           args.root)
                gcov_path = src_path + '.gcov'
                src_report = {}
                src_report['name'] = src_path
                with open(src_path) as fobj:
                    src_report['source'] = fobj.read()

                coverage = []
                if os.path.exists(gcov_path):
                    with open(gcov_path) as fobj:
                        for line in fobj:
                            report_fields = line.split(':')
                            cov_num = report_fields[0].strip()
                            line_num = int(report_fields[1].strip())
                            text = report_fields[2]
                            if line_num == 0:
                                continue
                            if cov_num == '-':
                                coverage.append(None)
                            elif cov_num == '#####':
                                # Avoid false positives.
                                if text.lstrip().startswith('static'):
                                    coverage.append(None)
                                else:
                                    coverage.append(0)
                            else:
                                coverage.append(int(cov_num))
                src_report['coverage'] = coverage
                report['source_files'].append(src_report)
    report['git'] = gitrepo.gitrepo('.')
    return report
