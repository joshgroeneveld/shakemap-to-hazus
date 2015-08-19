# The purpose of this script is to take an input shake.zip file from
# a USGS ShakeMap and convert the necessary files into a *.mdb file
# that can be used in HAZUS.

# Author: Josh Groeneveld
# Created On: 08.17.2015
# Updated On: 08.19.2015
# Copyright: 2015

"""NOTES: This script assumes that the shake.zip file has been downloaded
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

# 1. Initialize wxpython window
class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=wx.Size(520, 450))

        self.mainPanel = wx.Panel(self)

        self.SetTitle("Convert shake.zip to *.mdb for HAZUS")

        self.sb = self.CreateStatusBar()
        self.sb.SetStatusText("Please select your output directory.")

        # the welcome box
        self.welcome_sizerbox = wx.StaticBox(self.mainPanel, -1,
                                                pos=wx.Point(8, 6), size=wx.Size(476, 135))

        # the file picker box
        self.output_directory_staticbox = wx.StaticBox(self.mainPanel, -1, "Choose the output directory",
                                                pos=wx.Point(8, 145), size=wx.Size(476, 55))

        # the shape.zip box
        self.serverinfo_staticbox = wx.StaticBox(self.mainPanel, -1, "Select the location of the shake.zip file",
                                                pos=wx.Point(8, 200), size=wx.Size(476, 75))

        # the go button box
        self.go_button_staticbox = wx.StaticBox(self.mainPanel, -1,
                                                pos=wx.Point(8, 280), size=wx.Size(476, 100))

        # welcome text
        welcomemessage = "The hazus.zip file that comes with a standard USGS ShakeMap product has average ground" \
                         " motions instead of peak ground motions.  This tool converts the shake.zip file and its" \
                         " peak ground motions into a *.mdb file that you can then import into HAZUS for your own" \
                         " HAZUS earthquake scenario.  For more information on the differences between shake.zip" \
                         " and hazus.zip, follow this link: http://earthquake.usgs.gov/research/shakemap/formats.php"

        self.welcome_label = wx.StaticText(self.mainPanel, -1, welcomemessage, pos=wx.Point(20, 30),
                                          size=wx.Size(460, 95))

        # Set up the menu to choose a directory from the system
        self.output_directory_dialog_button = wx.Button(self.mainPanel, label="Choose Output Directory",
                                                        pos=wx.Point(20, 165), size=wx.Size(200, -1))
        self.output_directory = ""
        self.output_directory_dialog_button.Bind(wx.EVT_BUTTON, self.select_output_directory)

        # Create a file picker to choose the location of the shake.zip file
        self.input_file_button = wx.FilePickerCtrl(self.mainPanel, pos=wx.Point(20, 230), size=wx.Size(450, -1),
                                        wildcard="*.zip")
        self.input_file = ""
        self.input_file_button.Bind(wx.EVT_FILEPICKER_CHANGED, self.select_input_file)

        # Create a button that executes the process to extract the shake.zip file
        self.extract_file_button = wx.Button(self.mainPanel, label="Go!", pos=wx.Point(20, 300),
                                        size=wx.Size(150, 60))
        self.Bind(wx.EVT_BUTTON, self.extract_file, self.extract_file_button)

        self.Show()

    # 2. Select output directory
    def select_output_directory(self, event):
        """This function allows the user to choose an output directory that will store
        the *.mdb file."""
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE)
        dlg.Show()
        if dlg.ShowModal() == wx.ID_OK:
            self.output_directory = dlg.GetPath()
            self.sb.SetStatusText("You chose %s" % self.output_directory)
        dlg.Destroy()
        self.sb.SetStatusText("Select the location of your shake.zip file.")

    # 3. Select the location of the shake.zip file
    def select_input_file(self, event):
        """This function allows the user to choose the location of the shake.zip file"""
        obj = event.GetEventObject()
        path = event.GetPath()
        self.input_file = path
        self.sb.SetStatusText("You chose %s" % self.input_file)

    # 4. Extract the shake.zip file using the zipfile module
    def extract_file(self, event):
        """This function takes the user input path to the shake.zip file and
        unzips it in the output directory."""
        self.sb.SetStatusText("This button doesn't do anything...yet")

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
