#!/usr/bin/python
# -*- coding: utf8 -*-

from qgis.core import  QgsApplication, QgsProject, QgsLayoutExporter
import os
import argparse

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='Export QGIS map composer layout to png using pyqgis',
            formatter_class=PrettyFormatter)
    parser.add_argument('--project', dest='project', required=True, help='Path to qgis project')
    parser.add_argument('--layout', dest='layout', required=True, help='layout name')
    parser.add_argument('--output',dest='output', required=True, help='Output raster file')

    parser.epilog = \
        '''Samples:
%(prog)s --project "/home/trolleway/tmp/tests/basemap.qgs" --layout "layout_retrowave_album" --output "/home/trolleway/tmp/out.png"

''' \
        % {'prog': parser.prog}
    return parser



def export_atlas(qgs_project_path, layout_name, filepath):

    # Open existing project
    project = QgsProject.instance()
    print(os.path.abspath(os.path.dirname(qgs_project_path)))
    #quit()
    os.chdir(os.path.abspath(os.path.dirname(qgs_project_path)))
    #project.read(qgs_project_path)
    project.read(os.path.abspath(qgs_project_path))
    project.readPath(os.path.abspath(os.path.dirname(qgs_project_path)))

    #print(f'Project in "{project.fileName()} loaded successfully')
    print('Project in "{fn} loaded successfully'.format(fn=project.fileName()) )

    # Open prepared layout that as atlas enabled and set
    layout = project.layoutManager().layoutByName(layout_name)

    # Export atlas
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()

    img_path = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    myAtlas = layout.atlas()
    myAtlasMap = myAtlas.layout()
    myAtlas.setFilenameExpression(img_path)
    
    pdf_settings=QgsLayoutExporter(myAtlasMap).PdfExportSettings()
    image_settings = QgsLayoutExporter(myAtlasMap).ImageExportSettings()
    image_settings.dpi = 96
    
    imageExtension = '.jpg'
    
    print('layout_name= {layout_name} '.format(layout_name=layout_name) )
    print('try export to {img_path} '.format(img_path=img_path) )
    
    outputFormat = 'image'
    if outputFormat == 'image':
        if os.path.isfile(os.path.join(img_path,'output_0.jpg')):
            os.unlink(os.path.join(img_path,'output_0.jpg'))
            
        for layout in QgsProject.instance().layoutManager().printLayouts():
            if myAtlas.enabled():
                print('signal')
                result, error = QgsLayoutExporter.exportToImage(myAtlas, 
                                    baseFilePath=img_path + '', extension=imageExtension, settings=image_settings)
                if not result == QgsLayoutExporter.Success:
                    print(error)
    quit()
    os.rename(os.path.join(img_path,'output_0.jpg'),os.path.join(img_path,filename))
    quit()
                

    #exporter.exportToImage(img_path, layout.atlas(), QgsLayoutExporter.ImageExportSettings())
    #there will be ERROR 6: The PNG driver does not support update access to existing datasets,
    #but png will created successfully


def main():

    parser = argparser_prepare()
    args = parser.parse_args()

    # Start a QGIS application without GUI
    qgs = QgsApplication([], False)
    qgs.initQgis()


    #project_path = args.project
    #output_folder = '/home/trolleway/tmp/tests'
    #layout_name = args.layout

    export_atlas(args.project, args.layout, args.output)

    # Close the QGIS application
    qgs.exitQgis()

if __name__ == "__main__":
    main()
