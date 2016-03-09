import arcpy
import arcpy.mapping
import pythonaddins
import os


g_survey_data = {}
g_survey_selected = None
selection_update_count = 0

sde_conn_COUNTY_IMG = "COUNTY_IMG_2015"

class Survey(object):
    def __init__(self, batch_id, name):
        self.batch_id = batch_id
        self.name = name


def getSurveyBatchId(survey_name):

    global g_survey_data
    return [batch_id for batch_id, name in g_survey_data.items() if name == survey_name][0]


class cls_btnEnableCountyInventoryTools(object):

    """Implementation for CountyInventory2015_addin.cls_btnEnableCountyInventoryTools (Button)"""
    def __init__(self):

        self.enabled = True
        self.checked = False

    def onClick(self):

        global g_survey_data
        global g_survey_selected
        global sde_conn_COUNTY_IMG

        # enable combobox and populate with survey name values
        if self.checked:

            # disable the combo box
            cbSurveyIdentifier.enabled = False

        else:

            # enable the combo box
            cbSurveyIdentifier.enabled = True

            # now query and populate dropdown for survey data
            sde_conn_root = r'\\hamivarcgis10\scripts\CountyInventory2015'
            sde_conn_county_inventory = sde_conn_COUNTY_IMG + ".sde"
            sde_view_surveys = sde_conn_COUNTY_IMG + ".dbo.v_Current_Batch"

            view_surveys = os.path.join(
                sde_conn_root,
                sde_conn_county_inventory,
                sde_view_surveys
            )

            fields_view_surveys_in = [
                'batch_id',
                'survey_name'
            ]

            # test to make sure the table can be connected to
            if arcpy.Exists(view_surveys):
                print "Connected to v_Current_Batch table"
            else:
                arcpy.AddError('Unable to connect to database.')

            # select the surveys from the sql view into numpy array
            ary_surveys = arcpy.da.TableToNumPyArray(
                in_table=view_surveys,
                field_names=fields_view_surveys_in
            )

            # emtpy array to hold combo box items (survey names)
            cmb_items = []

            # create and add survey objects to the global space for access across classes and tools
            for survey in ary_surveys:
                # s = Survey(
                #     batch_id=survey[0],
                #     name=survey[1]
                # )
                cmb_items.append(survey[1])
                g_survey_data[survey[0]] = survey[1]

            del ary_surveys

            cbSurveyIdentifier.items = cmb_items

            mxd = arcpy.mapping.MapDocument("CURRENT")
            mxd.activeDataFrame.spatialReference = 4326
            print "Data Frame Spatial Reference set to WGS84 (4326)"

        pass


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


