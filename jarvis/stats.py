#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pyscp
import textwrap

from . import core


###############################################################################
# Templates
###############################################################################


CHART = """
google.charts.setOnLoadCallback({name});

function {name}() {{
    var data = new google.visualization.arrayToDataTable([
{data}
        ]);

    var options = {options};

    var chart = new google.visualization.{class_name}(
        document.getElementById('{name}'));

    chart.draw(data, options);
}}
"""

USER = """
[[html]]
<base target="_parent" />

<style type="text/css">
@import url(http://scp-stats.wdfiles.com/local--theme/scp-stats/style.css);
</style>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js">
</script>

<script type="text/javascript">
google.charts.load('current', {{'packages':['table', 'corechart']}});
{articles_chart}
{articles_table}
</script>

<div id="articles_chart"></div>
<div style="clear: both;"></div>
<h2>Articles</h2>
<div id="articles_table"></div>

[[/html]]
"""

###############################################################################
# Helper Functions
###############################################################################


def html(tag, text, **kwargs):
    if 'cls' in kwargs:
        kwargs['class'] = kwargs.pop('cls')
    attrs = ' '.join('{}="{}"'.format(k, v) for k, v in kwargs.items())
    if attrs:
        attrs = ' ' + attrs
    return '<{tag}{attrs}>{text}</{tag}>'.format(
        tag=tag, text=text, attrs=attrs)

###############################################################################
# Chart Classes
###############################################################################


class Chart:

    def __init__(self, pages):
        for p in pages:
            self.add_page(p)

    def format_row(self, row, indent):
        row = ',\n'.join(map(repr, row))
        row = textwrap.indent(row, '    ')
        row = '[\n{}\n]'.format(row)
        return textwrap.indent(row, ' ' * indent)

    def render(self):
        data = ',\n'.join([self.format_row(r, 8) for r in self.data])
        return CHART.format(
            name=self.name,
            class_name=self.class_name,
            data=data,
            options=self.options)


class ArticlesChart(Chart):

    def __init__(self, pages):
        self.name = 'articles_chart'
        self.class_name = 'ColumnChart'
        self.data = [
            ['Title', 'Rating', {'role': 'tooltip'}, {'role': 'style'}]]
        self.options = {}
        super().__init__(pages)

    def add_page(self, page):
        if 'scp' in page.tags:
            color = 'color: #db4437'
        elif 'tale' in page.tags:
            color = 'color: #4285f4'
        else:
            color = 'color: #f4b400'

        self.data.append([
            page.title,
            page.rating,
            page.created[:10],
            color])


class ArticlesTable(Chart):

    def __init__(self, pages, user):
        self.name = 'articles_table'
        self.class_name = 'Table'
        self.user = user
        self.data = ['Title Rating Tags Link Created Relation'.split()]
        self.options = {
            'showRowNumber': 'True',
            'allowHtml': 'True',
            'sortColumn': 1,
            'width': '100%'}
        super().__init__(pages)

    def add_page(self, page):
        tags = [html('b', t) if t in 'scp tale hub admin author' else t
                for t in page.tags]
        tags = ', '.join(sorted(tags))

        link = html('a', page.url.split('/')[-1], href=page.url)

        rel = page.metadata[self.user][0]
        rel = html('span', rel, cls='rel-' + rel)

        self.data.append([
            page.title, page.rating, tags, link, page.created[:10], rel])


###############################################################################


def update_user(name):
    wiki = pyscp.wikidot.Wiki('scp-stats')
    wiki.auth(core.config['wiki']['name'], core.config['wiki']['pass'])
    p = wiki('user:' + name.lower())

    pages = core.pages.related(name).articles
    pages = sorted(pages, key=lambda x: x.created)
    data = USER.format(
        articles_chart=ArticlesChart(pages).render(),
        articles_table=ArticlesTable(pages, name).render())

    p.create(data, title=name, comment='automated update')
    return p.url
