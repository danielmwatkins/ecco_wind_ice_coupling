""" Computing monthly means from the ECCO daily mean data.

Sea ice velocity
- Aggregate data into daily means for each year
- Only keep the Arctic tiles
- Mask data using SIArea
- TBD: Compute daily drift speed, compute direction in u_east, v_north

"""
import xarray as xr
import numpy as np
import pandas as pd
import os
import xgcm
import ecco_v4_py as ecco
from ecco_v4_py import get_llc_grid



# Necessary when using parallel computing and writing
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'

# These 5 tiles cover all Arctic dates
keep_tiles = [2, 5, 6, 7, 10]

# Set to True to run the computation for that variable
sic_daily = True

#### Sea ice concentration and thickness ####
dataloc = '/Volumes/Research/ENG_Wilhelmus_Shared/group/ECCO/ecco-seaice-velocity/'
grid_path = '/Volumes/Research/ENG_Wilhelmus_Shared/group/ECCO/ecco-geometry/GRID_GEOMETRY_ECCO_V4r4_native_llc0090.nc'
ecco_grid = xr.open_dataset(grid_path)
XGCM_grid = get_llc_grid(ecco_grid)


# Data is organized Year / Month / Files
saveloc = '../../data/' # One directory up, so not in the GitHub repo
if sic_daily:
    print("Subsetting daily sea ice velocity")
    
    for year in np.arange(1992, 2018):
        
        month_data = []
        for month in pd.date_range('{y}-01-01'.format(y=year), periods=12, freq='1MS'):
            daily_data = []
            print(year, month)
            files = os.listdir(dataloc + '{y}/{m}'.format(y=year, m=month.strftime('%b')))
            files.sort()
            files = [f for f in files if '.nc' in f]
            files = [dataloc + '{y}/{m}/'.format(y=year, m=month.strftime('%b')) + f for f in files]

            for file in files:
                with xr.open_dataset(file) as ds:
                    ds_merged = xr.merge((ecco_grid, ds), compat='no_conflicts').compute()
                    u_x = ds_merged['SIuice']
                    v_y = ds_merged['SIvice']
                    u_east, v_north = ecco.vector_calc.UEVNfromUXVY(u_x, v_y, ds_merged)
                    ds['u_east'] = u_east
                    ds['v_north'] = v_north
                    ds['speed'] = np.sqrt(u_east**2 + v_north**2)
                    daily_data.append(ds.sel(tile=keep_tiles)[['u_east', 'v_north', 'speed']])
            month_data.append(xr.concat(daily_data, dim='time'))
        ds = xr.concat(month_data, dim='time')
        ds.to_netcdf(saveloc + "ecco_daily_sea_ice_velocity/ecco_daily_mean_sea_ice_velocity_" + str(year) + '.nc',
                     encoding={v: {'zlib': True} for v in ds.variables},
                     engine='netcdf4')
        ds.close()

print("Merging year files")
monthly_means = []
for year in range(1992, 2018):
    with xr.open_dataset(saveloc + 'ecco_daily_sea_ice_velocity/ecco_daily_mean_sea_ice_velocity_{y}.nc'.format(y=year)) as ds:
        n = ds.resample({'time': '1MS'}).count()
        min_count = 0.9 * n.time.dt.daysinmonth
        include_cells = (n['speed'] > min_count)
        ds_masked = ds.where(include_cells)
        monthly_means.append(ds.resample({'time': '1MS'}).mean())
ds = xr.concat(monthly_means, dim='time')
ds.attrs['processing'] = 'Monthly means computed from daily means, Daniel Watkins and Ashfaq Ahmed, June 2026'
ds.to_netcdf(saveloc + 'ecco_monthly_sea_ice_velocity_1992-2017.nc',
                encoding={v: {'zlib': True} for v in ds.variables},
                engine='netcdf4') 