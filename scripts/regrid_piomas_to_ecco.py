"""

Interpolate the NOAA/NSIDC sea ice concentration data to the ECCO grid.
Uses nearest-neighbor interpolation so as not to smear mask values into the data.

"""

import xarray as xr
import numpy as np
import xesmf
import pyproj
import os


gridloc = '/Volumes/Research/ENG_Wilhelmus_Shared/group/ECCO/ecco-geometry/'
ecco_grid = xr.open_dataset(gridloc + 'GRID_GEOMETRY_ECCO_V4r4_native_llc0090.nc')

dataloc = '/Volumes/Research/ENG_Wilhelmus_Shared/group/ECCO/piomas/piomas_ice_thickness.nc'

saveloc = '../../data/'

variables = ['heff']

# TBD: Copy code used early to concatenate PIOMAS data
# For now, starting with the monthly mean data, so only regridding is needed.

ds = xr.open_dataset(dataloc)
keep_tiles = [2, 5, 6, 7, 10]
tile_results = []
for tile in keep_tiles:
    longrid = ecco_grid.sel(tile=tile).XC.data
    latgrid = ecco_grid.sel(tile=tile).YC.data
    ds_out = xr.Dataset(coords={'lon': (('j', 'i'), longrid),
                                'lat': (('j', 'i'), latgrid)})
    results = []
    for var in variables:
        lon = ds.lon.data
        lat = ds.lat.data
        ds_in = xr.Dataset({var: (('time', 'j', 'i'), ds[var].data)},
                        coords={'time': ds['time'].data,
                                'lon': (('j', 'i'), lon),
                                'lat': (('j', 'i'), lat)})
        regridder = xesmf.Regridder(ds_in, ds_out, "nearest_s2d", unmapped_to_nan=True)
        regridded_data = regridder(ds_in[var]).rename(var)
        results.append(regridded_data)

    tile_results.append(xr.merge(results).assign_coords({'tile': tile}))
ds_merged = xr.concat(tile_results, dim='tile', coords='different')
ds_merged = ds_merged.assign_coords({'XC': ecco_grid.XC, 'YC': ecco_grid.YC})
ds_merged.attrs = ds.attrs
ds_merged.attrs['processing'] = 'Regridded to the ECCO model grid with bilinear interpolation using xESMF by Daniel Watkins, June 2026'
ds_merged.attrs['final_projection'] = 'ECCO grid'

ds_merged.to_netcdf(saveloc + 'piomas_monthly_sea_ice_thickness.nc',
                    encoding={v: {'zlib': True} for v in variables},
                     engine='netcdf4')
