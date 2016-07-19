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
docsearch_weight = { "position": 10,
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
        plain_text = re.sub(r"\{\{[%<] .* [%>]\}\}", "", plain_text)

        md_data["content"] = plain_text
    else:
        sys.stderr.write("ERROR: Could not store content for '" + filepath + "'. Frontmatter key 'content' exists!\n")
    return md_data


def create_index_list(walk_dir, base_level, base_url, verbose=False):
    """Create a list containing index data according to the docsearch spec.

    walk_dir: the directory to recursively search for .md files
    base_level: name of top level node
    base_url: the base url used to construct page URLs
    """

    global docsearch_mapping, docsearch_weight

    index_list = []
    objectID = 0

    for root, subdirs, files in os.walk(walk_dir):
        for filename in files:

            # only index md files
            if filename.endswith(".md"):
                objectID += 1
                filepath = os.path.join(root, filename)

                # get data from the file (frontmatter and content)
                filedata = parse_md(filepath)

                # subpath (i.e. path below content dir) as string then converted
                # to list
                subpath = root[len(walk_dir):].rstrip(os.sep)
                subpath = subpath.lstrip(os.sep).split(os.sep)

                # transform the subpath. Assumes that Hugo uses "pretty URLs"
                # (strip the file extension '.md')
                #
                # index.md uses its parent dir. all other .md files become
                # folders
                if filename != "index.md":
                    # append if path is not just the root
                    if len(subpath) > 1:
                        subpath.append(filename[:-3])
                    # if just the root, i.e. subpath == [""], then replace it
                    else:
                        subpath[0] = filename[:-3]

                # build the URL to the file
                url_subpath = "/".join(subpath)
                url = base_url + "/" + url_subpath + "/"

                if verbose:
                    sys.stderr.write("Indexing '" + filepath + "' (" + url + ")\n")

                # hierarchy_list contains the names of all levels (sections)
                # and is used to build the hierarchy structures below
                hierarchy_list = [base_level]
                hierarchy_list.extend(subpath)

                # replace the last hierarchy with the `linktitle` or `title`
                # of the page if it exists
                if "linktitle" in filedata.keys():
                    hierarchy_list[-1] = filedata["linktitle"]
                elif "title" in filedata.keys():
                    hierarchy_list[-1] = filedata["title"]
                
                hierarchy_max_lvl = len(hierarchy_list) - 1

                # create the new index entry
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

                    # build hierarchy and hierarchy_complete dictionaries
                    # - hierarchy items contain the names of the leaves
                    # - hierarchy_complete items contains the full breadcrumb
                    #   path for each leaf
                    #
                    # a hierarchy has levels 0-6
                    hierarchy = create_empty_hierarchy()
                    hierarchy_complete = create_empty_hierarchy()
                    for level in range(7):
                        # fill in blanks for all levels with names
                        if level < len(hierarchy_list):
                            # single leaf value for hiearchy
                            hierarchy["lvl" + str(level)] = hierarchy_list[level]
                            # breadcrumbs for hierarchy_complete
                            hierarchy_complete["lvl" + str(level)] = " > ".join(hierarchy_list[:level+1])
                    indexed_item["hierarchy"] = hierarchy
                    indexed_item["hierarchy_complete"] = hierarchy_complete

                    # hierarchy_radio and type
                    # - in hierarchy_radio, one of the levels has a value
                    # - type contains the name of the deepest level, e.g. "lvl2"
                    hierarchy_radio = create_empty_hierarchy()
                    hierarchy_radio["lvl" + str(hierarchy_max_lvl)] = hierarchy_list[hierarchy_max_lvl]
                    indexed_item["hierarchy_radio"] = hierarchy_radio
                    indexed_item["type"] = "lvl" + str(hierarchy_max_lvl)

                    # anchor is not captured
                    indexed_item["anchor"] = None

                    # shallow copy the weight template (ok since no nesting)
                    indexed_item["weight"] = docsearch_weight.copy()
                    # use hierarchy depth as weight level
                    indexed_item["weight"]["level"] = hierarchy_max_lvl

                # add the indexed item to the index list (returned by function)
                index_list.append(indexed_item)

    sys.stderr.write("Done indexing .md files in '" + walk_dir + "'" + "\n")
    return index_list


def create_empty_hierarchy():
    """Create an empty hierarchy structure (dict).

    hierarchy = {
                  "lvl0": None,
                  "lvl1": None,
                  "lvl2": None,
                  "lvl3": None,
                  "lvl4": None,
                  "lvl5": None,
                  "lvl6": None
                }
    """

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
