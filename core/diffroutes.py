#!/usr/bin/python
# -*- coding: utf8 -*-

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='Take two filtered OSM dump with routes. Generate JSON with diff description.',
            formatter_class=PrettyFormatter)
    parser.add_argument('dump1', help='1st pbf file')      
    parser.add_argument('dump2', help='2st pbf file')     
    parser.add_argument('--skip-osmupdate',dest='skip_osmupdate', required=False, default=None, action='store_true')
    parser.add_argument('--workdir',dest='WORKDIR', required=True)
    parser.add_argument('--where',dest='attribute_filter', required=False,help = 'attrubute filter for layout geojson')
    parser.add_argument('--osmupdate-mode',
    dest='osmupdate_mode', 
    required=False, 
    default='hour', 
    const='hour', 
    choices=['minute', 'hour', 'day'], nargs = '?',
    help = 'osmupdate mode')
        
    parser.epilog = \
        '''Samples:
%(prog)s
--where="name_int = Vidnoe  --skip-osmupdate
--where "name_int = 'Gdansk'" --osmupdate-mode day

JSON structure:
Array of routes (one record = one type=route). Each record has:
route (bus, tram, or any route=* tag)
name,
ref,
action (created, deleted, changed)
tags_changes (array of (tag, old_value, new_value))
geometry_changes (length_increment_simplified (1.5 km, -8km, 0.5 km). Generated only if new line does not overlaps by buffer of old route.
geometry_changes_minor (is_minor_geometry_change)
''' \
        % {'prog': parser.prog}
    return parser



'''
check if sourcr files exists
convert to routes layers using ogr 
(сразу в память, а хули нет-то)

check if any route layers non-zero

begin synchro routine

for feature in routelayer_left:
    founded_route = self.search_route(route_feature, routeslayer_right)
    if founded_route is None:
        cmp_result = self.DELETED
    else:
        tags_diff = self.calc_tags_diff(route_feature, founded_feature)
        geometry_changes,geometry_changes_minor = self.calc_geometry_changes(route_feature, founded_feature)
    
# add deleted and modified routes to json
#search for created routes
for route_feature in routelayer_right:
    founded_route = self.search_route(route_feature, routeslayer_left)
    if founded_route is None:
        cmp_result = self.CREATED
        
    
#add created routes to json    
#end of synchro routine


'''


'''
Input:
2 x pbf

Output:
JSON with difference description


'''
