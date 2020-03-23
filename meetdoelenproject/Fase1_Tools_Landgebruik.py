'''
'''

#%% Import packages
import collections
import gdalnumeric
import gdal
import numpy as np

## GPS to Pixel
def Tiff_GPStoPixel(X_gps, Y_gps, GeoTrans):
    '''
    Retrieve row and column number of gps coordinate in raster
    '''
    
    UL_X = GeoTrans[0]
    UL_Y = GeoTrans[3]
    dx = GeoTrans[1]
    dy = GeoTrans[5]
    
    col = int((X_gps - UL_X) / dx)
    row = int((Y_gps - UL_Y) / dy)
    return row, col


def Import_Landgebruik(Peilfilters_UtrechtNoordHolland, Loc_LGNraster):
    '''
    Voor ieder peilfilter wordt bekeken wat het bijbehorende landgebruik is, o.b.v. LGN.
    '''
    
    ## Stap 5A.
    DF_Filters = Peilfilters_UtrechtNoordHolland.copy()
    DF_Filters.loc[:,'LGN'] = ''
    
    ## Stap 5B. Importeren van LGN
    LGN_Data = gdalnumeric.LoadFile(Loc_LGNraster)
    LGN_Image = gdal.Open(Loc_LGNraster)
    LGN_GeoTrans = LGN_Image.GetGeoTransform()
    
    ## Codes
    Landbouw = [1, 2, 3, 4, 5, 6, 7, 9, 10]
    Bebouwing = [8, 18]
    Natuur = [11, 12, 13, 14, 19]
    Overig = [0, 15, 16, 17]
    
    ## Stap 5C. Uitlezen per peilfilter.
    for i in DF_Filters.index:
        ## 5Ca. 
        Filter_X = DF_Filters.loc[i, 'X']
        Filter_Y = DF_Filters.loc[i, 'Y']
        Row, Col = Tiff_GPStoPixel(X_gps=Filter_X, Y_gps=Filter_Y, GeoTrans=LGN_GeoTrans)
        LGN_Type = LGN_Data[Row,Col]
        
        ## 5Cb.
        if LGN_Type in Landbouw:
            DF_Filters.loc[i, 'LGN'] = 'Landbouw'
        elif LGN_Type in Bebouwing:
            DF_Filters.loc[i, 'LGN'] = 'Bebouwing'
        elif LGN_Type in Natuur:
            DF_Filters.loc[i, 'LGN'] = 'Natuur'
        
        ## 5Cc.
        else:
            Array = list(LGN_Data[Row-2:Row+2,Col-2:Col+2].flatten())
            for Type in Overig:
                while Type in Array:
                    Array.remove(Type)
            if type(Array) != np.int32:
                LGN_Type = collections.Counter(Array).most_common(1)[0][0]
            if LGN_Type in Landbouw:
                DF_Filters.loc[i, 'LGN'] = 'Landbouw'
            elif LGN_Type in Bebouwing:
                DF_Filters.loc[i, 'LGN'] = 'Bebouwing'
            elif LGN_Type in Natuur:
                DF_Filters.loc[i, 'LGN'] = 'Natuur'
            
    return DF_Filters