class cls_cbSurveyIdentifier(object):
    """Implementation for CountyInventory2015_addin.cbSurveyIdentifier (ComboBox)"""
    def __init__(self):
        self.items = []
        self.editable = True
        self.enabled = False
        self.dropdownWidth = 'WWWWWWWWWWWWW'
        self.width = 'WWWWWWWWWWWWW'

    def onSelChange(self, selection):

        global selection_update_count
        global sde_conn_COUNTY_IMG
        global g_survey_selected

        selection_update_count = 0

        # check if the layer_survey_image_points layer exists.. if so, delete it and all other layers
        if arcpy.Exists("layer_survey_image_points"):

            arcpy.Delete_management("survey_image_points")
            arcpy.Delete_management("layer_survey_image_points")
            arcpy.Delete_management('layer_route_sris')

            # clear all layers
            mxd = arcpy.mapping.MapDocument('CURRENT')
            for df in arcpy.mapping.ListDataFrames(mxd):
                for lyr in arcpy.mapping.ListLayers(mxd, "", df):
                    arcpy.mapping.RemoveLayer(df, lyr)
                for table_view in arcpy.mapping.ListTableViews(mxd, "", df):
                    arcpy.mapping.RemoveTableView(df, table_view)
            del mxd

        g_survey_selected = Survey(
            batch_id=getSurveyBatchId(selection),
            name=selection
        )

        print "Combobox selection changed.." + selection

        # create database connection paths.  connection, dataset?, table/layer
        sde_conn_root = r'\\hamivarcgis10\scripts\CountyInventory2015'
        sde_conn_route_network = 'NJ_SDE_10.sde'
        sde_route_network_dataset = 'NJ_SDE_10.SDE.Dataset'
        sde_layer_route_network = 'NJ_SDE_10.SDE.NJ_ROADWAY_NETWORK'

        sde_conn_county_inventory = sde_conn_COUNTY_IMG + ".sde"
        sde_view_survey_image_points = sde_conn_COUNTY_IMG + ".dbo.v_Current_Virtual_Points"

        # create link to roads network layer
        layer_roads_network = os.path.join(
            sde_conn_root,
            sde_conn_route_network,
            sde_route_network_dataset,
            sde_layer_route_network
        )

        # create link to data source view
        view_survey_image_points = os.path.join(
            sde_conn_root,
            sde_conn_county_inventory,
            sde_view_survey_image_points
        )

        # create a list of fields to be used in the
        fields_view_surveys_in = [
            'CamImNm',
            'SRI',
            'direction',
            'MP_START',
            'Latitude',
            'Longitude',
            'do_not_transfer',
            'virtual_image_path'
        ]

        # test to make sure the table can be connected to
        if arcpy.Exists(view_survey_image_points):
            print "Connected to v_Current_Virtual_Points table"
        else:
            arcpy.AddError('Unable to connect to database.')

        print "BATCH_ID: ", g_survey_selected.batch_id

        # query the working table for image points with the appropriate batch_id
        table_sri_selection = arcpy.MakeQueryTable_management(
            in_table=view_survey_image_points,
            out_table="survey_image_points",
            in_key_field_option="USE_KEY_FIELDS",
            in_key_field="CamImNm",
            in_field=fields_view_surveys_in,
            where_clause="batch_id='" + str(g_survey_selected.batch_id) + "'"
        )

        # make a spatial layer from the survey image point locations
        layer_xy_events = arcpy.MakeXYEventLayer_management(
            table="survey_image_points",
            in_x_field="Longitude",
            in_y_field="Latitude",
            out_layer="layer_survey_image_points"
        )

        # add selected routes
        npary_sris = arcpy.da.SearchCursor(
            in_table=table_sri_selection, # "survey_image_points"
            field_names="SRI"
            # sqlclause=(None, "GROUP BY SRI")
        )

        arcpy.Delete_management("survey_image_points")

        # get a workable list of sris
        ary_sri = [i[0] for i in npary_sris]

        # add the route query layer
        mem_layer_sri_selected = arcpy.MakeQueryLayer_management(
            input_database=os.path.join(sde_conn_root, sde_conn_route_network),
            out_layer_name="layer_route_sris",
            query="Select * from " + sde_layer_route_network + " where SRI IN ('" + "','".join(ary_sri) + "')",
            shape_type="POLYLINE"
        )

        # add symbology for the image point layer
        map_layer_image_points = arcpy.mapping.Layer("layer_survey_image_points")
        symbology_image_points = arcpy.mapping.Layer(os.path.join(sde_conn_root, 'layer_image_points.lyr'))
        arcpy.ApplySymbologyFromLayer_management(map_layer_image_points, symbology_image_points)

        mxd = arcpy.mapping.MapDocument('CURRENT')
        df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]

        ext = map_layer_image_points.getExtent()
        df.extent = ext

        # add roadway network
        layer_roads = arcpy.mapping.Layer(os.path.join(sde_conn_root, 'NJ_ROADWAY_NETWORK.lyr'))
        arcpy.mapping.AddLayer(df, layer_roads, "BOTTOM")
        # arcpy.RefreshTOC()

        del mxd
        del df
        del ext

        # # add symbology for the centerline data
        # map_layer_routes = arcpy.mapping.Layer("layer_route_sris")
        # symbology_route_sris = arcpy.mapping.Layer(os.path.join(os.path.dirname(__file__), 'layer_route_sris.lyr'))
        # arcpy.ApplySymbologyFromLayer_management(map_layer_routes, symbology_route_sris)

        btnMarkAsDoNotTransfer.enabled = True
        btnMarkAsTransfer.enabled = True

        pass

    def onEditChange(self, text):

        pass
    def onFocus(self, focused):
        pass

    def onEnter(self):
        pass

    def refresh(self):


        pass

class cls_btnLoadSurvey(object):

    """Implementation for CountyInventory2015_addin.btnLoadSurvey (Button)"""
    def __init__(self):

        self.enabled = False
        self.checked = False

    def onClick(self):
        pass

