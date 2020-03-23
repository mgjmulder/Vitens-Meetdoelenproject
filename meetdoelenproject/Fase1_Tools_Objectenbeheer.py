'''
Functies om Objectenbeheer te importeren en foutieve data te filteren van totale dataset.
Naast foutieve data wordt ook gefilterd op alleen waarnemingsputten en actieve buizen (dus niet vervallen).
'''

#%% Import packages
import numpy as np
import pandas as pd


#%% Define functions

def Import_ObjMaaiveldhoogtes(Obj_Meetpunt, Obj_Maaiveld):
    '''
    Importeert alle meest recente maaiveldhoogtes uit Objectbeheer. 
    '''
    
    ## Configuratie van Maaiveld dataframe met meetpunt ID en kolom met maaiveldhoogtes.
    Maaiveld_DF = pd.DataFrame()
    Maaiveld_DF['MP_id'] = Obj_Meetpunt['id'].unique()
    Maaiveld_DF = Maaiveld_DF.sort_values(['MP_id'], ascending=[True]) 
    Maaiveld_DF = Maaiveld_DF.reset_index(drop=True)
    Maaiveld_DF['MV_Objectbeheer'] = ''
    
    ## Trekt meest recente maaiveldhoogteaanpassing uit Objectbeheer en vult Maaiveld dataframe in. 
    for ID in Maaiveld_DF['MP_id']:
        ## Indien er geen maaiveldhoogte voor het betreffende ID bekend is, wordt nan ingevuld.
        if len(Obj_Maaiveld[Obj_Maaiveld['meetpunt_id'] == ID]) == 0:
            Maaiveld_DF.loc[Maaiveld_DF[Maaiveld_DF['MP_id'] == ID].index,'MV_Objectbeheer'] = np.nan
            ## Indien er wel een maaiveldhoogte voor het ID bekend is, wordt de meest recente waarde ingevuld.
        else:
            MV_MP = Obj_Maaiveld['maaiveldhoogte'][Obj_Maaiveld['datum_vanaf'][Obj_Maaiveld['meetpunt_id'] == ID].idxmax()]
            Maaiveld_DF.loc[Maaiveld_DF[Maaiveld_DF['MP_id'] == ID].index,'MV_Objectbeheer'] = MV_MP
    
    ## Zet alle maaiveldhoogtes als float.
    Maaiveld_DF['MV_Objectbeheer'] = Maaiveld_DF['MV_Objectbeheer'].astype(np.float)
    
    return Maaiveld_DF


def Import_Instantie(Obj_Meetpunt, Loc_Objectbeheer):
    Obj_Instantie = pd.read_excel(Loc_Objectbeheer, sheet_name='Instantie')
    
    Obj_Meetpunt_Columns = ['eigenaar_meetpunt_id', 'opdrachtgevende_instantie_id', 'beherende_instantie_id', 'waarnemende_instantie_id']
    for j, column in enumerate(Obj_Meetpunt_Columns):
        for i, index in enumerate(Obj_Instantie.index):
            Obj_Meetpunt.loc[:, column] = Obj_Meetpunt.loc[:, column].replace(Obj_Instantie.loc[index, 'id'], Obj_Instantie.loc[index, 'name'])
    
    return Obj_Instantie, Obj_Meetpunt


