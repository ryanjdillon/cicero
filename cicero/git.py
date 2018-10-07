import os
import flask
import sys
import requests
import json

blueprint = flask.Blueprint('git', __name__)

URL_BASE = 'CICERO_URL_BASE_is_undefined'
_url_base = os.environ.get('CICERO_URL_BASE')
if _url_base is not None:
    URL_BASE = _url_base


def get_sha_github(owner, repo, ref):
    uri = 'https://api.github.com/repos/{0}/{1}/commits/{2}'.format(owner, repo, ref)
    response = requests.get(uri)
    data = json.loads(response.text)
    return data['sha']


def test_get_sha_github():
    is_travis_build = os.getenv('TRAVIS', False)
    # Travis CI is rate-limited by GitHub API
    if not is_travis_build:
        sha = get_sha_github('bast', 'cicero', 'bfa3748447')
        assert sha == 'bfa3748447fe0c7455f19a027575406a0c561a4f'


def set_url_base(host, port):
    global URL_BASE
    URL_BASE = 'http://{}:{}'.format(host, port)


@blueprint.route('/')
def home():
    return flask.render_template('index.html', url_base=URL_BASE)


def render_github_markdown(path, engine, engine_version):
    from .title import extract_title
    from .images import fix_images

    file_path = '/'.join(path.split('/')[4:])
    if '/' in file_path:
        last_file = file_path.split('/')[-1]
    else:
        last_file = file_path

    (service, owner, repo, ref) = path.split('/')[0:4]

    if service == 'github.com':
        # we need to translate the reference to a sha (the reference can be a sha)
        # the reason for this is that cdn.rawgit.com caches files forever
        # the reference may change but the sha won't
        sha = get_sha_github(owner, repo, ref)

        root = '{0}/{1}/{2}'.format(owner, repo, sha)
        if '/' in file_path:
            root += '/' + '/'.join(file_path.split('/')[:-1]) + '/'

        prefix = 'https://cdn.rawgit.com/{0}/'.format(root)
    else:
        prefix = 'https://{0}/{1}/{2}/raw/{3}/'.format(service, owner, repo, ref)

    url = prefix + '/' + last_file

    response = requests.get(url)
    if response.status_code == 404:
        return flask.render_template('404.html')

    markdown = response.text

    title = extract_title(markdown)
    style = flask.request.args.get('style')
    if style is None:
        style = 'default'

    file_without_suffix, _suffix = os.path.splitext(last_file)

    # if own css is available, we load it
    # if not, we default to empty own css
    url = prefix + '/' + file_without_suffix + '.css'
    response = requests.get(url)
    if response.status_code == 404:
        own_css = ''
    else:
        own_css = response.text
        own_css = flask.Markup(own_css)  # disable autoescaping

    # .. do the same for own javascript
#   url = prefix + '/' + file_without_suffix + '.js'
#   response = requests.get(url)
#   if response.status_code == 404:
#       own_javascript = ''
#   else:
#       own_javascript = response.text
    # for the moment I am not sure whether the above is not too risky
    own_javascript = ''

    # use custom configuration for the rendering engine, if available
    url = prefix + '/' + file_without_suffix + '.conf'
    response = requests.get(url)
    if response.status_code == 404:
        own_conf = ''
    else:
        own_conf = ',\n'.join(response.text.split('\n'))

    return flask.render_template('render.html',
                                 title=title,
                                 markdown=fix_images(markdown, prefix),
                                 style=style,
                                 own_css=own_css,
                                 own_javascript=own_javascript,
                                 own_conf=own_conf,
                                 engine='{0}-{1}'.format(engine, engine_version))


@blueprint.route('/v1/github/<path:path>/remark/')
def render_v1(path):
    return render_github_markdown('github.com' + '/' + path, 'remark', '0.13.0')


@blueprint.route('/v2/remark/github/<path:path>/')
def render_v2(path):
    return render_github_markdown('github.com' + '/' + path, 'remark', '0.13.0')


@blueprint.route('/v3/<string:engine>/<string:engine_version>/<path:path>/')
def render_v3(path, engine, engine_version):
    return render_github_markdown(path, engine, engine_version)
