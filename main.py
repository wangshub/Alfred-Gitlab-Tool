# encoding: utf-8
from os import sys, path
import sys
import argparse
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
    wf.add_item(title='Open issues in browser',
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
    log.info('total projects = ' + str(len(projects)))

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
        wf.add_item(title=proj['name_with_namespace'],
                    subtitle=proj['path_with_namespace'],
                    arg=proj['web_url'],
                    valid=True,
                    icon=None,
                    uid=proj['id'])
    wf.send_feedback()


def main(wf):
    # command line parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', dest='token', nargs='?', default=None)
    parser.add_argument('--url', dest='url', nargs='?', default=None)
    parser.add_argument('--repo', dest='repo', nargs='?', default=None)
    parser.add_argument('--issue', dest='issue', nargs='?', default=None)
    parser.add_argument('--merge', dest='merge', nargs='?', default=None)
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


if __name__ == u"__main__":
    wf = Workflow3()
    log = wf.logger
    sys.exit(wf.run(main))