class cls_btnMarkAsDoNotTransfer(object):
    """Implementation for CountyInventory2015_addin.btnMarkImageLocationsAsDoNotTransfer (Button)"""
    def __init__(self):
        self.enabled = False
        self.checked = False

    def onClick(self):

        global selection_update_count
        global sde_conn_COUNTY_IMG

        layer_survey_image_points = "layer_survey_image_points"

        # set a flag to check processing processing
        do_selection_update = False

        # are there any selected features
        are_features_selected = len(arcpy.Describe("layer_survey_image_points").FIDset) > 0

        if not are_features_selected:

            pythonaddins.MessageBox('No Image Location Features have been selected.'
                                    '\n\nMake a selection and try again.', 'No Features Selected')

        else:

            # get a count of the selected features to limit within the threshold
            selected_features = arcpy.GetCount_management(layer_survey_image_points)
            selected_features_count = int(selected_features.getOutput(0))

            if selected_features_count > 50:

                do_selection_update = False

                response = pythonaddins.MessageBox('Are you sure you want to change more than 50 features?.', 'Continue?', 4)

                if response == "Yes":

                    do_selection_update = True
            else:

                do_selection_update = True

            if do_selection_update:

                # get a list of the selected points

                # with arcpy.da.SearchCursor("layer_survey_image_points", ["CamImNum", "Sri"]) as cur_selectedPoints:
                #     ids = [id for id in [point_selected[0] for point_selected in cur_selectedPoints]]

                camimnms_selected = []

                with arcpy.da.SearchCursor(layer_survey_image_points, ["CamImNm", "Sri"]) as cur_selectedPoints:
                    for row_selectedPoint in cur_selectedPoints:
                        camimnms_selected.append(row_selectedPoint[0])
                        sri_selected = row_selectedPoint[1]

                # arcpy.AddMessage("camimnms to be submitted for do_not_transfer" + ",".join(camimnms_selected))
                print "cam in nums selected: ", camimnms_selected

                sde_conn_root = r'\\hamivarcgis10\scripts\CountyInventory2015'
                sde_conn_county_inventory = sde_conn_COUNTY_IMG + ".sde"

                sde_county_inventory = os.path.join(
                    sde_conn_root,
                    sde_conn_county_inventory
                )

                sde_sql_conn = arcpy.ArcSDESQLExecute(sde_county_inventory)

                list_cam_im_nums = ",".join([str(camimnm) for camimnm in camimnms_selected])

                sql = """DECLARE @RC int
                DECLARE @batch_id int
                DECLARE @CamImNms nvarchar(max)
                DECLARE @sri nvarchar(20)
                DECLARE @do_not_transfer bit

                set @batch_id=""" + str(g_survey_selected.batch_id) + """
                set @CamImNms='""" + list_cam_im_nums + """'
                set @sri='""" + sri_selected + """'
                set @do_not_transfer=1

                EXECUTE @RC = [""" + sde_conn_COUNTY_IMG + """].[dbo].[P_Mark_As_Do_Not_Transfer]
                   @batch_id
                  ,@CamImNms
                  ,@sri
                  ,@do_not_transfer
                """

                # execute the stored procedure
                try:
                    sql_exec_return = sde_sql_conn.execute(sql)
                except Exception as err:
                    print(err)
                    sql_exec_return = False

                if isinstance(sql_exec_return, list):
                    print("Number of rows returned by query: {0} rows".format(len(sql_exec_return)))
                    for row in sql_exec_return:
                        print(row)
                    print("+++++++++++++++++++++++++++++++++++++++++++++\n")
                else:
                    if sql_exec_return:
                        print("SQL statement: {0} ran successfully.".format(sql))
                    else:
                        print("SQL statement: {0} FAILED.".format(sql))

                arcpy.SelectLayerByAttribute_management(layer_survey_image_points, "CLEAR_SELECTION")
                arcpy.RefreshActiveView()

                selection_update_count += 1

                if selection_update_count == 1:

                    # now update the symbology since there are Do Not Transfer Records

                    map_layer_image_points = arcpy.mapping.Layer(layer_survey_image_points)
                    symbology_image_points = arcpy.mapping.Layer(os.path.join(sde_conn_root, 'layer_image_points.lyr'))
                    # arcpy.ApplySymbologyFromLayer_management(map_layer_image_points, symbology_image_points)
                    mxd = arcpy.mapping.MapDocument("CURRENT")
                    df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]
                    arcpy.mapping.UpdateLayer(df, map_layer_image_points, symbology_image_points, "TRUE")
                    arcpy.RefreshTOC()
                    arcpy.RefreshActiveView()


