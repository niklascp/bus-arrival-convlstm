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

    grouping = data[data['LinkTravelTime'].notnull()].sort_values('LineDirectionLinkOrder').groupby('LinkRef', sort = False)
    for link_ref, data_link in grouping:
        # Fit outlier bounds using MAD
        median = data_link.groupby('DowTimeRef')['LinkTravelTime'].median()
        error = pd.concat([data_link['DowTimeRef'], np.abs(data_link['LinkTravelTime'] - median[data_link['DowTimeRef']].values)], axis = 1)
        mad = 1.4826 * error.groupby('DowTimeRef')['LinkTravelTime'].median()
        
        _low = median - 5 * mad
        _upr = median + 5 * mad
        mask = (_low[data_link['DowTimeRef']].values < data_link['LinkTravelTime']) & (data_link['LinkTravelTime'] < _upr[data_link['DowTimeRef']].values)
        data_link_no = data_link[mask]
        
        _mean = data_link_no.groupby('DowTimeRef')["LinkTravelTime"].mean()
        means[link_ref] = _mean
        low[link_ref] = _low
        upr[link_ref] = _upr
        #scales[k] = v_[(low[k] < v_['LinkTravelTime']) & (v_['LinkTravelTime'] < upr[k])]['LinkTravelTime'].std()
        scales[link_ref] = 1
    
    ix = pd.date_range('1970-01-01', '1970-01-08', freq = ref_freq, closed = 'left')
    means_df = pd.DataFrame(data = means, index = ix).interpolate()
    low_df = pd.DataFrame(data = low, index = ix).interpolate()
    upr_df = pd.DataFrame(data = upr, index = ix).interpolate()
    
    if smooth >= 1:
        means_df = means_df.rolling(window = smooth, center = True).mean()
        
    # Fill NaNs    
    means_df = means_df.fillna(method='pad').fillna(method='bfill')
    low_df = low_df.fillna(method='pad').fillna(method='bfill')
    upr_df = upr_df.fillna(method='pad').fillna(method='bfill')
    
    return (means_df, scales, low_df, upr_df)

def remove_outliers(data, low, upr): 
    _low = low.lookup(data['DowTimeRef'], data['LinkRef'])
    _upr = upr.lookup(data['DowTimeRef'], data['LinkRef'])
    mask = ((_low < data['LinkTravelTime']) & (data['LinkTravelTime'] < _upr))
    data = data.loc[mask].copy()
    return data, (~mask).sum()

def transform(data, means_df, scales, freq = '15min'):
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

def roll(ix, ts, removed_mean, removed_scale, w, lags, preds):
    X = np.stack([np.roll(ts, i, axis = 0) for i in range(lags, 0, -1)], axis = 1)[lags:-preds,]
    Y = np.stack([np.roll(ts, -i, axis = 0) for i in range(0, preds, 1)], axis = 1)[lags:-preds,]
    Y_ix = ix[lags:-preds]
    Y_mean = np.stack([np.roll(removed_mean, -i, axis = 0) for i in range(0, preds, 1)], axis = 1)[lags:-preds,]
    Y_scale = np.stack([np.roll(removed_scale, -i, axis = 0) for i in range(0, preds, 1)], axis = 1)[lags:-preds,]
    w_y = np.stack([np.roll(w, -i, axis = 0) for i in range(0, preds, 1)], axis = 1)[lags:-preds,]

    return X, Y, Y_ix, Y_mean, Y_scale, w_y