def Import_Objectbeheer(Loc_Objectbeheer):
    '''
    Functie om alle Vitens peilfilters uit Objectbeheer te importeren, inclusief met (meest recente) maaiveldhoogtes.
    '''
    ## Importeer alle meetpunten uit Objectenbeheer.
    Obj_Meetpunt = pd.read_excel(Loc_Objectbeheer, sheet_name='Meetpunt')
    
    ## Pas filtering toe op alle meetpunten. Selecteer alleen de waarnemingsputten.
    Obj_Meetpunt_overig = Obj_Meetpunt[Obj_Meetpunt['meetpuntsoort'] != 'waarnemingsput']
    Obj_Meetpunt = Obj_Meetpunt[Obj_Meetpunt['meetpuntsoort'] == 'waarnemingsput']
    
    ## Importeer alle maaiveldhoogtes uit Objectenbeheer.
    Obj_Maaiveld = pd.read_excel(Loc_Objectbeheer, sheet_name='Maaiveldaanpassing')
    Maaiveld_DF = Import_ObjMaaiveldhoogtes(Obj_Meetpunt, Obj_Maaiveld)
    
    ## Importeer informatie over instanties uit Objectenbeheer
    Obj_Instantie, Obj_Meetpunt = Import_Instantie(Obj_Meetpunt, Loc_Objectbeheer)
    
    ## Importeer informatie over filters uit Objectenbeheer
    Obj_Filter = pd.read_excel(Loc_Objectbeheer, sheet_name='Filter')


    ## Selecteer alle relevante informatie van de meetpunten en filters.
    ## Bijv naamcodes, aantal filters, dieptes filters en coördinaten.
    Obj_MP = Obj_Meetpunt.copy()
    Obj_MP = Obj_MP[['id', 'business_id', 'olga_code', 'nitg_code', 'coordinaat_x', 'coordinaat_y', 'meetpuntstatus', 'aantal_filters', 'meetroute_id', 'eigenaar_meetpunt_id', 'opdrachtgevende_instantie_id', 'beherende_instantie_id', 'waarnemende_instantie_id']]
    Obj_Filt = Obj_Filter.copy()
    Obj_Filt = Obj_Filt[['id','meetpunt_id','filternummer','business_id','nitg_code','diepte_bovenkant_filter','diepte_onderkant_filter']]

    ## Hernoem de namen van enkele columns, zodat de column-namen van meetpunten en filters corresponderen.
    Obj_MP = Obj_MP.rename(columns={'id':'MP_id', 'coordinaat_x':'X_rd', 'coordinaat_y':'Y_rd', 'meetroute_id':'Meetroute_id'})
    Obj_Filt = Obj_Filt.rename(columns={'id':'Filt_id', 'meetpunt_id':'MP_id', 'diepte_bovenkant_filter':'Filt_BK', 'diepte_onderkant_filter':'Filt_OK'})

    ## Join van tabellen vd meetpunten en filters en voeg maaiveldhoogte toe
    Obj_join = Obj_MP.join(other=Obj_Filt.set_index('MP_id'), on='MP_id', lsuffix='_MP', rsuffix='_Filt')
    Obj_join = Obj_join.join(other=Maaiveld_DF.set_index('MP_id'), on='MP_id', lsuffix='_MP', rsuffix='_MV')
    Obj_join = Obj_join.rename(columns={'MV_Objectbeheer':'MP_Maaiveld'})
    Obj_join = Obj_join.sort_values(['MP_id','filternummer'], ascending=[True, True])   # Sorteer obv 1. meetpunt ID en 2. vervolgens filter nummer
    
    # Conversie van de Filters tabel naar gewenst format
    Obj_Filters = Obj_join[['MP_id', 'aantal_filters', 'Filt_id', 'filternummer', 'MP_Maaiveld', 
                            'Filt_BK', 'Filt_OK', 'business_id_MP', 'olga_code', 'nitg_code_MP',
                            'meetpuntstatus', 'Meetroute_id', 'X_rd', 'Y_rd', 'eigenaar_meetpunt_id', 
                            'opdrachtgevende_instantie_id', 'beherende_instantie_id', 'waarnemende_instantie_id']]
    Obj_Filters = Obj_Filters.rename(columns={'filternummer':'Filt_N', 'aantal_filters':'Nfilters',
                                              'business_id_MP':'Business_id', 'olga_code':'Olga_code',
                                              'nitg_code_MP':'NITG_code', 'meetpuntstatus':'Status',
                                              'X_rd':'X', 'Y_rd':'Y', 'eigenaar_meetpunt_id':'Eigenaar',
                                              'opdrachtgevende_instantie_id':'Opdrachtgever', 
                                              'beherende_instantie_id':'Beheerder', 'waarnemende_instantie_id':'Waarnemer'})
    Obj_Filters = Obj_Filters.reset_index(drop=True)
        
    return Obj_Filters

