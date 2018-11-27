# -*- coding: UTF-8 -*-
from os import sys, path
import sys
import argparse
from gitlab import get_gitlab_issue, get_gitlab_merge_requests
from workflow import Workflow3, ICON_WEB, ICON_WARNING, ICON_INFO, web, PasswordNotFound
from workflow.background import run_in_background, is_running

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

log = None


def search_for_project(project):
    """Generate a string search key for a project"""
    elements = []
    elements.append(project['name_with_namespace'])
    elements.append(project['path_with_namespace'])
    return u' '.join(elements)


def save_gitlab_token(wf, token):
    """
    save gitlab token
    :param wf:
    :param token:
    :return:
    """
    log.info('Setting gitlab token {}'.format(token))
    wf.save_password('gitlab_token', token)


def save_gitlab_url(wf, url):
    """
    save gitlab url
    :param wf:
    :param url:
    :return:
    """
    log.info('Setting gitlab url {}'.format(url))
    wf.save_password('gitlab_url', url)


def open_gitlab_todo(wf):
    """
    open gitlab todos url in default browser
    :param wf:
    :return:
    """
    url_todo = wf.get_password('gitlab_url').replace('/api/v4', '') + '/dashboard/todos'
    wf.add_item(title='Open gitlab todo in default browser',
                arg=url_todo,
                valid=True,
                icon=None)
    wf.send_feedback()


def search_gitlab_repo(wf, query):
    """
    search repo from cached data
    :param wf:
    :param query:
    :return:
    """
    projects = wf.cached_data('gitlab_projects', max_age=0)

    # update gitlab api data
    if not wf.cached_data_fresh('gitlab_projects', max_age=3600) and not is_running('gitlab_update'):
        cmd = ['/usr/bin/python', wf.workflowfile('gitlab.py')]
        run_in_background('gitlab_update', cmd)
        wf.rerun = 0.

    if query and projects:
        projects = wf.filter(query, projects, key=search_for_project, min_score=20)

    if not projects:
        wf.add_item('No projects found', icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    for proj in projects:
        if proj['issues_enabled']:
            subtitle = "issue:{0: <3} star:{1: <3} fork:{2: <3}".format(proj['open_issues_count'],
                                                                    proj['star_count'],
                                                                    proj['forks_count'])
        else:
            subtitle = ""
        wf.add_item(title=proj['name_with_namespace'],
                    subtitle=subtitle,
                    arg=proj['web_url'],
                    valid=True,
                    icon=None,
                    uid=proj['id'])
    wf.send_feedback()


def query_gitlab_issue(wf, query):
    """
    query gitlab issues
    :param wf:
    :param query:
    :return:
    """
    query = query.encode('utf-8')
    gitlab_token = wf.get_password('gitlab_token')
    gitlab_url = wf.get_password('gitlab_url')
    issues = get_gitlab_issue(gitlab_url, gitlab_token, query, 1, [])

    if not issues:
        wf.add_item('No issues found', icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    for issue in issues:
        wf.add_item(title=issue['title'],
                    subtitle=issue['description'],
                    arg=issue['web_url'],
                    valid=True,
                    icon=None,
                    uid=issue['id'])
    wf.send_feedback()


def get_gitlab_mr_assigned(wf):
    gitlab_token = wf.get_password('gitlab_token')
    gitlab_url = wf.get_password('gitlab_url')
    merges = get_gitlab_merge_requests(gitlab_url, gitlab_token, 1, [])
    if not merges:
        wf.add_item('No issues found', icon=ICON_WARNING)
        wf.send_feedback()
        return 0
    for merge in merges:
        title =merge['title'] + ' by ' + merge['author']['username']
        wf.add_item(title,
                    subtitle=merge['description'],
                    arg=merge['web_url'],
                    valid=True,
                    icon=None,
                    uid=merge['id'])
    wf.send_feedback()


def main(wf):
    # command line parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', dest='token', nargs='?', default=None)
    parser.add_argument('--url', dest='url', nargs='?', default=None)
    parser.add_argument('--repo', dest='repo', nargs='?', default=None)
    parser.add_argument('--issue', dest='issue', nargs='?', default=None)
    parser.add_argument('--merge', dest='merge', action='store_true', default=False)
    parser.add_argument('--todo', dest='todo', action='store_true', default=False)
    parser.add_argument('query', nargs='?', default=None)
    args = parser.parse_args(wf.args)
    log.info(args)

    if args.token:
        save_gitlab_token(wf, args.token)
        return 0

    if args.url:
        save_gitlab_url(wf, args.url)
        return 0

    if args.todo:
        open_gitlab_todo(wf)
        return 0

    if args.repo:
        search_gitlab_repo(wf, args.repo)
        return 0

    if args.issue:
        query_gitlab_issue(wf, args.issue)
        return 0

    if args.merge:
        get_gitlab_mr_assigned(wf)
        return 0


if __name__ == u"__main__":
    wf = Workflow3()
    log = wf.logger
    sys.exit(wf.run(main))