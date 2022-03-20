#!/usr/bin/env python3
import os.path
from wikigraph import WikiGraph
from argparse import ArgumentParser
"""CLI for the Wikigraph, with commandline options.
"""

if __name__=='__main__':


    parser = ArgumentParser(description="Creates a Graph of referenced articles in Wikipedia")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument('--url', type=str, help='The url of the starting article', default=None)
    source_group.add_argument('--infile', metavar= 'PATH', type=str, help='Instead of creating, use the graph that is stored under this path', default=None)
    parser.add_argument('--depth', type=int, help='The maximum amount of references that will be followed from the starting article', default=10, dest='depth')
    parser.add_argument('--size', type=int, help='The maximum amount of articles that the graph will include', default=500, dest='size')
    parser.add_argument('--draw', action='store_true', help='Create and open an HTML-File with a visualization of the graph. Additional draw options are --search and --html.')
    parser.add_argument('--search', type=str, help='Highlight articles with this string in it. (per default, only in Title)', default=None, dest='search_string')
    parser.add_argument('--html', help='Also look through html to find the search term', action="store_true")
    parser.add_argument('--write_adj_list', metavar='PATH', type=str, help='graph adjacency list file will be stored in this path.', default=None)
    parser.add_argument('--write_gml', metavar='PATH', type=str, help='graph will be stored in this path in gml format. Good for analysis in other graph exploration tools.', default=None)
    parser.add_argument('--write_with_html', help='also save html into the output file into the export format. Not compatible with adjacency lists.', action='store_true')
    parser.add_argument('--save', type=str, metavar='PATH', help='Save the graph in this path', default=None)
    args = parser.parse_args()
    # Creation of graph object:
    if args.url and args.infile:
        print('You can either specify an url around which the graph is created, or specify a file from which it is loaded.')
        exit(1)
    
    elif args.url:
        # If the graph is created, more than likely, it should be saved. Terminating early if the path to the save is invalid.
        if not args.save and not args.write_gml and not args.write_adj_list:
            print('\nWARNING: You have not specified any persistence for your graph. If this is a mistake, terminate now and start with appropriate arguments.\n')
        if args.save:
            if os.path.exists(args.save): 
                print(f'There is already a file or directory at {args.save}, the graph could not be saved. Aborting creation...')
                exit(1)
            if not os.path.exists(os.path.dirname(args.save)):
                print(f'{args.save} is an invalid path. The graph could not be saved. Aborting creation...')
                exit(1)
        print(f'Creating wikigraph around {args.url} with depth {args.depth} and maximum size {args.size}')
        graph = WikiGraph(args.url, args.depth, args.size)
    elif args.infile:
        print(f'Loading wikigraph from {args.infile}...')
        try:
            graph = WikiGraph.load(args.infile)
        except FileNotFoundError as e:
            print(f'{args.infile} could not be loaded: Path invalid.')
            exit(1)
    else:
        print('You need to either specify a file from which the graph should be loaded, or an url around which it should be created. See --help for help.')
        exit(1)
    
    ##############
    # Processing #
    ##############
    # First, draw the graph. It will be displayed while further processing to files takes place.
    if args.draw:
        print(f'drawing graph...')
        if args.search_string:
            print(f'Highlighting all article-nodes containing {args.search_string}')
            if args.html:
                print(f'Also searching HTML for {args.search_string}')
        graph.draw(search_term=args.search_string, search_html=args.html)
    
    # Write adjacency list file if specified
    if args.write_adj_list:
        print(f'writing adjacency-file to {args.write_adj_list}')
        try:
            graph.write_adjacency_list(args.write_adj_list)
        except FileExistsError:
            print(f'There is already a file in {args.write_adj_list}. Not overwriting.')
        except FileNotFoundError:
            print(f'{args.write_adj_list}: Path invalid')
    # Write gml file if specified
    if args.write_gml:
        print(f'writing gml to {args.write_gml}')
        if args.write_with_html: print(f'including article html as gml properties')
        try:
            graph.write_to_gml(args.write_gml, args.write_with_html)
        except FileExistsError:
            print(f'There is already a file in {args.write_gml}. Not overwriting.')
        except FileNotFoundError:
            print(f'{args.write_gml}: Path invalid')

    if args.save:
        print(f'saving graph at {args.save}')
        try:
            graph.save(args.save)
        except FileExistsError:
            print(f'There is already a file in {args.save}. Not overwriting.')
        except FileNotFoundError:
            print(f'{args.save}: Path invalid')