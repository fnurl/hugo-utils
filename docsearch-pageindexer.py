#!/usr/bin/env python3

import os
import sys
import argparse
import re
import yaml
import json
from mistune import markdown
from bs4 import BeautifulSoup


# The attribute mapping for docsearch.
# The 'tags' mapping's value will be a list, so multiple list attributes can be
# aggregated into the docsearch `tags` attribute.
#
# Note: The 'tags' mapping will be overwritten by command line arguments. See bottom
# of file.
docsearch_mapping = { "content": "content",
                      "url": "url",
                      "tags": ["tags", "categories"]
                    }

# Default weighting of pages.
docsearch_weight = { "position": 1,
                     "level": 10,
                     "page_rank": 0
                    }

def parse_md(filepath):
    """Parse a Hugo markdown file with YAML frontmatter. Removes shortcodes."""

    yaml_string = ""
    in_yaml = None
    markdown_content = ""
    with open(filepath) as datafile:
        for line in datafile:
            if line.startswith("---"):
                if in_yaml:
                    in_yaml = False
                else:
                    in_yaml = True
                    continue
            elif in_yaml == True:
                yaml_string += line
            else:
                markdown_content += line
    
    md_data = yaml.load(yaml_string)

    # if no yaml was found, set md_data to a empty dict
    if not md_data:
        md_data = {}

    if not "content" in md_data.keys():
        html = markdown(markdown_content)
        plain_text = BeautifulSoup(html, "html.parser").get_text()

        # remove Hugo shortcodes
        plain_text = re.sub(r"\{\{% .* %\}\}", "", plain_text)

        md_data["content"] = plain_text
    else:
        sys.stderr.write("ERROR: Could not store content for '" + filepath + "'. Frontmatter key 'content' exists!\n")
    return md_data


def create_index_list(walk_dir, base_level, base_url, verbose=False):
    global docsearch_mapping, docsearch_weight

    index_list = []
    objectID = 0

    for root, subdirs, files in os.walk(walk_dir):
        for filename in files:

            # only index md files
            if filename.endswith(".md"):
                objectID += 1
                filepath = os.path.join(root, filename)

                # sub-path as string
                subpath = root[len(walk_dir):].rstrip(os.sep)
                subpaths = subpath.lstrip(os.sep).split(os.sep)
                # index.md use their parent dir. all other files become folders
                if filename != "index.md":
                    subpaths[-1] = filename[:-3]
                hierarchy_list = [base_level]
                hierarchy_list.extend(subpaths)
                
                url_subpath = "/".join(subpaths)
                url = base_url + "/" + url_subpath + "/"

                if verbose:
                    sys.stderr.write("Indexing '" + filepath + "' (" + url + ")\n")

                # get data from the file (frontmatter and content)
                filedata = parse_md(filepath)

                # create index entry
                indexed_item = {'objectID': objectID, 'url': url }

                # map filedata to docsearch structure
                for docsearch_key, filedata_key in docsearch_mapping.items():
                    if type(filedata_key) == str and filedata_key in filedata.keys():
                        indexed_item[docsearch_key] = filedata[filedata_key]

                    # list values get aggregated as a list to the 
                    # docsearch attribute
                    elif type(filedata_key) == list:
                        aggregated = []
                        for filedata_subkey in filedata_key:
                            if filedata_subkey in filedata.keys():
                                aggregated.extend(filedata[filedata_subkey])
                        indexed_item[docsearch_key] = aggregated

                    # hierarchy and hierarchy_complete
                    hierarchy = create_empty_hierarchy()
                    hierarchy_complete = create_empty_hierarchy()
                    for level in range(7):
                        if level < len(hierarchy_list):
                            hierarchy["lvl" + str(level)] = hierarchy_list[level]
                            hierarchy_complete["lvl" + str(level)] = " > ".join(hierarchy_list[:level])
                    indexed_item["hierarchy"] = hierarchy
                    indexed_item["hierarchy_complete"] = hierarchy_complete

                    # hierarchy_radio and type
                    hierarchy_radio = create_empty_hierarchy()
                    max_lvl = len(subpaths) - 1
                    hierarchy_radio["lvl" + str(max_lvl)] = subpaths[max_lvl]
                    indexed_item["hierarchy_radio"] = hierarchy_radio
                    indexed_item["type"] = "lvl" + str(max_lvl)

                    # anchor and weight
                    indexed_item["anchor"] = None
                    indexed_item["weight"] = docsearch_weight

                index_list.append(indexed_item)
    sys.stderr.write("Done indexing .md files in '" + walk_dir + "'" + "\n")
    return index_list

def create_empty_hierarchy():
    empty_hierarchy = {}
    for level_index in range(7):
        empty_hierarchy["lvl" + str(level_index)] = None
    return empty_hierarchy


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="docsearch-pageindexer.py",
                                     description=
"""Produce a docsearch compatible index file (JSON) by examining all Hugo
markdown files in a directory and its sub-directories.""")
    parser.add_argument('content_dir',
                        metavar="<content dir>",
                        help='the top directory to search for .md files in')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        dest='verbose',
                        help='verbose output')
    parser.add_argument('-b', '--base-level',
                        default='Site Home',
                        dest='base_level', 
                        help='name of base level to use in index hierarchy. Defaults to "Site Home"')
    parser.add_argument('-u', '--base-url', 
                        default='http://localhost', 
                        dest='base_url', 
                        help='base URL to use in the index. Defaults to http://localhost')
    parser.add_argument('-t', '--tag', 
                        action='append', 
                        dest='tags', 
                        help='frontmatter taxonomy to use as tags in the index. Can be specified multiple times. E.g. -t tags -t categories')

    args = parser.parse_args()

    if args.tags != None:
        docsearch_mapping['tags'] = args.tags
    else:
        docsearch_mapping['tags'] = []

    # gather index data
    index_list = create_index_list(args.content_dir, args.base_level, args.base_url, verbose=args.verbose)

    # output index as json to stdout
    sys.stdout.write(json.dumps(index_list, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
