# ecco_wind_ice_coupling
Scripts and notebooks supporting Ahmed et al. 2026


# data processing workflow
All scripts are designed to begin with data at daily resolution from the original data providers, then process this data to the form used for the article.
For the observational data and PIOMAS reanalysis, this includes mapping the data to the ECCO grid using xESMF.
The user sets the location of the downloaded original files in `saveloc` in the scripts, and by default data is saved one level above the repository on the user's local computer.
This is to prevent large files from clogging up the GitHub repo.

- `regrid_nsidc_sic_to_ecco.py`: Takes the NOAA/NSIDC Climate Data Record of Sea Ice Concentration v4, compiles into yearly files, then regrids the files onto the ECCO grid. Individual years are saved in  `../../data/nsidc_daily_sea_ice_concentration` and the monthly means are computed, concatenated, then saved in `../../data/`.
- `regrid_nsidc_ice_motion_to_ecco.py`: Takes the NSIDC Ice Motion Vectors data product (v4) at daily resolution, regrids to ECCO, then saves the year long daily resolution files to `../../data/nsidc_daily_sea_ice_velocity`. Then, read these files in, mask months where less than 90% of the days of the month have data, and compute the monthly means, and concatenate all years. The result is saved to `../../data/nsidc_monthly_sea_ice_velocity_1992-2017.nc`.

## TBD
- compute drift speed ratios
- regrid PIOMAS
- compile yearly ecco sea ice concentration data (edit the monthly mean file for this)
- compile yearly ecco wind speed data
- compute complex correlation coefficients at monthly resolution, save "n". Need to drop values where the denominator is too close to zero.
- plot figure 1: comparison of sea ice extent time series, sea ice concentration, location of sea ice edge.