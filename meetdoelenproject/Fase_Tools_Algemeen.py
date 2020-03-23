'''
Algemene tools voor meetdoelenproject, waaronder:
    - Clippen van filters
    - Buizen in effectcontour
    - Inventarisatie van meetdoelen
    - String-cleaning
'''

#%% Import packages
import geopandas as gpd
import numpy as np
import os
import pandas as pd
import shapely.geometry

#%% Define functions

def Clip_Peilfilters(Obj_Filters, Path_ShapeGebied, Path_OutputPoints):
    '''
    Clip peilfilters binnen een gegeven shapefile.
    '''
    
    ## Stap 3A. Op basis van X en Y coördinaten van gegeven peilfilters wordt een geodatabase aangemaakt.
    Geometry = [shapely.geometry.Point(XY) for XY in zip(Obj_Filters['X'], Obj_Filters['Y'])]
    Obj_Points_gpd = gpd.GeoDataFrame(Obj_Filters, crs='epsg:28992', geometry=Geometry)

    ## Stap 3B. En uit de geodatabase kunnen alle peilfilters in het betreffende gebied worden geclipt.
    Gebied_polygon = gpd.read_file(Path_ShapeGebied)
    Polygon_extent = Gebied_polygon.geometry.unary_union
    Indices = []
    for i, index in enumerate(Obj_Points_gpd.index):
        if Obj_Points_gpd.loc[index,'geometry'].intersects(Polygon_extent):
            Indices.append(index)
            
    Gebied_points = Obj_Points_gpd.loc[Indices, :]
    Gebied_points.to_file(drive='ESRI Shapefile', filename=Path_OutputPoints)
    return Gebied_points


def Extract_Contouren(Peilfilters_Meetdoelen, Loc_Contouren):
    Peilfilters_Meetdoelen.loc[:,'InContour'] = ''
    Peilfilters_Meetdoelen.loc[:,'Winning'] = ''
    
    Files_Contouren = os.listdir(Loc_Contouren)
    for Files_Contour in Files_Contouren:
        if '.shp' in Files_Contour:
            if 'L1' not in Files_Contour:
                Contouren_Bepompt = gpd.read_file(Loc_Contouren + '\\' + Files_Contour)
                for i in Contouren_Bepompt.index:
                    EffectContour = Contouren_Bepompt.loc[i].geometry
                    Peilfilters_Meetdoelen.loc[Peilfilters_Meetdoelen.geometry.intersects(EffectContour), 'InContour'] = 'Yes'
                    Peilfilters_Meetdoelen.loc[Peilfilters_Meetdoelen.geometry.intersects(EffectContour), 'Winning'] += Contouren_Bepompt.loc[0,'Winning'] + ', '
    return Peilfilters_Meetdoelen


def Inventarisatie_Meetdoelen(Peilfilters_Meetdoelen):
    Peilfilters_Meetdoelen.loc[:,'Meetdoel_Inventarisatie'] = ''

    for i in Peilfilters_Meetdoelen.index:
        ## Meetdoel Effect Winning
        if Peilfilters_Meetdoelen.loc[i, 'Nfilters'] > 1:
            if Peilfilters_Meetdoelen.loc[i, 'InContour'] == 'Yes':
                Peilfilters_Meetdoelen.loc[i, 'Meetdoel_Inventarisatie'] += 'Effect Winning, '
        
        ## Meetdoel Droogteschade Landbouw
        if Peilfilters_Meetdoelen.loc[i, 'WVP'] == 1:
            if Peilfilters_Meetdoelen.loc[i, 'LGN'] == 'Landbouw':
                Peilfilters_Meetdoelen.loc[i, 'Meetdoel_Inventarisatie'] += 'Droogteschade, '
        
        ## Meetdoel Droogteschade Natuur
        if Peilfilters_Meetdoelen.loc[i, 'WVP'] == 1:
            if Peilfilters_Meetdoelen.loc[i, 'LGN'] == 'Natuur':
                Peilfilters_Meetdoelen.loc[i, 'Meetdoel_Inventarisatie'] += 'Droogteschade, '
        
        ## Meetdoel Zettingschade Bebouwing
        if Peilfilters_Meetdoelen.loc[i, 'WVP'] == 1:
            if Peilfilters_Meetdoelen.loc[i, 'LGN'] == 'Bebouwing':
                Peilfilters_Meetdoelen.loc[i, 'Meetdoel_Inventarisatie'] += 'Zettingschade, '
    return Peilfilters_Meetdoelen


