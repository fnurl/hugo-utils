# hugo-utils
Utility scripts for [Hugo](https://gohugo.io).

## docsearch-pageindexer.py

Creates a JSON index file to be used with [algolia/docsearch](https://github.com/algolia/docsearch) without your site being crawled by Algolia. This is handy when you are working on an unpublished site (e.g. localhost).

Only `.md` files are indexed. Use the `-t` flag to set which taxonomies you want to use as "tags" in the index. Markdown content is converted into plain text and stripped from shortcodes.

The script does not create individual index entries for headings etc., so when in production, it is probably better to use Algolia's own crawler to create the site index. 

Requires [`mistune`](https://github.com/lepture/mistune) for markdown parsing and [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/).

### Settings to set on your algolia index

- Indices > Display > Display & Pagination > Attributes to snippet: content (choose how many words)

Changeing which attributes to index might break `docsearch` as you might miss something it needs.

## update-lastmod.py

Updates the `lastmod` frontmatter value to the current date and time. Parses `stdio` or accepts a single filepath as an argument.

## watch-lastmod.sh

Watches a directory for any changes in `.md` files. Defaults to watch `./content/` if no argument is supplied. When a file update is detected, it calls `update-lastmod.py` to update the `lastmod` of that file.

Requires `fswatch`. Install e.g. using homebrew: `brew install fswatch`. 