def data_cleaning(Obj_Filters, path_Output):
    ## Save totale lijst
    Obj_Filters.to_excel(path_Output + '\\0_VitensFilters_Totaal.xlsx', index=False)
    Obj_Filters_clean = Obj_Filters.copy()

    ## Save vervallen filters
    Obj_Filters_vervallen = Obj_Filters.loc[Obj_Filters.loc[:, 'Status'] == 'vervallen'].copy()
    Obj_Filters_vervallen.loc[:, 'Opmerking'] = 'Status vervallen'
    Obj_Filters_vervallen.to_excel(path_Output + '\\1_VitensFilters_vervallen.xlsx', index=False)
    Obj_Filters_clean = Obj_Filters_clean.loc[Obj_Filters_clean.loc[:, 'Status'] != 'vervallen']
    
    ## Save lijst met verkeerde coördinaten.
    Obj_Filters_coordinatenfoutief = Obj_Filters.loc[(Obj_Filters.loc[:, 'X'] <= 100000) | (Obj_Filters.loc[:, 'Y'] <= 400000)].copy()
    Obj_Filters_coordinatenfoutief.loc[:, 'Opmerking'] = 'Foutieve coördinaten'
    Obj_Filters_coordinatenfoutief.to_excel(path_Output + '\\2_Peilfilters_FoutieveCoördinaten.xlsx', index=False)
    Obj_Filters_clean = Obj_Filters_clean.loc[(Obj_Filters_clean.loc[:, 'X'] > 100000) & (Obj_Filters_clean.loc[:, 'Y'] > 400000)]
    
    ## Save lijst met verkeerde maaiveldhoogte.
    Obj_Filters_maaiveldfoutief = Obj_Filters.loc[(Obj_Filters.loc[:, 'MP_Maaiveld'] <= -5) | (Obj_Filters.loc[:, 'MP_Maaiveld'] >= 100) | (Obj_Filters.loc[:, 'MP_Maaiveld'] == 0) | np.isnan(Obj_Filters.loc[:, 'MP_Maaiveld'])].copy()
    Obj_Filters_maaiveldfoutief.loc[:, 'Opmerking'] = 'Foutieve maaiveldhoogte'
    Obj_Filters_maaiveldfoutief.to_excel(path_Output + '\\3_Peilfilters_FoutiefMaaiveld.xlsx', index=False)
    Obj_Filters_clean = Obj_Filters_clean.loc[(Obj_Filters_clean.loc[:, 'MP_Maaiveld'] > -5) & (Obj_Filters_clean.loc[:, 'MP_Maaiveld'] < 100) & (Obj_Filters_clean.loc[:, 'MP_Maaiveld'] != 0) & ~np.isnan(Obj_Filters_clean.loc[:, 'MP_Maaiveld'])]

    ## Save lijst met peilfilters met Foutieve filterdiepte.
    Obj_Filters_filterfoutief = Obj_Filters.loc[np.isnan(Obj_Filters.loc[:, 'Filt_BK']) | np.isnan(Obj_Filters.loc[:, 'Filt_OK']) | (Obj_Filters.loc[:, 'Filt_BK'] <= 0) | (Obj_Filters.loc[:, 'Filt_OK'] <= 0) | (Obj_Filters.loc[:, 'Filt_BK'] >= 600) | (Obj_Filters.loc[:, 'Filt_OK'] >= 600) | (abs(Obj_Filters.loc[:, 'Filt_BK'] - Obj_Filters.loc[:, 'Filt_OK']) <= 0.5) | (abs(Obj_Filters.loc[:, 'Filt_BK'] - Obj_Filters.loc[:, 'Filt_OK']) >= 5) | (Obj_Filters.loc[:, 'Filt_BK'] <= 0.5)].copy()
    Obj_Filters_filterfoutief.loc[:, 'Opmerking'] = 'Foutieve filterdiepte'
    Obj_Filters_filterfoutief.to_excel(path_Output + '\\4_Peilfilters_FoutieveFilterDiepte.xlsx', index=False)
    
    ## a: Ontbrekende filterdieptes tov Maaiveld.
    Obj_Filters_ontbrekendediepte = Obj_Filters.loc[np.isnan(Obj_Filters.loc[:, 'Filt_BK']) | np.isnan(Obj_Filters.loc[:, 'Filt_OK'])].copy()
    Obj_Filters_ontbrekendediepte.to_excel(path_Output + '\\4a_Peilfilters_OntbrekendeFilterDieptes.xlsx', index=False)
    Obj_Filters_clean = Obj_Filters_clean.loc[~np.isnan(Obj_Filters_clean.loc[:, 'Filt_BK']) & ~np.isnan(Obj_Filters_clean.loc[:, 'Filt_OK'])]
    
    ## b:  Negatieve filterdieptes tov Maaiveld.
    Obj_Filters_negatievediepte = Obj_Filters.loc[(Obj_Filters.loc[:, 'Filt_BK'] <= 0) | (Obj_Filters.loc[:, 'Filt_OK'] <= 0)].copy()
    Obj_Filters_negatievediepte.to_excel(path_Output + '\\4b_Peilfilters_NegatieveFilterDieptes.xlsx', index=False)
    Obj_Filters_clean = Obj_Filters_clean.loc[(Obj_Filters_clean.loc[:, 'Filt_BK'] > 0) & (Obj_Filters_clean.loc[:, 'Filt_OK'] > 0)]

    ## c:  Extreme filterdieptes tov Maaiveld. 
    Obj_Filters_extremediepte = Obj_Filters.loc[(Obj_Filters.loc[:, 'Filt_BK'] >= 600) | (Obj_Filters.loc[:, 'Filt_OK'] >= 600)].copy()
    Obj_Filters_extremediepte.to_excel(path_Output + '\\4c_Peilfilters_ExtremeFilterDieptes.xlsx', index=False)
    Obj_Filters_clean = Obj_Filters_clean.loc[(Obj_Filters_clean.loc[:, 'Filt_BK'] < 600) & (Obj_Filters_clean.loc[:, 'Filt_OK'] < 600)]
    
    ## d: Foutieve filterlengtes
    Obj_Filters_filterlengtefoutief = Obj_Filters.loc[(abs(Obj_Filters.loc[:, 'Filt_BK'] - Obj_Filters.loc[:, 'Filt_OK']) <= 0.5) | (abs(Obj_Filters.loc[:, 'Filt_BK'] - Obj_Filters.loc[:, 'Filt_OK']) >= 5)].copy()
    Obj_Filters_filterlengtefoutief.to_excel(path_Output + '\\4d_Peilfilters_FoutieveFilterLengte.xlsx', index=False)
    Obj_Filters_clean = Obj_Filters_clean.loc[(abs(Obj_Filters_clean.loc[:, 'Filt_BK'] - Obj_Filters_clean.loc[:, 'Filt_OK']) > 0.5) & (abs(Obj_Filters_clean.loc[:, 'Filt_BK'] - Obj_Filters_clean.loc[:, 'Filt_OK']) < 5)]
    
    ## e: Ondiepe filters
    Obj_Filters_zeerondiepfilter = Obj_Filters.loc[(Obj_Filters.loc[:, 'Filt_BK'] <= 0.5) & (Obj_Filters.loc[:, 'Filt_BK'] > 0)].copy()
    Obj_Filters_zeerondiepfilter.to_excel(path_Output + '\\4e_Peilfilters_ZeerOndiepFilter.xlsx', index=False)
    Obj_Filters_clean = Obj_Filters_clean.loc[Obj_Filters_clean.loc[:, 'Filt_BK'] > 0.5]
    

    ## Save totaallijst met alle foutieve gefilterde data.
    Obj_Filters_foutief = pd.DataFrame()
    Obj_Filters_foutief = Obj_Filters_foutief.append(Obj_Filters_coordinatenfoutief)
    Obj_Filters_foutief = Obj_Filters_foutief.append(Obj_Filters_maaiveldfoutief)
    Obj_Filters_foutief = Obj_Filters_foutief.append(Obj_Filters_filterfoutief)
    Obj_Filters_foutief = Obj_Filters_foutief.drop_duplicates(subset=['MP_id', 'Filt_id'], keep='first')
    
    Obj_Filters_gefilterd = Obj_Filters_foutief.copy()
    Obj_Filters_gefilterd = Obj_Filters_gefilterd.append(Obj_Filters_vervallen)
    Obj_Filters_gefilterd = Obj_Filters_gefilterd.drop_duplicates(subset=['MP_id', 'Filt_id'], keep='first')

    return Obj_Filters_clean, Obj_Filters_gefilterd, Obj_Filters_vervallen, Obj_Filters_foutief
