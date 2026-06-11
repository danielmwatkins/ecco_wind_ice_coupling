""" Computing monthly means from the ECCO daily mean data.

Sea ice concentration and thickness
- Simple average into monthly files for each year
- Combine files into single monthly-mean-resolution file for 1992-2017
- Only keep the Arctic tiles
"""
import xarray as xr
import numpy as np
import pandas as pd
import os

# Necessary when using parallel computing and writing
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'

# These 5 tiles cover all Arctic dates
keep_tiles = [2, 5, 6, 7, 10]

# Set to True to run the computation for that variable
sic_monthly = False

#### Sea ice concentration and thickness ####
# Sea ice concentration and thickness are well-defined for the full range (0-1),
# so we don't need to do additional subsetting. 
dataloc = '/Volumes/Research/ENG_Wilhelmus_Shared/group/ECCO/ecco-seaice-concentration/'
# Data is organized Year / Month / Files
saveloc = '../../data/' # One directory up, so not in the GitHub repo
if sic_monthly:
    print("Computing mean sea ice concentration and thickness")
    
    monthly_means = []
    for year in np.arange(1992, 2018):
        print(year)
        for month in pd.date_range('{y}-01-01'.format(y=year), periods=12, freq='1MS'):
            files = os.listdir(dataloc + '{y}/{m}'.format(y=year, m=month.strftime('%b')))
            files.sort()
            files = [f for f in files if '.nc' in f]
            files = [dataloc + '{y}/{m}/'.format(y=year, m=month.strftime('%b')) + f for f in files]
    
            month_ds = xr.open_mfdataset(
                    files,
                    combine='by_coords',
                    parallel=False # Errors with multithreading here 
                ).sel(tile=keep_tiles)[['SIarea', 'SIheff']]
            
            monthly_means.append(month_ds.mean(dim='time'))
            month_ds.close()
            
        ds = xr.concat(monthly_means, dim='time').sortby('time')

        # Update time axis -- otherwise it's just 0, 1, 2, ..., 11
        ds['time'] = pd.date_range('{y}-01-01'.format(y=year),
                                     freq='1MS', periods=12)
        
        ds.attrs['processing'] = 'Monthly means computed from daily means, Daniel Watkins and Ashfaq Ahmed, June 2026'
        ds.to_netcdf(saveloc + "ecco_monthly_sea_ice_concentration_by_year/ecco_monthly_mean_sea_ice_concentration_thickness_" + str(year) + '.nc',
                     encoding={v: {'zlib': True} for v in ds.variables},
                     engine='netcdf4')
        ds.close()
        monthly_means = []

print("Merging year files")
concat_files = os.listdir(saveloc)
concat_files.sort()
concat_files = [saveloc + f for f in concat_files if '.nc' in f]

ds = xr.open_mfdataset(
                concat_files,
                combine='by_coords',
                compat='no_conflicts',
                parallel=False # Errors with multithreading here 
            )
ds.to_netcdf(saveloc + 'ecco_monthly_mean_sea_ice_concentration_thickness_1992-2017.nc',
                encoding={v: {'zlib': True} for v in ds.variables},
                engine='netcdf4')        
