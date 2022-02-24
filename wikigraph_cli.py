#!/usr/bin/env python3
from wikigraph import WikiGraph
from argparse import ArgumentParser


if __name__=='__main__':


    parser = ArgumentParser(description="Creates a Graph of referenced articles in Wikipedia")
    parser.add_argument('url',nargs='?', metavar='<URL>', type=str, help='The url of the starting article', default=None)
    parser.add_argument('--depth', type=int, help='The maximum amount of references that will be followed from the starting article', default=10, dest='depth')
    parser.add_argument('--size', type=int, help='The maximum amount of articles that the graph will include', default=500, dest='size')

    args = parser.parse_args()
    if not args.url:
        start_url = str(input("enter the url of the starting wikipedia page."))
    else:
        start_url = args.url

    print(f'Creating wikigraph around {start_url} with depth {args.depth} and maximum size {args.size}')

    graph = WikiGraph(start_url, args.depth, args.size)
    graph.draw()
