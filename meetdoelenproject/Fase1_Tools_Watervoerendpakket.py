'''
'''

#%% Import packages
import imod
import numpy as np

#%% 
def IDF_GPStoPixel(GPS_loc, Rast_coords, dXY):
    '''
    Zoekt voor een gegeven coördinaat (x of y), de bijbehorende pixel in het raster. 
        
    GPS_loc is de gegeven X- of Y-coördinaat
    Rast_coords is een array met X- of Y-coördinaten van de pixels in het raster.
    dXY is de breedte/hoogte van de pixels in het raster. 
    '''
    
    for XY in Rast_coords:
        if (GPS_loc >= XY - 0.5 * dXY) & (GPS_loc <= XY + 0.5 * dXY):
            Pixel_raster = np.argwhere(Rast_coords == XY)[0,0]
            break
        else:
            Pixel_raster = False
    
    return Pixel_raster


def Import_Lagenmodel(Model=['AZURE',9], ModelPath=r'C:\Users\mulderma\Documents\DATA\\'):
    '''
    Importeren van Lagenmodel voor gegeven grondwatermodel met N lagen.
    '''
    
    ## Opzetten van lege dictionaries waarin data per laag wordt opgeslagen.
    Tops = {}
    Bottoms = {}
    KDs = {}
    Cs = {}
    
    ## for loop die iedere modellaag doorloopt, o.b.v. opgegeven aantal lagen.
    for Layer in np.linspace(1,Model[1],Model[1]):
        
        ## Inlezen van tops data. 
        Topn_path = ModelPath + str(Model[0]) + '\\Layers' + '\\WVP_Top_L' + str(int(Layer)) + '.idf'
        Topn_data = imod.idf.open_dataset(Topn_path)  # Top van WVP, laag n. 
        Topn_Key = list(Topn_data.keys())[0]
        Tops['Layer_'+str(int(Layer))] = Topn_data[Topn_Key].values[0,:,:]
        
        ## Inlezen van bots data.
        Botn_path = ModelPath + str(Model[0]) + '\\Layers' + '\\WVP_Bot_L' + str(int(Layer)) + '.idf'
        Botn_data = imod.idf.open_dataset(Botn_path)  # Bodem van WVP, laag n.
        Botn_Key = list(Botn_data.keys())[0]
        Bottoms['Layer_'+str(int(Layer))] = Botn_data[Botn_Key].values[0,:,:]
        
        ## Inlezen van KD data.
        KDn_path = ModelPath + str(Model[0]) + '\\KD' + '\\KD_L' + str(int(Layer)) + '.idf'
        KDn_data = imod.idf.open_dataset(KDn_path)  # KD van WVP laag n
        KDn_Key = list(KDn_data.keys())[0]
        KDs['Layer_'+str(int(Layer))] = KDn_data[KDn_Key].values[0,:,:]
        
        ## Inlezen van C data. Rekening houdend dat de onderste C-laag niet bestaat, aangezien dit de geohydrologische basis is. 
        if Layer != Model[1]:
            Cn_path = ModelPath + str(Model[0]) + '\\C' + '\\C_L' + str(int(Layer)) + '.idf'
            Cn_data = imod.idf.open_dataset(Cn_path)
            C_Key = list(Cn_data.keys())[0]
            Cs['Layer_'+str(int(Layer))] = Cn_data[C_Key].values[0,:,:]
    
    # Tenslotte worden ook de X en Y locaties opgeslagen. In dit geval van de laatste Tops-laag. 
    X = Topn_data[Topn_Key].x
    Y = Topn_data[Topn_Key].y
    return Tops, Bottoms, KDs, Cs, X, Y

