"""

Interpolate the NSIDC Ice Motion vectors to the ECCO grid. In addition, computes the
drift speed magnitude and adds u_east and v_north vectors -- the original u and v
are relative to the NSIDC EASE grid.

"""

import xarray as xr
import numpy as np
import xesmf

gridloc = '/Volumes/Research/ENG_Wilhelmus_Shared/group/ECCO/ecco-geometry/'
ecco_grid = xr.open_dataset(gridloc + 'GRID_GEOMETRY_ECCO_V4r4_native_llc0090.nc')

dataloc = '/Volumes/Research/ENG_Wilhelmus_Shared/group/ECCO/nsidc-daily-seaice-motion/'
saveloc = '../../data/'
variables = ['u', 'v', 'u_east', 'v_north', 'speed', 'icemotion_error_estimate']

if False:
    for year in range(1992, 2018):
        ds_nsidc = xr.open_dataset(dataloc + 'icemotion_daily_nh_25km_{y}0101_{y}1231_v4.1.nc'.format(y=1992))
        # Convert longitude to radians
        lon_radians = np.radians(ds_nsidc['longitude'])
        
        # Compute the new zonal and meridional components
        ds_nsidc['u_east'] = ds_nsidc['u'] * np.cos(lon_radians) + ds_nsidc['v'] * np.sin(lon_radians)
        ds_nsidc['v_north'] = -ds_nsidc['u'] * np.sin(lon_radians) + ds_nsidc['v'] * np.cos(lon_radians)
        ds_nsidc['speed'] = np.sqrt(ds_nsidc['u']**2 + ds_nsidc['v']**2)
        
        keep_tiles = [2, 5, 6, 7, 10]
        tile_results = []
        for tile in keep_tiles:
            longrid = ecco_grid.sel(tile=tile).XC.data
            latgrid = ecco_grid.sel(tile=tile).YC.data
            ds_out = xr.Dataset(coords={'lon': (('j', 'i'), longrid),
                                        'lat': (('j', 'i'), latgrid)})
            results = []
            for var in variables:
                lon = ds_nsidc.longitude.data
                lat = ds_nsidc.latitude.data
                offset = 1e2
                ds_in = xr.Dataset({var: (('time', 'j', 'i'), ds_nsidc[var].data + offset)},
                                coords={'time': ds_nsidc['time'].data,
                                        'lon': (('j', 'i'), lon),
                                        'lat': (('j', 'i'), lat)})
                regridder = xesmf.Regridder(ds_in, ds_out, "bilinear")
                regridded_data = regridder(ds_in[var]).rename(var)  # Name the DataArray
                regridded_data = regridded_data.where(regridded_data != 0)
                regridded_data = regridded_data - offset
                
                results.append(regridded_data)
            tile_results.append(xr.merge(results).assign_coords({'tile': tile}))
        ds_merged = xr.concat(tile_results, dim='tile')
        ds_merged = ds_merged.assign_coords({'XC': ecco_grid.XC, 'YC': ecco_grid.YC})
        ds_merged.attrs = ds_nsidc.attrs
        ds_merged.attrs['processing'] = 'Regridded to the ECCO model grid with bilinear interpolation using xESMF by Daniel Watkins, June 2026'
        ds_merged.to_netcdf(saveloc + '/nsidc_daily_sea_ice_velocity/nsidc_daily_ice_velocity_{y}.nc'.format(y=year),
                            encoding={v: {'zlib': True} for v in variables},
                            engine='netcdf4'
        )

# Compute monthly means
min_valid_frac = 0.9 # Only compute where there are enough valid vectors
monthly_means = []
for year in range(1992, 2018):
    with xr.open_dataset(saveloc + 'nsidc_daily_sea_ice_velocity/nsidc_daily_ice_velocity_{y}.nc'.format(y=year)) as ds:
        n = ds.resample({'time': '1MS'}).count()
        min_count = 0.9 * n.time.dt.daysinmonth
        include_cells = (n['speed'] > min_count)
        ds_masked = ds.where(include_cells)
        monthly_means.append(ds_masked.resample({'time': '1MS'}).mean())

ds = xr.concat(monthly_means, dim='time')
ds.attrs['processing'] = ds.attrs['processing'] + '\n Monthly means computed for cells with at least 0.9*days_in_month valid vectors.'
ds.to_netcdf(saveloc + 'nsidc_monthly_sea_ice_velocity_1992-2017.nc',
                encoding={v: {'zlib': True} for v in variables},
                engine='netcdf4') 