# The purpose of this script is to take an input shape.zip file from
# a USGS ShakeMap and convert the necessary files into a *.mdb file
# that can be used in HAZUS.

# Author: Josh Groeneveld
# Created On: 08.17.2015
# Updated On: 08.31.2015
# Copyright: 2015

"""NOTES: This script assumes that the shape.zip file has been downloaded
to a local drive.  While a typical USGS ShakeMap includes a hazus.zip file,
this file represents average ground motions and not peak ground motions.  For
our HAZUS analyses, we have been using peak ground motions to model worst-case
scenarios.  For a description of the differences between the hazus.zip file
and the shape.zip file, check out the information here:
http://earthquake.usgs.gov/research/shakemap/formats.php
"""

import sys
import traceback
import wx
import os
import shutil
import zipfile
import arcpy
import inspect

# Initialize wxpython window
class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=wx.Size(520, 520))

        self.mainPanel = wx.Panel(self)

        self.SetTitle("Convert shape.zip to *.mdb for HAZUS")

        self.sb = self.CreateStatusBar()
        self.sb.SetStatusText("Please select your output directory.")

        # the welcome box
        self.welcome_sizerbox = wx.StaticBox(self.mainPanel, -1,
                                                pos=wx.Point(8, 6), size=wx.Size(476, 135))

        # the file picker box
        self.output_directory_staticbox = wx.StaticBox(self.mainPanel, -1, "Choose the output directory",
                                                pos=wx.Point(8, 145), size=wx.Size(476, 55))

        # earthquake name box
        self.earthquakename_staticbox = wx.StaticBox(self.mainPanel, -1, "Type the earthquake name",
                                                pos=wx.Point(8, 205), size=wx.Size(476, 60))

        # the shape.zip box
        self.serverinfo_staticbox = wx.StaticBox(self.mainPanel, -1, "Select the location of the shape.zip file",
                                                pos=wx.Point(8, 270), size=wx.Size(476, 75))

        # the go button box
        self.go_button_staticbox = wx.StaticBox(self.mainPanel, -1,
                                                pos=wx.Point(8, 350), size=wx.Size(476, 100))

        # welcome text
        welcomemessage = "The hazus.zip file that comes with a standard USGS ShakeMap product has average ground" \
                         " motions instead of peak ground motions.  This tool converts the shape.zip file and its" \
                         " peak ground motions into a *.mdb file that you can then import into HAZUS for your own" \
                         " HAZUS earthquake scenario.  For more information on the differences between shape.zip" \
                         " and hazus.zip, follow this link: http://earthquake.usgs.gov/research/shakemap/formats.php"

        self.welcome_label = wx.StaticText(self.mainPanel, -1, welcomemessage, pos=wx.Point(20, 30),
                                          size=wx.Size(460, 95))

        # Set up the menu to choose a directory from the system
        self.output_directory_dialog_button = wx.Button(self.mainPanel, label="Choose Output Directory",
                                                        pos=wx.Point(20, 165), size=wx.Size(200, -1))
        self.output_directory = ""
        self.output_directory_dialog_button.Bind(wx.EVT_BUTTON, self.select_output_directory)

        # Set up a text control for the earthquake name
        self.earthquake_name_box = wx.TextCtrl(self.mainPanel, -1, pos=wx.Point(20, 230), size=wx.Size(300, -1))
        self.earthquake_name = ""

        # Create a file picker to choose the location of the shape.zip file
        self.input_file_button = wx.FilePickerCtrl(self.mainPanel, pos=wx.Point(20, 300), size=wx.Size(450, -1),
                                        wildcard="*.zip")
        self.input_file = ""
        self.input_file_button.Bind(wx.EVT_FILEPICKER_CHANGED, self.select_input_file)

        # Create a button that executes the process to extract the shape.zip file
        self.extract_file_button = wx.Button(self.mainPanel, label="Go!", pos=wx.Point(20, 370),
                                        size=wx.Size(150, 60))
        self.Bind(wx.EVT_BUTTON, self.extract_file, self.extract_file_button)

        self.Show()

    # Select output directory
    def select_output_directory(self, event):
        """This function allows the user to choose an output directory that will store
        the *.mdb file."""
        dlg = wx.DirDialog(self, "Choose a folder", style=wx.DD_DEFAULT_STYLE)
        dlg.Show()
        if dlg.ShowModal() == wx.ID_OK:
            self.output_directory = dlg.GetPath()
            self.sb.SetStatusText("You chose %s" % self.output_directory)
        dlg.Destroy()
        self.sb.SetStatusText("Select the location of your shape.zip file.")

    # Select the location of the shape.zip file
    def select_input_file(self, event):
        """This function allows the user to choose the location of the shape.zip file"""
        obj = event.GetEventObject()
        path = event.GetPath()
        self.input_file = path
        self.sb.SetStatusText("You chose %s" % self.input_file)

    # Extract the shape.zip file using the zipfile module
    def extract_file(self, event):
        """This function takes the user input path to the shape.zip file and
        unzips it in the output directory."""
        # Capture the earthquake name
        self.earthquake_name = str(self.earthquake_name_box.GetValue())
        # If the earthquake name has spaces in it, replace with underscores
        self.earthquake_name = self.earthquake_name.replace(" ", "_")
        # Open the zip file
        fh = open(self.input_file, 'rb')
        # Create a ZipFile object
        z = zipfile.ZipFile(fh)
        # Go through each file in the zip archive and extract it
        for name in z.namelist():
            outpath = self.output_directory + "\\" + self.earthquake_name + "\\shape"
            z.extract(name, outpath)
        # Close the file
        fh.close()
        self.sb.SetStatusText("Unzipped shape.zip to %s" % outpath)
        self.project_fcs(outpath)

    # Reproject the files in the shape folder from WGS 84 to GCS_NAD83
    def project_fcs(self, path):
        """This function takes the unzipped shape folder and projects the four
        feature classes HAZUS needs from WGS84 to GCS_NAD83."""
        arcpy.env.workspace = path
        fcs = arcpy.ListFeatureClasses()
        for fc in fcs:
            out_sr = arcpy.SpatialReference(4269)
            fc_name = fc[:-4]
            if fc_name in ["pga", "pgv", "psa03", "psa10"]:
                fc_out_name = fc_name + "_GCS_NAD83.shp"
                arcpy.management.Project(fc, fc_out_name, out_sr)
                self.sb.SetStatusText("Projected: " + fc_name + " to GCS NAD83")
        self.copy_template()

    # Copy the template shakemap geodatabase to a Data folder in the
    # same directory as the earthquake name
    def copy_template(self):
        """This function copies a template geodatabase with empty data layers
        for PGA, PGV, PSA03, and PSA10 into the same directory as the
        earthquake name."""
        temp = inspect.stack()[0][1]
        script_dir = temp.replace('Shakemap-to-HAZUS.py', "Template")
        earthquake_dir = self.output_directory + "\\" + self.earthquake_name + "\\Data"
        shutil.copytree(script_dir, earthquake_dir)
        self.sb.SetStatusText("Copied template shakemap to " + earthquake_dir)
        self.rename_template(earthquake_dir)

    # Rename the template shakemap to match the earthquake name
    def rename_template(self, earthquake_dir):
        """This function expects a string that is a path to the output earthquake
        directory, then renames the template shakemap geodatabase based on the
        earthquake name."""
        os.chdir(earthquake_dir)
        for filename in os.listdir(os.getcwd()):
            if filename.endswith(".mdb"):
                os.rename(filename, filename.replace("Template_Shakemap", self.earthquake_name))
        self.sb.SetStatusText("Renamed template Shakemap to: " + self.earthquake_name + ".mdb")


try:
    app = wx.App(False)
    MainFrame(None)
    app.MainLoop()

except:
    # Error handling code from ArcGIS Resource Center
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n     " + str(sys.exc_type) + ": " + str(
        sys.exc_value) + "\n"

    print pymsg
