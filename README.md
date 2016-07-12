# hugo-utils
Utility scripts for [Hugo](https://gohugo.io).

## docsearch-pageindexer.py

Converts the markdown content into plain text. Requires [`mistune`](https://github.com/lepture/mistune) for markdown parsing and [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/).

## update-lastmod.py

Updates the `lastmod` frontmatter value to the current date and time. Parses stdio or accepts a single filepath as an argument.