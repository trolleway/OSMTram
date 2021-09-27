#!/usr/bin/python
# -*- coding: utf8 -*-


import os
import ogr, gdal, osr
import argparse

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='Take two filtered OSM dump with routes. Generate JSON with diff description.',
            formatter_class=PrettyFormatter)
    parser.add_argument('dump1', help='1st pbf file')      
    parser.add_argument('dump2', help='2st pbf file')     

        
    parser.epilog = \
        '''Samples:
%(prog)s dump1.osm.pbf dump2.osm.pbf
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


class Processor:
    gdal.UseExceptions()
    
    CHANGED = 'changed'
    NOCHANGED = 'nochanged'
    DELETED = 'deleted' 
    CREATED = 'created'   
    
    def open2mem(self,path):
        gdal.SetConfigOption('OSM_CONFIG_FILE', 'core/osmconf.ini')
        # OGR_INTERLEAVED_READING shall not be used in modern gdal versions
        ds = gdal.OpenEx(path,gdal.OF_READONLY) #,allowed_drivers=['PBF']
        assert ds is not None
        layer = ds.GetLayer('multilinestrings')
        
        driver_mem = ogr.GetDriverByName('MEMORY')
        ds_mem = driver_mem.CreateDataSource('memData')
        driver_mem.Open('memData',1) 
        
        layer_mem = ds_mem.CopyLayer(ds.GetLayer('multilinestrings'),'multilinestrings',['OVERWRITE=YES'])
             
        return ds_mem, layer_mem
        
    def search_route(self,route_feature,routes_layer, routes_ds):
        for feature in routes_layer:
            if feature.GetField('osm_id')==route_feature.GetField('osm_id'): 
                return feature.Clone()
        return None
    
    def calc_tags_diff(self,route_feature, founded_feature):
        is_changed = False
        diff = dict()

        assert founded_feature is not None  
        if route_feature is None and founded_feature is not None: 
            is_changed = True        
            return True
            
        if route_feature.GetField('ref') != founded_feature.GetField('ref'):
            is_changed = True
        if route_feature.GetField('from') != founded_feature.GetField('from'):
            is_changed = True     
        if route_feature.GetField('to') != founded_feature.GetField('to'):
            is_changed = True 
        if is_changed: return True           
        return None
        
    def calc_geometry_changes(self,route_feature, founded_feature):
    
        def get_utm_zone(centroid):

            #magic numbers 
            x = int(centroid.GetX() // 6)
            zone = x + 31
            epsg_utm = zone + 32600
            if int(centroid.GetX()) < 0 : 
                epsg_utm = zone + 32700 #south hemisphere

            return epsg_utm
        def digit_distance_nums(n1, n2):
            return sum(map(int,str(abs(int(n1)-int(n2)))))
    
        geom_left = route_feature.GetGeometryRef()
        geom_right = founded_feature.GetGeometryRef()
        
        centroid = geom_left.Centroid()
        
        utmEPSG = get_utm_zone(centroid)

        
        wgs1984SpatialRef = osr.SpatialReference()
        wgs1984SpatialRef.ImportFromEPSG(4326)
        
        utmSpatialRef = osr.SpatialReference()
        utmSpatialRef.ImportFromEPSG(utmEPSG)
        
        coordTrans = osr.CoordinateTransformation(wgs1984SpatialRef,utmSpatialRef)
        
        geom_left.Transform(coordTrans)
        geom_right.Transform(coordTrans)
                
        len1 = geom_left.Length()
        len2 = geom_right.Length()
        
        geom_status = dict()
        is_diff = False
        
        if len2 > len1 and len2-len1>100: 
            is_diff = True
            geom_status.update({'length increased':True})
            geom_status.update({'length diff':len2-len1})
        if len2 < len1 and len2-len1<-100: 
            is_diff = True 
            geom_status.update({'length decreased':True})
            geom_status.update({'length diff':len2-len1})
                    
        if is_diff: 
            return geom_status
        return  None
    def calc_diff(self,pbf1,pbf2):

        #check if sourcr files exists

        assert os.path.isfile(pbf1)
        assert os.path.isfile(pbf2)
        
        gdal.UseExceptions()
        
        #convert to routes layers using ogr 
        #(сразу в память, а хули нет-то)
        ds_mem_left, routeslayer_left = self.open2mem(pbf1)
        
        fc = routeslayer_left.GetFeatureCount()

        ds_mem_right,routeslayer_right = self.open2mem(pbf2)

        result_struct = list()
        #check if any route layers non-zero
        #assert (routeslayer_left.GetFeatureCount() > 0) or (routeslayer_right.GetFeatureCount() > 0) 

        for route_feature in routeslayer_left:
            print(route_feature.GetField('ref'))
            founded_route_feature = self.search_route(route_feature, routeslayer_right, ds_mem_right)

            record = dict()
            if founded_route_feature is None:
                cmp_result = self.DELETED
                record.update({'status' : cmp_result})
                record.update({'old_ref':route_feature.GetField('ref')})
                record.update({'old_from':route_feature.GetField('from')})
                record.update({'old_to':route_feature.GetField('to')})
                record.update({'old_name':route_feature.GetField('name')}) 
            else:
                assert founded_route_feature is not None
                assert route_feature is not None
                
                if route_feature is None: print('signal')
                tags_diff = self.calc_tags_diff(route_feature.Clone(), founded_route_feature)
                geometry_changes = self.calc_geometry_changes(route_feature, founded_route_feature)
                if tags_diff is None and geometry_changes is None:
                    cmp_result = self.NOCHANGED
                    record.update({'status' : cmp_result})
                else:
                    cmp_result = self.CHANGED
                    record.update({'status' : cmp_result})
                    record.update({'tags_diff' : tags_diff})
                    record.update({'name':founded_route_feature.GetField('name')})
                    
                    record.update({'ref':founded_route_feature.GetField('ref')})
                    record.update({'from':founded_route_feature.GetField('from')})
                    record.update({'to':founded_route_feature.GetField('to')})
                    
                                        
                    record.update({'old_ref':route_feature.GetField('ref')})
                    record.update({'old_from':route_feature.GetField('from')})
                    record.update({'old_to':route_feature.GetField('to')})
                    record.update({'old_name':route_feature.GetField('name')})  
                    if geometry_changes is not None: record.update(geometry_changes)
                    
            if record['status'] != self.NOCHANGED:
                result_struct.append(record)
            

            
        # add deleted and modified routes to json
        #search for created routes
        for route_feature in routeslayer_right:
            founded_route = self.search_route(route_feature, routeslayer_left,ds_mem_left)
            if founded_route is None:
                cmp_result = self.CREATED
                record = {}
                record.update({'status' : cmp_result})
                
                record.update({'name':route_feature.GetField('name')})
                record.update({'ref':route_feature.GetField('ref')})
                record.update({'from':route_feature.GetField('from')})
                record.update({'to':route_feature.GetField('to')})
                tags_diff = self.calc_tags_diff(None, route_feature)
                result_struct.append(record)
            
        #add created routes to json    
        #end of synchro routine
        
        return result_struct
        
    
    def print_diff(self,diff_dict):
    

        print('---- Сводка изменений ----')
        for element in diff_dict:
            #print(element)
            #print()
            msg = ''
            if element.get('length increased'): msg = msg + ' продлён на ' + str(round(element.get('length diff'),0)) + ' м '
            if element.get('length decreased'): msg = msg + ' укорочен на ' + str(round(element.get('length diff'),0)) + ' м '
            
            if element.get('tags_diff'):
                msg = msg + element.get('old_name') + ' становится  [' + element.get('name') + '] '
            elif element.get('status') == self.DELETED:
                msg = msg + 'отменён [' + element.get('old_name') + '] '
            elif element.get('status') == self.CREATED:
                msg = msg + 'введён [' + element.get('name') + '] '
            else:
                msg = msg + ' [' + element.get('name') + '] '
            
            
            msg = msg + ' '


            print(msg)
        '''
        { 
        
        
        
        }
'''

'''


2 x pbf

Output:
JSON with difference description

   
'''



'''

aria2c https://osm-internal.download.geofabrik.de/russia/central-fed-district-internal.osh.pbf
osmium extract central-fed-district-internal.osh.pbf -H -p moscow.poly -o moscow.osh.pbf

ts='2020-10-01'

ti=T00:00:00Z
tst=$ts$ti
osmium time-filter moscow.osh.pbf $tst --overwrite -o temp.osm.pbf
osmconvert temp.osm.pbf -o=temp.o5m
        osmfilter temp.o5m --keep= --keep="route=tram " --out-o5m >temp2.o5m
        rm -f temp.o5m
        osmconvert temp2.o5m -o=$ts.osm.pbf
        rm -f temp2.o5m
        
'''




if __name__ == '__main__':
    parser = argparser_prepare()
    args = parser.parse_args()
    print(args.dump1)
    print(args.dump2)
    
    processor = Processor()
    diff_dict = processor.calc_diff(pbf1=args.dump1,pbf2=args.dump2)
    processor.print_diff(diff_dict)
