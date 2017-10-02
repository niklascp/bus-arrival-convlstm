import numpy as np
import pandas as pd

from scipy.stats import rankdata

def prep_data(file, sep = ';', ref_freq = '15min'):
    data = pd.read_csv(file, sep)

    data.sort_values('DateTime', inplace = True)

    # Add a reference date for grouping similar measurements
    ix = pd.DatetimeIndex(pd.to_datetime(data['DateTime'])).floor(ref_freq)
    
    data["DateTimeRef"] = ix
    data["DowTimeRef"] = pd.to_datetime((data['DayOfWeek'].values - 1) * 24 * 60 * 60 + ix.hour * 60 * 60 + ix.minute * 60, unit = 's')
    
    return data

def fit_scale(data, smooth = 1, ref_freq = '15min'):
    means = { }
    scales = { }
    low = { }
    upr = { }

    for link_ref, v in data[~np.isnan(data['LinkTravelTime'])].sort_values('LineDirectionLinkOrder').groupby('LinkRef', sort = False):
        # Fit outlier bounds using MAD
        median = np.median(v['LinkTravelTime']);
        mad = 1.4826 * np.median(np.abs(v['LinkTravelTime'] - median))
        low[link_ref] = max(median - 2 * mad, 0)
        upr[link_ref] = median + 2 * mad
        no_outliers = v[(low[link_ref] < v['LinkTravelTime']) & (v['LinkTravelTime'] < upr[link_ref])]
        
        mean = no_outliers.groupby('DowTimeRef')["LinkTravelTime"].mean()
        means[link_ref] = mean
        #scales[k] = v_[(low[k] < v_['LinkTravelTime']) & (v_['LinkTravelTime'] < upr[k])]['LinkTravelTime'].std()
        scales[link_ref] = 1
    
    means_ix = pd.date_range('1970-01-01', '1970-01-08', freq = ref_freq, closed = 'left')
    means_df = pd.DataFrame(data = means, index = means_ix).interpolate()
    
    if smooth >= 1:
        means_df = means_df.rolling(window = smooth, center = True).mean()
        
    # Fill NaNs
    means_df = means_df.fillna(method='pad').fillna(method='bfill')
    
    return (means_df, scales, low, upr)

def remove_outliers(data, low, upr): 
    _low = data['LinkRef'].apply(lambda k: low[k])
    _upr = data['LinkRef'].apply(lambda k: upr[k])
    mask = ~((_low < data['LinkTravelTime']) & (data['LinkTravelTime'] < _upr))
    data = data.copy()
    data.loc[mask, 'LinkTravelTime'] = np.nan
    return data, mask.sum()

def transform(data, means_df, scales, low, upr, freq = '15min'):
    tss = { }
    ws = { }
    removed_mean = { }
    removed_scale = { }
    ks = []
    for k, v in data.sort_values('LineDirectionLinkOrder').groupby('LinkRef', sort = False):
        # Link Data Time Indexed
        link_time_ix = pd.DatetimeIndex(pd.to_datetime(v['DateTime']))    
        link_time_ixd = v.set_index(link_time_ix)
        
        # Link Reference Data Index
        ix_ref = link_time_ixd['DowTimeRef']  

        link_travel_time_k = link_time_ixd['LinkTravelTime'].resample(freq).mean()
        removed_mean[k] = pd.Series(data = means_df.loc[ix_ref, k].values, index = link_time_ix).resample(freq).mean()
        removed_scale[k] = pd.Series(data = np.repeat(scales[k], link_travel_time_k.shape[0]), index = link_travel_time_k.index)
        tss[k] = (link_travel_time_k - removed_mean[k].values) / removed_scale[k].values
        ws[k] = link_time_ixd['LinkTravelTime'].resample(freq).count()

        ks.append(k)
        
    ts = pd.DataFrame(data = tss).fillna(method='pad').fillna(0) # Link Travel Time Time Series
    df_removed_mean = pd.DataFrame(data = removed_mean, index = ts.index).fillna(method='pad').fillna(method='bfill') # Removed Mean from Link Travel Time
    df_removed_scale = pd.DataFrame(data = removed_scale, index = ts.index).fillna(method='pad').fillna(method='bfill')
    w = pd.DataFrame(data = ws).fillna(0) # Link Travel Time Weights, e.g. number of measurements
    return (ts.index, ts.values, df_removed_mean.values, df_removed_scale.values, w.values, ks)