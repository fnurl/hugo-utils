# hugo-utils
Utility scripts for [Hugo](https://gohugo.io).

## docsearch-pageindexer.py

Converts the markdown content into plain text. Requires [`mistune`](https://github.com/lepture/mistune) for markdown parsing and [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/).

## update-lastmod.py

Updates the `lastmod` frontmatter value to the current date and time. Parses `stdio` or accepts a single filepath as an argument.

## watch-lastmod.sh

Watches a directory for any changes in `.md` files. Defaults to watch `./content/` if no argument is supplied. When a file update is detected, it calls `update-lastmod.py` to update the `lastmod` of that file.

Requires `fswatch`. Install e.g. using homebrew: `brew install fswatch`. 