class cls_btnMarkAsTransfer(object):
    """Implementation for CountyInventory2015_addin.btnMarkImageLocationsAsDoNotTransfer (Button)"""
    def __init__(self):
        self.enabled = False
        self.checked = False

    def onClick(self):

        global sde_conn_COUNTY_IMG

        layer_survey_image_points = "layer_survey_image_points"
        
        # flag to go through with the selection and update
        do_selection_update = False

        # are there any selected features
        are_features_selected = len(arcpy.Describe(layer_survey_image_points).FIDset) > 0

        if not are_features_selected:

            pythonaddins.MessageBox('No Image Location Features have been selected.'
                                    '\n\nMake a selection and try again.', 'No Features Selected')
        else:
        
            # make sure there aren't too many features selected
            selected_features = arcpy.GetCount_management(layer_survey_image_points)
            selected_features_count = int(selected_features.getOutput(0))

            if selected_features_count > 50:

                do_selection_update = False

                response = pythonaddins.MessageBox('Are you sure you want to change more than 50 features?.', 'Continue?', 4)

                if response == "Yes":
                    do_selection_update = True
            else:

                do_selection_update = True

            if do_selection_update:

                # get a list of the selected points

                # with arcpy.da.SearchCursor("layer_survey_image_points", ["CamImNum", "Sri"]) as cur_selectedPoints:
                #     ids = [id for id in [point_selected[0] for point_selected in cur_selectedPoints]]

                camimnms_selected = []

                with arcpy.da.SearchCursor(layer_survey_image_points, ["CamImNm", "Sri"]) as cur_selectedPoints:
                    for row_selectedPoint in cur_selectedPoints:
                        camimnms_selected.append(row_selectedPoint[0])
                        sri_selected = row_selectedPoint[1]

                # arcpy.AddMessage("camimnms to be submitted for do_not_transfer" + ",".join(camimnms_selected))
                print "cam in nums selected: ", camimnms_selected

                sde_conn_root = r'\\hamivarcgis10\scripts\CountyInventory2015'
                sde_conn_county_inventory = sde_conn_COUNTY_IMG + ".sde"

                sde_county_inventory = os.path.join(
                    sde_conn_root,
                    sde_conn_county_inventory
                )

                sde_sql_conn = arcpy.ArcSDESQLExecute(sde_county_inventory)

                list_cam_im_nums = ",".join([str(camimnm) for camimnm in camimnms_selected])

                sql = """DECLARE @RC int
                DECLARE @batch_id int
                DECLARE @CamImNms nvarchar(max)
                DECLARE @sri nvarchar(20)
                DECLARE @do_not_transfer bit

                set @batch_id=""" + str(g_survey_selected.batch_id) + """
                set @CamImNms='""" + list_cam_im_nums + """'
                set @sri='""" + sri_selected + """'
                set @do_not_transfer=0

                EXECUTE @RC = [""" + sde_conn_COUNTY_IMG + """].[dbo].[P_Mark_As_Do_Not_Transfer]
                   @batch_id
                  ,@CamImNms
                  ,@sri
                  ,@do_not_transfer
                """

                # execute the stored procedure
                try:
                    sql_exec_return = sde_sql_conn.execute(sql)
                except Exception as err:
                    print(err)
                    sql_exec_return = False

                if isinstance(sql_exec_return, list):
                    print("Number of rows returned by query: {0} rows".format(len(sql_exec_return)))
                    for row in sql_exec_return:
                        print(row)
                    print("+++++++++++++++++++++++++++++++++++++++++++++\n")
                else:
                    if sql_exec_return:
                        print("SQL statement: {0} ran successfully.".format(sql))
                    else:
                        print("SQL statement: {0} FAILED.".format(sql))

                arcpy.SelectLayerByAttribute_management(layer_survey_image_points, "CLEAR_SELECTION")
                arcpy.RefreshActiveView()

