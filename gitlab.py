# -*- coding: UTF-8 -*-
import sys
from workflow import web, Workflow3, PasswordNotFound


def get_projects(token, url):
    """
    Parse all pages of projects
    :return: list
    """
    return get_gitlab_repos(url, token, 1, [])


def get_gitlab_repos(url, token, page, result):
    if page == 1:
        url = url.encode('utf-8') + '/projects'
    log.info('Fetching {url} page {page}'.format(url=url, page=page))
    params = dict(private_token=token, per_page=100, page=page)
    r = web.get(url, params)
    r.raise_for_status()
    result = result + r.json()
    next_page = r.headers.get('X-Next-Page')
    if next_page:
        result = get_gitlab_repos(url, token, next_page, result)
    return result


def get_gitlab_issue(url, token, query, page, result):
    if page == 1:
        url = url.encode('utf-8') + '/search?scope=issues&search='+query
    params = dict(private_token=token, per_page=100, page=page)
    r = web.get(url, params)
    r.raise_for_status()
    result = result + r.json()
    next_page = r.headers.get('X-Next-Page')
    if next_page:
        result = get_gitlab_issue(url, token, query, next_page, result)
    return result


def get_gitlab_merge_requests(url, token, page, result):
    if page == 1:
        url = url.encode('utf-8') + '/merge_requests'
    params = dict(private_token=token,
                  per_page=100,
                  page=page,
                  scope='assigned-to-me',
                  state='opened')
    r = web.get(url, params)
    r.raise_for_status()
    result = result + r.json()
    next_page = r.headers.get('X-Next-Page')
    if next_page:
        get_gitlab_merge_requests(url, token, next_page, result)
    return result


def main(wf):
    try:
        gitlab_token = wf.get_password('gitlab_token')
        gitlab_url = wf.get_password('gitlab_url')

        # Retrieve projects from cache if available and no more than 600
        # seconds old
        def wrapper():
            return get_projects(gitlab_token, gitlab_url)

        projects = wf.cached_data('gitlab_projects', wrapper, max_age=3600)
        # log.info('total gitlab projects = ' + str(len(projects)))

        # Record our progress in the log file
        log.debug('{} gitlab projects cached'.format(len(projects)))

    except PasswordNotFound:  # API key has not yet been set
        # Nothing we can do about this, so just log it
        wf.logger.error('No API key saved')


if __name__ == u"__main__":
    wf = Workflow3()
    log = wf.logger
    wf.run(main)