def Import_WatervoerendPakket(Peilfilters, Model=['AZURE',9], LayerModels_path = r'C:\Users\mulderma\Documents\DATA\\'):
    '''
    Functie die voor ieder peilfilter uitleest in welke modellaag dat betreffende filter staat.
    '''
    
    ## Stap A. Inlezen van lagenmodel.
    WVP_Tops, WVP_Bots, WVP_KDs, WVP_Cs, X, Y = Import_Lagenmodel(Model=Model, ModelPath=LayerModels_path)
    
    ## Stap B. Aanvullen van dataframe met kolommen.
    Peilfilters['WVP'] = ''
    Peilfilters['WVP_BK'] = ''
    Peilfilters['WVP_OK'] = ''
    Peilfilters['SDL'] = ''
    Peilfilters['SDL_BK'] = ''
    Peilfilters['SDL_OK'] = ''
    Peilfilters['FilterMEAN'] = ''
    Peilfilters['C_boven'] = ''
    Peilfilters['WVP_nieuw'] = ''
    
    ## Stap 4C. Per peilfilter informatie inladen van bijbehorende WVP
    for i in Peilfilters.index:
        
        ## 4Ca. Uitlezen Pixelnummer, inclusief met maaiveldhoogte en filter dieptes.
        Pix_X = IDF_GPStoPixel(Peilfilters.loc[i, 'X'],X.values,X.dx.values)
        Pix_Y = IDF_GPStoPixel(Peilfilters.loc[i, 'Y'],Y.values,Y.dx.values)
        
        Filter_MV = Peilfilters.loc[i, 'MP_Maaiveld']
        Filter_BK_NAP = Filter_MV - Peilfilters.loc[i, 'Filt_BK']
        Filter_OK_NAP = Filter_MV - Peilfilters.loc[i, 'Filt_OK']
        Filter_mean = (Filter_OK_NAP + Filter_BK_NAP) / 2
        
        ## 4Cb. Toewijzen filternr aan watervoerend pakket.
        for Layer in np.linspace(1,Model[1],Model[1]):
            WVP_Top_Filter = WVP_Tops['Layer_'+str(int(Layer))][Pix_Y,Pix_X]
            WVP_Bot_Filter = WVP_Bots['Layer_'+str(int(Layer))][Pix_Y,Pix_X]
            
            ## Indien filter onder top van WVP en boven het bot van WVP zit, behoord deze tot dat WVP.
            if (Filter_mean < WVP_Top_Filter) & (Filter_mean >= WVP_Bot_Filter):
                Peilfilters.loc[i, 'WVP'] = str(int(Layer))
                Peilfilters.loc[i, 'WVP_BK'] = WVP_Top_Filter
                Peilfilters.loc[i, 'WVP_OK'] = WVP_Bot_Filter
                continue
            
            ## Indien bij eerste modellaag en filter ligt boven Top van WVP, dan toewijzen aan WVP 1. 
            if Layer == 1:
                if Filter_mean > WVP_Top_Filter:
                    Peilfilters.loc[i, 'WVP'] = str(int(Layer))
                    Peilfilters.loc[i, 'WVP_BK'] = WVP_Top_Filter
                    Peilfilters.loc[i, 'WVP_OK'] = WVP_Bot_Filter
                    continue
                
            ## Indien bij laatste modellaag en filter ligt onder bot van WVP, dan toewijzen aan laagste WVP. 
            if Layer == Model[1]:
                if Filter_mean < WVP_Bot_Filter:
                    Peilfilters.loc[i, 'WVP'] = str(int(Layer))
                    Peilfilters.loc[i, 'WVP_BK'] = WVP_Top_Filter
                    Peilfilters.loc[i, 'WVP_OK'] = WVP_Bot_Filter
                    continue
            
            ## 4Cc. 
            ## In het geval dat het midden van het filter in het slecht doorlatend pakket ligt.
            if Layer < Model[1]:
                ## Bekijken wat top en bottom van SDL zijn. 
                SDL_Top_Filter = WVP_Bot_Filter
                SDL_Bot_Filter = WVP_Tops['Layer_'+str(int(Layer + 1))][Pix_Y,Pix_X]
                
                ## Extra controle om te zien of filter gemiddelde inderdaad tussen Top van SDl en bot van SDl ligt.
                if (Filter_mean < SDL_Top_Filter) & (Filter_mean > SDL_Bot_Filter):
                    Peilfilters.loc[i, 'SDL'] = str(int(Layer))
                    Peilfilters.loc[i, 'SDL_BK'] = SDL_Top_Filter
                    Peilfilters.loc[i, 'SDL_OK'] = SDL_Bot_Filter
                    Peilfilters.loc[i, 'FilterMEAN'] = Filter_mean
                    
                    ## Type A: Bovenkant filter zit in bovenliggende WVP, onderkant filter in SDL
                    if (Filter_BK_NAP > SDL_Top_Filter) & (Filter_OK_NAP > SDL_Bot_Filter):
                        Peilfilters.loc[i, 'WVP'] = str(int(Layer))
                        Peilfilters.loc[i, 'WVP_BK'] = WVP_Top_Filter
                        Peilfilters.loc[i, 'WVP_OK'] = WVP_Bot_Filter
                    
                    ## Type B: Bovenkant filter zit in SDL, onderkant filter zit in onderliggende WVP
                    elif (Filter_BK_NAP < SDL_Top_Filter) & (Filter_OK_NAP < SDL_Bot_Filter):
                        Peilfilters.loc[i, 'WVP'] = str(int(Layer + 1))
                        Peilfilters.loc[i, 'WVP_BK'] = WVP_Tops['Layer_'+str(int(Layer + 1))][Pix_Y,Pix_X]
                        Peilfilters.loc[i, 'WVP_OK'] = WVP_Bots['Layer_'+str(int(Layer + 1))][Pix_Y,Pix_X]

                    ## Type C: Zowel bk filter zit in bovenliggende wvp en ok filter zit in onderliggende wvp.
                    ## Wijs buis toe aan wvp waarmee meeste overlap is. 
                    elif (Filter_BK_NAP > SDL_Top_Filter) & (Filter_OK_NAP < SDL_Bot_Filter):
                        Verschil_boven = Filter_BK_NAP - SDL_Top_Filter
                        Verschil_onder = SDL_Bot_Filter - Filter_OK_NAP
                        
                        if Verschil_boven > Verschil_onder:   ## Indien meer overlap met bovenliggende wvp, wijs toe aan wvp i.
                            Peilfilters.loc[i, 'WVP'] = str(int(Layer))
                            Peilfilters.loc[i, 'WVP_BK'] = WVP_Top_Filter
                            Peilfilters.loc[i, 'WVP_OK'] = WVP_Bot_Filter
                        elif Verschil_boven < Verschil_onder: ## Indien meer overlap met onderliggende wvp, wijs toe aan wvp i+1.
                            Peilfilters.loc[i, 'WVP'] = str(int(Layer + 1))
                            Peilfilters.loc[i, 'WVP_BK'] = WVP_Tops['Layer_'+str(int(Layer + 1))][Pix_Y,Pix_X]
                            Peilfilters.loc[i, 'WVP_OK'] = WVP_Bots['Layer_'+str(int(Layer + 1))][Pix_Y,Pix_X]
                        else:   ##Indien precies evenveel overlap,
                            continue
                    ## Type D: Peilbuis ligt geheel in slecht doorlatende laag.
                    ## Dichtsbijzijnde wvp wordt toegewezen. Echter lastig besluit of dit de juiste weg is!! op basis van boorstat bepalen??
                    else:
                        Verschil_boven = SDL_Top_Filter - Filter_BK_NAP
                        Verschil_onder = Filter_OK_NAP - SDL_Bot_Filter
                        
                        if Verschil_boven < Verschil_onder:
                            Peilfilters.loc[i, 'WVP'] = str(int(Layer))
                            Peilfilters.loc[i, 'WVP_BK'] = WVP_Top_Filter
                            Peilfilters.loc[i, 'WVP_OK'] = WVP_Bot_Filter
                        elif Verschil_boven > Verschil_onder:
                            Peilfilters.loc[i, 'WVP'] = str(int(Layer + 1))
                            Peilfilters.loc[i, 'WVP_BK'] = WVP_Tops['Layer_'+str(int(Layer + 1))][Pix_Y,Pix_X]
                            Peilfilters.loc[i, 'WVP_OK'] = WVP_Bots['Layer_'+str(int(Layer + 1))][Pix_Y,Pix_X]
                        else:   ##Indien precies evenveel overlap,
                            continue
        
        ## 4Cd. Indien filter bijv in WVP is toegewezen, alsnog toewijzen aan WVP 1 indien er geen weerstand boven zit. Hij is in feite dus freatisch namelijk!                
        C_sum = 0
        WVP = int(Peilfilters.loc[i, 'WVP'])
        if WVP == 1:
            C_sum = 0
            Peilfilters.loc[i, 'C_boven'] = C_sum
        else:
            for Layer in np.linspace(1, WVP - 1, WVP - 1):
                C_sum = C_sum + WVP_Cs['Layer_'+str(int(Layer))][Pix_Y,Pix_X]
            Peilfilters.loc[i, 'C_boven'] = C_sum
        
            if (WVP > 1) & (C_sum < 10):
                Peilfilters.loc[i, 'WVP_nieuw'] = 1
                Peilfilters.loc[i, 'WVP'] = 1
    Peilfilters['WVP'] = Peilfilters['WVP'].astype(np.float)        
    Peilfilters = Peilfilters.drop(axis='columns', labels=['WVP_BK', 'WVP_OK', 'SDL', 'SDL_BK', 'SDL_OK', 'FilterMEAN', 'C_boven', 'WVP_nieuw'])
    return Peilfilters