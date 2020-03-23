'''

Script om meetdoelen te bepalen voor Fase 1. 

'''

#%% Import packages
import geopandas as gpd
from meetdoelenproject import *

path_Basemap = r'C:\Users\mulderma\Documents\Projecten\Meetdoelen'
path_Objectbeheer = r'\\2_Data\20200317_Objectenbeheer.xlsx'
path_Output = r'\\4_Python\Package\Output'
path_Output_Data_cleaning = r'\\4_Python\Package\Output\Data_cleaning'
path_UtrechtNHshp = r'\\3_GIS\Utrecht_NoordHolland\Prov_UtrechtNoordHolland.shp'
path_Landgebruik = r'\\2_Data\LGN7.tif'
path_Contouren = r'\\3_GIS\HyKaWi_LHM_Contouren'
path_HuidigMeetdoel = r'\\2_Data\Meetdoelen_Bekend'

#%%
print('Stap 1. Importeren van Objectbeheer')
Obj_Filters_import = Import_Objectbeheer(path_Basemap+path_Objectbeheer)

print('Stap 2. Filteren van peilbuisfilters met foutieve gegevens')
Obj_Filters_clean, Obj_Filters_gefilterd, Obj_Filters_vervallen, Obj_Filters_foutief = data_cleaning(Obj_Filters_import, path_Basemap+path_Output_Data_cleaning)

print('Stap 3. Clippen van peilbuis lijst naar gewenste gebied')
Peilfilters_UtrechtNoordHolland = Clip_Peilfilters(Obj_Filters_clean, Path_ShapeGebied=path_Basemap+path_UtrechtNHshp, Path_OutputPoints=path_Basemap+path_Output+'\Peilfilters_UtrechtNoordHolland.xlsx')

print('Stap 4. Importeren van informatie watervoerend pakket')
Peilfilters_UtrechtNoordHolland = Import_WatervoerendPakket(Peilfilters_UtrechtNoordHolland)

print('Stap 5. Importeren van informatie landgebruik')
Peilfilters_UtrechtNoordHolland = Import_Landgebruik(Peilfilters_UtrechtNoordHolland, Loc_LGNraster=path_Basemap+path_Landgebruik)

print('Stap 6. Toewijzen waarnemingsput aan winning o.b.v. effectcontouren')
Peilfilters_UtrechtNoordHolland = Extract_Contouren(Peilfilters_UtrechtNoordHolland, Loc_Contouren=path_Basemap+path_Contouren)

print('Stap 7. Inventarisatie van meetdoelen o.b.v. criteria')
Peilfilters_UtrechtNoordHolland = Inventarisatie_Meetdoelen(Peilfilters_UtrechtNoordHolland)

print('Stap 8. Vaststellen van huidige meetdoelen')
Peilfilters_UtrechtNoordHolland.loc[:,'Meetdoel_Huidig'] = ''
Peilfilters_UtrechtNoordHolland = Huidige_Meetdoelen(Peilfilters_UtrechtNoordHolland, Loc_Huidig=path_Basemap+path_HuidigMeetdoel)

print('Stap 9. Peilfilters naar Peilbuizen')
Peilbuizen_UtrechtNoordHolland = Filters_to_Buis(Peilfilters_UtrechtNoordHolland)

print('Opslaan van de peilbuisdata naar .xlsx en .shp')
Peilbuizen_UtrechtNoordHolland.to_excel(path_Basemap+path_Output+'\\Peilbuizen_UtrechtNoordHolland.xlsx')
Peilbuizen_UtrechtNoordHolland = gpd.GeoDataFrame(Peilbuizen_UtrechtNoordHolland)
Peilbuizen_UtrechtNoordHolland.to_file(filename=path_Basemap+path_Output+'\\Peilbuizen_UtrechtNoordHolland.shp', driver="ESRI Shapefile")


