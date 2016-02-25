import arcpy
import pythonaddins

class ExtensionClass6(object):
    """Implementation for CountyInventory2015_addin.extension7 (Extension)"""
    def __init__(self):
        # For performance considerations, please remove all unused methods in this class.
        self.enabled = True


class cls_btnImageLocationSelectionActivate(object):
    """Implementation for CountyInventory2015_addin.btnImageLocationSelectionActivate (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class cls_btnLoadSurvey(object):
    """Implementation for CountyInventory2015_addin.btnLoadSurvey (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class cls_btnMarkImageLocationsAsDoNotTransfer(object):
    """Implementation for CountyInventory2015_addin.btnMarkImageLocationsAsDoNotTransfer (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class cls_cbSurveyIdentifier(object):
    """Implementation for CountyInventory2015_addin.cbSurveyIdentifier (ComboBox)"""
    def __init__(self):
        self.items = ["item1", "item2"]
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWW'
        self.width = 'WWWWWW'
    def onSelChange(self, selection):
        pass
    def onEditChange(self, text):
        pass
    def onFocus(self, focused):
        pass
    def onEnter(self):
        pass
    def refresh(self):
        pass