import numpy as np
import pandas as pd

from scipy.stats import rankdata

def prep_data(file, sep = ';', ref_freq = '15min'):
    data = pd.read_csv(file, sep)

    data.sort_values('DateTime', inplace = True)

    # Add a reference date for grouping similar measurements
    ix = pd.DatetimeIndex(pd.to_datetime(data['DateTime'])).floor(ref_freq)
    
    data["DateTimeRef"] = ix
    data["DowTimeRef"] = rankdata(data['DayOfWeek'].values * 10000 + ix.hour*100 + ix.minute, 'dense')
    
    return data

def fit_scale(data, smooth = 7):
    means = { }
    scales = { }
    low = { }
    upr = { }

    for k, v in data[~np.isnan(data['LinkTravelTime'])].sort_values('LineDirectionLinkOrder').groupby('LinkRef', sort = False):
        median = np.median(v['LinkTravelTime']);
        mad = 1.4826 * np.median(np.abs(v['LinkTravelTime'] - median))
        low[k] = max(median - 3 * mad, 0)
        upr[k] = median + 3 * mad

        mean = v[(low[k] < v['LinkTravelTime']) & (v['LinkTravelTime'] < upr[k])].groupby("DowTimeRef")["LinkTravelTime"].mean()
        mean = mean.interpolate().rolling(window = smooth, center = True).mean()
        means[k] = mean
        #scales[k] = v_[(low[k] < v_['LinkTravelTime']) & (v_['LinkTravelTime'] < upr[k])]['LinkTravelTime'].std()
        scales[k] = 1
        
    means_df = pd.DataFrame(data = means).fillna(method='pad').fillna(method='bfill')
    return (means_df, scales, low, upr)

def remove_outliers(data, low, upr): 
    _low = data['LinkRef'].apply(lambda k: low[k])
    _upr = data['LinkRef'].apply(lambda k: upr[k])
    mask = ~(_low < data['LinkTravelTime']) & (data['LinkTravelTime'] < _upr)
    data.loc[mask, 'LinkTravelTime'] = np.nan
    return mask.sum()