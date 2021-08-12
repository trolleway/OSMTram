#!/usr/bin/python3
# -*- coding: utf8 -*-


import argparse

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='Substitute values to QGIS project',
            formatter_class=PrettyFormatter)
    parser.add_argument('--src', dest='src', required=True, help='Path to template project')
    parser.add_argument('--dst', dest='dst', required=True, help='Path to new project')
    parser.add_argument('--layout_extent',dest='layout_extent', required=True, help='<Extent ymax="8087642" xmax="3487345" xmin="3470799" ymin="8075943"/>')

    parser.epilog = \
        '''Samples:
%(prog)s --src "../qgis_project_templates/retrowave.qgs.template.qgs" --dst "~/tmp/tests/out.qgs" --layout_extent "<Extent ymax=/"8087642" xmax="3487345" xmin="3470799" ymin="8075943"/>"

''' \
        % {'prog': parser.prog}
    return parser

def substitute_project(src,dst,layout_extent):
    #open template file
    file = open(src, 'r')
    newfile = open(dst, 'w')
    for line in file:
        #print(line)
        tokens=list()
        tokens.append('{layout_extent}')
        if any(word in line for word in tokens):
            fmt_line = line.format(layout_extent=layout_extent)
        else:
            fmt_line = line
        newfile.write(fmt_line)
    #create export file
    #read by line

    newfile.close()
    file.close()


if __name__ == "__main__":
    substitute_project(src='../qgis_project_templates/retrowave.qgs.template.qgs',dst = '/home/trolleway/tmp/tests/out.qgs', layout_extent='''<Extent ymax="8087642" xmax="3487345" xmin="3470799" ymin="8075943"/>''')