def Huidige_Meetdoelen(Peilfilters_Meetdoelen, Loc_Huidig):
    Huidig_Vergunningplichtig = pd.read_excel(Loc_Huidig+'\\'+ 'Vergunningsplichtig_UtrechtNH.xlsx')
    for i in Huidig_Vergunningplichtig.index:
        Buis = Huidig_Vergunningplichtig.loc[i, 'business_id']
        for j in Peilfilters_Meetdoelen.index:
            if str(Buis) in str(Peilfilters_Meetdoelen.loc[j,'Business_id']):
                Peilfilters_Meetdoelen.loc[j,'Meetdoel_Huidig'] = 'Vergunningplichtig, '
            elif str(Buis) in str(Peilfilters_Meetdoelen.loc[j,'NITG_code']):
                Peilfilters_Meetdoelen.loc[j,'Meetdoel_Huidig'] = 'Vergunningplichtig, '
    
    Huidig_Kwaliteit = pd.read_excel(Loc_Huidig+'\\'+ 'Kwaliteitsbuizen situatie okt2018.xlsx')
    Huidig_Kwaliteit_actief = Huidig_Kwaliteit[Huidig_Kwaliteit['Kwaliteitsbuis?'] == 'J']
    
    Buizen = Huidig_Kwaliteit_actief['Peilbuis TNO-code'].unique()
    for Buis in Buizen:
        for j in Peilfilters_Meetdoelen.index:
            if str(Buis) in str(Peilfilters_Meetdoelen.loc[j,'Business_id']):
                Peilfilters_Meetdoelen.loc[j,'Meetdoel_Huidig'] = 'Kwaliteit Meetnet, '
            elif str(Buis) in str(Peilfilters_Meetdoelen.loc[j,'NITG_code']):
                Peilfilters_Meetdoelen.loc[j,'Meetdoel_Huidig'] = 'Kwaliteit Meetnet, '
    return Peilfilters_Meetdoelen


def CharacterRemoval(Chars):
    Chars = str(Chars)
    chars2remove = "'[]'"
    for char in chars2remove:
        Chars = Chars.replace(char, '')
    return Chars


def MeetdoelLISTcleaner(Meetdoel):
    Meetdoel = CharacterRemoval(Meetdoel)
    Meetdoel = Meetdoel.split(", ")
    Meetdoel = list(set(Meetdoel))
    Meetdoel = list(filter(None, Meetdoel))
    return Meetdoel

def Filters_to_Buis(Peilfilters_Meetdoelen):
    Peilbuizen = pd.DataFrame(columns=['MP_id','Nfilters','Filters','Business_id','NITG_code','X','Y','geometry','WVP','LGN','Winning','Meetdoel_Inventarisatie','Meetdoel_Huidig'])
    IDs = Peilfilters_Meetdoelen.loc[:,'MP_id'].unique()
    for ID in IDs:
        Filters = Peilfilters_Meetdoelen[Peilfilters_Meetdoelen['MP_id'] == ID]
        Filters_Save = Filters
        Buis_info = {'MP_id':Filters_Save['MP_id'].iloc[0], 'Nfilters':Filters_Save['Nfilters'].iloc[0], 
                      'Filters':CharacterRemoval(list(Filters_Save['Filt_N'].values.astype(np.int))), 
                      'Business_id':Filters_Save['Business_id'].iloc[0], 'NITG_code':Filters_Save['NITG_code'].iloc[0],
                      'X':Filters_Save['X'].iloc[0] , 'Y':Filters_Save['Y'].iloc[0], 'geometry':Filters_Save['geometry'].iloc[0],
                      'WVP':CharacterRemoval(list(Filters_Save['WVP'].values.astype(np.int))), 'LGN':Filters_Save['LGN'].iloc[0],
                      'Winning':Filters_Save['Winning'].iloc[0], 'Meetdoel_Inventarisatie':CharacterRemoval(MeetdoelLISTcleaner(str(list(Filters_Save['Meetdoel_Inventarisatie'].values)))),
                      'Meetdoel_Huidig':CharacterRemoval(MeetdoelLISTcleaner(str(list(Filters_Save['Meetdoel_Huidig'].values))))}
        Peilbuizen = Peilbuizen.append(Buis_info,ignore_index=True)
    
    return Peilbuizen
