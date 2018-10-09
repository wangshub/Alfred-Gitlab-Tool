# encoding: utf-8
from os import sys, path
import sys
import argparse
from workflow import Workflow3, ICON_WEB, ICON_WARNING, ICON_INFO, web, PasswordNotFound
from workflow.background import run_in_background, is_running

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
# from lib import gitlab


log = None


def get_gitlab_repos(url, token, page, result):
    if page == 1:
        url = url + '/projects'
    log.info('Fetching {url} page {page}'.format(url=url, page=page))
    params = dict(private_token=token, per_page=100, page=page)
    r = web.get(url, params)
    r.raise_for_status()
    result = result + r.json()
    next_page = r.headers.get('X-Next-Page')
    if next_page:
        result = get_gitlab_repos(url, token, next_page, result)
    return result


def search_for_project(project):
    """Generate a string search key for a project"""
    elements = []
    elements.append(project['name_with_namespace'])
    elements.append(project['path_with_namespace'])
    return u' '.join(elements)


def main(wf):
    # command line parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', dest='token', nargs='?', default=None)
    parser.add_argument('--url', dest='url', nargs='?', default=None)
    parser.add_argument('--repo', dest='repo', nargs='?', default=None)
    parser.add_argument('--issue', dest='issue', nargs='?', default=None)
    parser.add_argument('--merge', dest='merge', nargs='?', default=None)
    parser.add_argument('--todo', dest='todo', nargs='?', default=None)
    parser.add_argument('query', nargs='?', default=None)
    args = parser.parse_args(wf.args)
    log.info(args)

    query = args.query

    if args.token:
        log.info('Setting gitlab token {}'.format(args.token))
        wf.save_password('gitlab_token', args.token)
        return 0

    if args.url:
        log.info('Setting gitlab url {}'.format(args.url))
        wf.save_password('gitlab_url', args.url)
        return 0

    # gitlab_token = wf.get_password('gitlab_token')
    # gitlab_url = wf.get_password('gitlab_url')
    # projects = get_gitlab_repos(gitlab_url, gitlab_token, 1, [])

    projects = wf.cached_data('gitlab_projects', max_age=0)
    log.info('total projects = '+str(len(projects)))

    # update gitlab api data
    if not wf.cached_data_fresh('gitlab_projects', max_age=3600) and not is_running('gitlab_update'):
        cmd = ['/usr/bin/python', wf.workflowfile('update.py')]
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


if __name__ == u"__main__":
    wf = Workflow3(update_settings={
        'github_slug': 'lukewaite/alfred-gitlab',
    })
    log = wf.logger
    sys.exit(wf.run(main))