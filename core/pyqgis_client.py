#!/usr/bin/python
# -*- coding: utf8 -*-


from qgis.core import  QgsApplication, QgsProject, QgsLayoutExporter
import os

def export_atlas(qgs_project_path, layout_name, outputs_folder):

    # Open existing project
    project = QgsProject.instance()
    project.read(qgs_project_path)

    #print(f'Project in "{project.fileName()} loaded successfully')
    print('Project in "{fn} loaded successfully'.format(fn=project.fileName()) )

    # Open prepared layout that as atlas enabled and set
    layout = project.layoutManager().layoutByName(layout_name)

    # Export atlas
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()


    img_path = os.path.join(outputs_folder, "output.png")
    if os.path.isfile(img_path):
        os.unlink(img_path)

    exporter.exportToImage(img_path, QgsLayoutExporter.ImageExportSettings())
    #there will be ERROR 6: The PNG driver does not support update access to existing datasets,
    #but png will created successfully


def main():
    # Start a QGIS application without GUI
    qgs = QgsApplication([], False)
    qgs.initQgis()

    project_path = '/home/trolleway/tmp/tests/basemap.qgs'
    output_folder = '/home/trolleway/tmp/tests'
    layout_name = 'layout_retrowave'

    export_atlas(project_path, layout_name, output_folder)

    # Close the QGIS application
    qgs.exitQgis()

if __name__ == "__main__":
    main()
