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
    log.info(next_page)
    if next_page:
        result = get_gitlab_repos(url, token, next_page, result)

    return result


def get_gitlab_repo_test(url, token, page):
    url = url + '/projects'
    params = dict(private_token=token, per_page=100, page=page, membership='true')
    r = web.get(url, params)
    # log.info(r.text)
    nextpage = r.headers.get('X-Next-Page')
    log.info(nextpage)
    r.raise_for_status()
    return r.json


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

    if args.token:
        log.info('Setting gitlab token {}'.format(args.token))
        wf.save_password('gitlab_token', args.token)
        return 0

    if args.url:
        log.info('Setting gitlab url {}'.format(args.url))
        wf.save_password('gitlab_url', args.url)
        return 0

    gitlab_token = wf.get_password('gitlab_token')
    gitlab_url = wf.get_password('gitlab_url')

    log.info(gitlab_token)
    log.info(gitlab_url)

    results = get_gitlab_repos(gitlab_url, gitlab_token, 1, [])
    # results = get_gitlab_repo_test(gitlab_url, gitlab_token, 1)
    log.info('total = ' + str(len(results)))


if __name__ == u"__main__":
    wf = Workflow3(update_settings={
        'github_slug': 'lukewaite/alfred-gitlab',
    })
    log = wf.logger
    sys.exit(wf.run(main))