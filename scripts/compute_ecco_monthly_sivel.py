""" Computing monthly means from the ECCO daily mean data.

Sea ice velocity
- Select Arctic regions and combine daily data into individual years
- Load the daily data of SIarea for the year
- Mask the sea ice velocity where the SIarea is 0
- Compute u_east and u_north
- Compute daily drift speed
- Save yearly files
- Compute monthly means and compile all years
"""
import xarray as xr
import numpy as np
import pandas as pd
import os

# Necessary when using parallel computing and writing
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'

# These 5 tiles cover all Arctic dates
keep_tiles = [2, 5, 6, 7, 10]

# Set to False if the daily data has already been subsetted
sic_daily = False

#### Sea ice concentration and thickness ####
dataloc = '/Volumes/Research/ENG_Wilhelmus_Shared/group/ECCO/ecco-seaice-concentration/'

# Data is organized Year / Month / Files
saveloc = '../../data/' # One directory up, so not in the GitHub repo

if sic_daily:
    print("Subsetting daily sea ice concentration and thickness")
    
    monthly_means = []
    for year in np.arange(1992, 2018):
        print(year)
        daily_data = []
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
            daily_data.append(month_ds)
            
        ds = xr.concat(daily_data, dim='time').sortby('time')

        # # Update time axis -- otherwise it's just 0, 1, 2, ..., 11
        # ds['time'] = pd.date_range('{y}-01-01'.format(y=year),
        #                              freq='1MS', periods=12)
        
        
        ds.to_netcdf(saveloc + "ecco_daily_sea_ice_concentration/ecco_daily_mean_sea_ice_concentration_thickness_" + str(year) + '.nc',
                     encoding={v: {'zlib': True} for v in ds.variables},
                     engine='netcdf4')
        ds.close()
        daily_data = []

print("Merging year files")
monthly_means = []
# Sea ice concentration and thickness are well-defined for the full range (0-1),
# so we don't need to do additional subsetting for monthly averages
for year in range(1992, 2018):
    with xr.open_dataset(saveloc + 'ecco_daily_sea_ice_concentration/ecco_daily_mean_sea_ice_concentration_thickness_{y}.nc'.format(y=year)) as ds:
        monthly_means.append(ds.resample({'time': '1MS'}).mean())
ds = xr.concat(monthly_means, dim='time')
ds.attrs['processing'] = 'Monthly means computed from daily means, Daniel Watkins and Ashfaq Ahmed, June 2026'
ds.to_netcdf(saveloc + 'ecco_monthly_sea_ice_concentration_thickness_1992-2017.nc',
                encoding={v: {'zlib': True} for v in variables},
                engine='netcdf4') 