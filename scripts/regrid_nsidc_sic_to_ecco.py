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

dataloc = '/Volumes/Research/ENG_Wilhelmus_Shared/group/ECCO/nsidc-daily-seaice-concentration/'
saveloc = '../../data/'


proj_LL = 'epsg:4326' # WGS 84 Ellipsoid
proj_XY = 'epsg:3413' # NSIDC Polar Stereographic
transform_to_ll = pyproj.Transformer.from_crs(proj_XY, proj_LL, always_xy=True)
transform_to_xy = pyproj.Transformer.from_crs(proj_LL, proj_XY, always_xy=True)
variables = ['sea_ice_concentration', 'cdr_seaice_conc', 'nsidc_bt_seaice_conc', 'nsidc_nt_seaice_conc', 'stdev_of_cdr_seaice_conc']

for year in range(1992, 2018):
    print("Loading data: {y}".format(y=year))

    files = os.listdir(dataloc + str(year))
    files = [dataloc + str(year) + '/' + f for f in files if 'nc' in f]
    files.sort()

    all_days = []
    for file in files:
        with xr.open_dataset(file) as ds_sic:
            all_days.append(ds_sic.swap_dims({'tdim': 'time'}).load())
    # Concatenate all SIC files
    ds_sic = xr.concat(all_days, dim='time')

    # Create meshgrid of x and y coordinates
    X, Y = np.meshgrid(ds_sic.xgrid.values, ds_sic.ygrid.values)

    # Transform from polar stereographic to latitude/longitude
    lon, lat = transform_to_ll.transform(X, Y)

    # Add lat and lon to dataset
    ds_sic = ds_sic.assign_coords({"lon": (("y", "x"), lon), "lat": (("y", "x"), lat)})
    ds_sic['sea_ice_concentration'] = ds_sic['cdr_seaice_conc'].where(ds_sic['cdr_seaice_conc'] <= 1)
    ds_sic = ds_sic.drop_vars('projection')
    ds_sic.attrs['initial_projection'] = 'EPSG:3413'

    keep_tiles = [2, 5, 6, 7, 10]
    tile_results = []
    for tile in keep_tiles:
        longrid = ecco_grid.sel(tile=tile).XC.data
        latgrid = ecco_grid.sel(tile=tile).YC.data
        ds_out = xr.Dataset(coords={'lon': (('j', 'i'), longrid),
                                    'lat': (('j', 'i'), latgrid)})
        results = []
        for var in variables:
            lon = ds_sic.lon.data
            lat = ds_sic.lat.data
            ds_in = xr.Dataset({var: (('time', 'j', 'i'), ds_sic[var].data)},
                            coords={'time': ds_sic['time'].data,
                                    'lon': (('j', 'i'), lon),
                                    'lat': (('j', 'i'), lat)})
            regridder = xesmf.Regridder(ds_in, ds_out, "nearest_s2d")
            regridded_data = regridder(ds_in[var]).rename(var)  # Name the DataArray
            results.append(regridded_data)

        tile_results.append(xr.merge(results).assign_coords({'tile': tile}))
    ds_merged = xr.concat(tile_results, dim='tile', coords='different')
    ds_merged = ds_merged.assign_coords({'XC': ecco_grid.XC, 'YC': ecco_grid.YC})
    ds_merged.attrs = ds_sic.attrs
    ds_merged.attrs['processing'] = 'Regridded to the ECCO model grid with bilinear interpolation using xESMF by Daniel Watkins, June 2026'
    ds_merged.attrs['final_projection'] = 'ECCO grid'

    ds_merged.to_netcdf(saveloc + 'nsidc_daily_sea_ice_concentration/nsidc_daily_sea_ice_concentration_{y}.nc'.format(y=year),
                        encoding={v: {'zlib': True} for v in variables},
                         engine='netcdf4'
    )
    print("Finished {y}".format(y=year))

print("Computing monthly means")
monthly_means = []
for year in range(1992, 2018):
    with xr.open_dataset(saveloc + 'nsidc_daily_sea_ice_concentration/nsidc_daily_sea_ice_concentration_{y}.nc'.format(y=year)) as ds:
        monthly_means.append(ds.resample({'time': '1MS'}).mean())
ds = xr.concat(monthly_means, dim='time')
ds.attrs['processing'] = ds.attrs['processing'] + '\n Computed monthly mean'
ds.to_netcdf(saveloc + 'nsidc_monthly_sea_ice_concentration_1992-2017.nc',
                encoding={v: {'zlib': True} for v in variables},
                engine='netcdf4') 