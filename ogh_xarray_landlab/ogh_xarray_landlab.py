# import libraries
import os
import numpy as np
import pandas as pd
import xarray as xray
import ftplib, wget, bz2, urllib
import dask as da
from dask.diagnostics import ProgressBar
from multiprocessing.pool import ThreadPool

import ogh
import landlab.grid.raster as r

import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.style.use('tableau-colorblind10')
import shapely.ops
from shapely.geometry import MultiPolygon, shape, point, box, Polygon
from mpl_toolkits.basemap import Basemap
import geopandas as gpd


def compile_x_wrfnnrp_raw_Salathe2014_locations(time_increments):
    """
    Compile a list of file URLs for Salathe et al., 2014 raw WRF NNRP data
    
    time_increments: (list) a list of dates that identify each netcdf file
    """
    locations=[]
    domain='http://cses.washington.edu'
    subdomain='/rocinante/WRF/NNRP/vic_16d/PNW_1970_1999/WRF_NNRP_noBC/netcdf_daily'

    for ind, yearmo in enumerate(time_increments):
        basename='/WRF_NNRP_noBC.{0}.nc'.format(yearmo)
        url='{0}{1}{2}'.format(domain, subdomain, basename)
        locations.append(url)
    return(locations)


def compile_x_dailymet_Livneh2013_raw_locations(time_increments):
    """
    Compile a list of file URLs for Livneh et al., 2013 raw MET data
    
    time_increments: (list) a list of dates that identify each netcdf file
    """
    locations=[]
    domain='ftp://livnehpublicstorage.colorado.edu'
    subdomain='/public/Livneh.2013.CONUS.Dataset/Meteorology.nc.v.1.2.1915.2011.bz2'

    for ind, yearmo in enumerate(time_increments):
        if yearmo.startswith('1915') or (yearmo=='191601'):
            basename='/Meteorology_Livneh_CONUSExt_v.1.2_2013.{0}.nc'.format(yearmo)
        else:
            basename='/Meteorology_Livneh_CONUSExt_v.1.2_2013.{0}.nc.bz2'.format(yearmo)
        url='{0}{1}{2}'.format(domain, subdomain, basename)
        locations.append(url)
    return(locations)


def compile_x_wrfpnnl2018_raw_locations(time_increments):
    """
    Compile a list of file URLs for PNNL 2018 raw WRF data
    time_increments: (list) a list of dates that identify each netcdf file
    """
    locations=[]
    domain='http://cses.washington.edu'
    subdomain='/rocinante/WRF/PNNL_NARR_6km'

    for ind, ymd in enumerate(time_increments):
        subfolder = '/{0}'.format(ymd[0:4])
        basename='/data.{0}-{1}-{2}.nc'.format(ymd[0:4], ymd[4:6], ymd[6:8])
        url='{0}{1}{2}{3}'.format(domain, subdomain, subfolder, basename)
        locations.append(url)
    return(locations)


def wget_x_download_spSubset(fileurl, 
                             spatialbounds, 
                             file_prefix='sp_',
                             rename_timelatlong_names={'LAT':'LAT','LON':'LON'}, 
                             replace_file=True):
    """
    Download files from an http domain
    
    fileurl: (str) a urls to request a netcdf file
    spatialbounds: (dict) dictionary providing the minx, miny, maxx, and maxy of the spatial region
    file_prefix: (str) a string to mark the output file as a spatial subset
    rename_timelatlong_names: (dict) a dictionary to standardize latitude/longitude synonyms to LAT/LON, respectively
    replace_file: (logic) If True, the existing file will be replaced; if False, the file download is skipped
    """
    
    # check if the file path already exists; if so, apply replace_file logic
    basename = os.path.basename(fileurl)
    if os.path.isfile(basename):
        os.remove(basename)
        
    if os.path.isfile(file_prefix+basename) and replace_file:
        os.remove(file_prefix+basename)
    elif os.path.isfile(file_prefix+basename) and not replace_file:
        # replace_file is False; return file path and skip
        return(os.path.join(os.getcwd(), file_prefix+basename))
        
    # try the file connection
    try:
        ping = urllib.request.urlopen(fileurl)
        
        # if the file exists, download it
        if ping.getcode() != 404:
            ping.close()
            wget.download(fileurl)

            # open the parent netcdf file
            ds = xray.open_dataset(basename, engine = 'netcdf4')
            
            # rename latlong if they are not LAT and LON, respectively
            if not isinstance(rename_timelatlong_names, type(None)):
                ds = ds.rename(rename_timelatlong_names)
                
            # slice by the bounding box
            spSubset = ds.sel(LON=slice(spatialbounds['minx'], spatialbounds['maxx']),
                              LAT=slice(spatialbounds['miny'], spatialbounds['maxy']))

            # print the spatial subset
            spSubset.to_netcdf(file_prefix+basename)
            
            # remove the parent
            ds.close()
            os.remove(basename)
            return(os.path.join(os.getcwd(), file_prefix+basename))

        else:
            ping.close()
    except:
        print('File does not exist at this URL: ' + basename)


def ftp_x_download_spSubset(fileurl,
                            spatialbounds,
                            file_prefix='sp_',
                            rename_timelatlong_names={'LAT':'LAT','LON':'LON','TIME':'TIME'},
                            replace_file=True):
    """
    Download files from an http domain
    
    fileurl: (str) a urls to request a netcdf file
    spatialbounds: (dict) dictionary providing the minx, miny, maxx, and maxy of the spatial region
    file_prefix: (str) a string to mark the output file as a spatial subset
    rename_timelatlong_names: (dict) a dictionary to standardize latitude/longitude synonyms to LAT/LON, respectively
    replace_file: (logic) If True, the existing file will be replaced; if False, the file download is skipped
    """
    # establish path info
    fileurl=fileurl.replace('ftp://', '') # loci is already the url with the domain already appended
    ipaddress=fileurl.split('/', 1)[0] # ip address
    path=os.path.dirname(fileurl.split('/', 1)[1]) # folder path
    filename = os.path.basename(fileurl)
    
    # check if the file path already exists; if so, apply replace_file logic
    if os.path.isfile(filename):
        os.remove(filename)
        
    if os.path.isfile(file_prefix+filename) and replace_file:
        os.remove(file_prefix+filename)
    elif os.path.isfile(file_prefix+filename) and not replace_file:
        # replace_file is False; return file path and skip
        return(os.path.join(os.getcwd(), file_prefix+filename))
        
    # download the file from the ftp server
    ftp=ftplib.FTP(ipaddress)
    ftp.login()
    ftp.cwd(path)
    try:
        # try the file connection
        ftp.retrbinary('RETR ' + filename , open(filename, 'wb').write)
        ftp.close()
        
        # decompress the file
        if filename.endswith('.bz2'):
            ogh.decompbz2(filename)
            filename = filename.replace('.bz2','')
            
        # open the parent netcdf file
        ds = xray.open_dataset(filename, engine = 'netcdf4')
        
        if not isinstance(rename_timelatlong_names, type(None)):
            ds = ds.rename(rename_timelatlong_names)

        # slice by the bounding box
        spSubset = ds.sel(LON=slice(spatialbounds['minx'], spatialbounds['maxx']),
                          LAT=slice(spatialbounds['miny'], spatialbounds['maxy']))

        # print the spatial subset
        spSubset.to_netcdf(file_prefix+filename)

        # remove the parent
        ds.close()
        os.remove(filename)
        return(os.path.join(os.getcwd(), file_prefix+filename))
    except:
        #os.remove(filename)
        print('File does not exist at this URL: '+fileurl)
        
        
def get_x_dailywrf_Salathe2014(homedir,
                               spatialbounds,
                               subdir='salathe2014/Daily_WRF_1970_1999/noBC',
                               nworkers=4,
                               start_date='1970-01-01',
                               end_date='1989-12-31',
                               rename_timelatlong_names={'LAT':'LAT','LON':'LON','TIME':'TIME'},
                               file_prefix='sp_',
                               replace_file=True):
    """
    get Daily WRF data from Salathe et al. (2014) using xarray on netcdf files
    """
    # check and generate DailyMET livneh 2013 data directory
    filedir=os.path.join(homedir, subdir)
    ogh.ensure_dir(filedir)
    
    # modify each month between start_date and end_date to year-month
    dates = [x.strftime('%Y%m') for x in pd.date_range(start=start_date, end=end_date, freq='M')]

    # initialize parallel workers
    da.set_options(pool=ThreadPool(nworkers))
    ProgressBar().register()
    
    # generate the list of files to download
    filelist = compile_x_wrfnnrp_raw_Salathe2014_locations(dates)

    # download files of interest
    NetCDFs=[]
    for url in filelist:
        NetCDFs.append(da.delayed(wget_x_download_spSubset)(fileurl=url,
                                                            spatialbounds=spatialbounds,
                                                            file_prefix=file_prefix,
                                                            rename_timelatlong_names=rename_timelatlong_names,
                                                            replace_file=replace_file))

    # run operations
    outputfiles = da.compute(NetCDFs)[0]

    # reset working directory
    os.chdir(homedir)
    return(outputfiles)


def get_x_hourlywrf_PNNL2018(homedir,
                             spatialbounds,
                             subdir='PNNL2018/Hourly_WRF_1981_2015/noBC',
                             nworkers=4,
                             start_date='1981-01-01',
                             end_date='2015-12-31',
                             rename_timelatlong_names={'LAT':'LAT','LON':'LON','TIME':'TIME'},
                             file_prefix='sp_',
                             replace_file=True):
    """
    get hourly WRF data from a 2018 PNNL WRF run using xarray on netcdf files
    """
    # check and generate data directory
    filedir=os.path.join(homedir, subdir)
    ogh.ensure_dir(filedir)
    
    # modify each month between start_date and end_date to year-month
    dates = [x.strftime('%Y%m%d') for x in pd.date_range(start=start_date, end=end_date, freq='D')]
    
    # initialize parallel workers
    da.set_options(pool=ThreadPool(nworkers))
    ProgressBar().register()
    
    # generate the list of files to download
    filelist = compile_x_wrfpnnl2018_raw_locations(dates)
    
    # download files of interest
    NetCDFs=[]
    for url in filelist:
        NetCDFs.append(da.delayed(wget_x_download_spSubset)(fileurl=url,
                                                            spatialbounds=spatialbounds,
                                                            file_prefix=file_prefix,
                                                            rename_latlong_names=rename_timelatlong_names,
                                                            replace_file=replace_file))
    
    # run operations
    outputfiles = da.compute(NetCDFs)[0]
    
    # reset working directory
    os.chdir(homedir)
    return(outputfiles)


def get_x_dailymet_Livneh2013_raw(homedir,
                                  spatialbounds,
                                  subdir='livneh2013/Daily_MET_1915_2011/raw_netcdf',
                                  nworkers=4,
                                  start_date='1915-01-01',
                                  end_date='2011-12-31',
                                  rename_timelatlong_names={'lat':'LAT','lon':'LON','time':'TIME'},
                                  file_prefix='sp_',
                                  replace_file=True):
    """
    get Daily MET data from Livneh et al. (2013) using xarray on netcdf files
    """
    # check and generate DailyMET livneh 2013 data directory
    filedir=os.path.join(homedir, subdir)
    ogh.ensure_dir(filedir)
    
    # modify each month between start_date and end_date to year-month
    dates = [x.strftime('%Y%m') for x in pd.date_range(start=start_date, end=end_date, freq='M')]

    # initialize parallel workers
    da.set_options(pool=ThreadPool(nworkers))
    ProgressBar().register()
    
    # generate the list of files to download
    filelist = compile_x_dailymet_Livneh2013_raw_locations(dates)

    # download files of interest
    NetCDFs=[]
    for url in filelist:
        NetCDFs.append(da.delayed(ftp_x_download_spSubset)(fileurl=url,
                                                           spatialbounds=spatialbounds,
                                                           file_prefix=file_prefix,
                                                           rename_timelatlong_names=rename_timelatlong_names,
                                                           replace_file=replace_file))

    # run operations
    outputfiles = da.compute(NetCDFs)[0]

    # reset working directory
    os.chdir(homedir)
    return(outputfiles)


def netcdf_to_ascii(homedir, subdir, source_directory, mappingfile, catalog_label, meta_file, 
                    temporal_resolution='D', netcdfs=None, variable_list=None):
    # initialize list of dataframe outputs
    outfiledict = {}
    
    # generate destination folder
    filedir=os.path.join(homedir, subdir)
    ogh.ensure_dir(filedir)

    # connect with collection of netcdfs
    if isinstance(netcdfs, type(None)):
        netcdfs=[os.path.join(source_directory,file) for file in os.listdir(source_directory) if file.endswith('.nc')]
    ds_mf = xray.open_mfdataset(netcdfs, engine = 'netcdf4').sortby('TIME')

    # generate list of variables
    if not isinstance(variable_list, type(None)):
        ds_vars = variable_list.copy()
    else:
        ds_vars = [ds_var for ds_var in dict(ds_mf.variables).keys() 
                   if ds_var not in ['YEAR','MONTH','DAY','TIME','LAT','LON']]

    # convert netcdfs to pandas.Panel API
    ds_pan = ds_mf.to_dataframe()[ds_vars]

    # read in gridded cells of interest
    maptable, nstation = ogh.mappingfileToDF(mappingfile, colvar=None, summary=False)

    # at each latlong of interest
    for ind, eachrow in maptable.iterrows():

        # generate ASCII time-series
        ds_df = ds_pan.loc[eachrow['LAT'],eachrow['LONG_'],:].reset_index(drop=True, level=[0,1])

        # create file name
        outfilename = os.path.join(filedir,'data_{0}_{1}'.format(eachrow['LAT'],eachrow['LONG_']))

        # save ds_df
        outfiledict[outfilename] = da.delayed(ds_df.to_csv)(path_or_buf=outfilename, sep='\t', header=False, index=False)
    
    # compute ASCII time-series files
    ProgressBar().register()
    outfiledict = da.compute(outfiledict)[0]
    
    # annotate metadata file
    meta_file[catalog_label] = dict(ds_mf.attrs)
    meta_file[catalog_label]['variable_list']=list(np.array(ds_vars))
    meta_file[catalog_label]['delimiter']='\t'
    meta_file[catalog_label]['start_date']=pd.Series(ds_mf.TIME).sort_values().iloc[0].strftime('%Y-%m-%d %H:%M:%S')
    meta_file[catalog_label]['end_date']=pd.Series(ds_mf.TIME).sort_values().iloc[-1].strftime('%Y-%m-%d %H:%M:%S')
    meta_file[catalog_label]['temporal_resolution']=temporal_resolution
    meta_file[catalog_label]['variable_info'] = dict(ds_mf.variables)
    
    # catalog the output files
    ogh.addCatalogToMap(outfilepath=mappingfile, maptable=maptable, folderpath=filedir, catalog_label=catalog_label)
    os.chdir(homedir)
    return(list(outfiledict.keys()))


def calculateUTMbounds(mappingfile, mappingfile_crs={'init':'epsg:4326'}, spatial_resolution=0.06250):
    # read in the mappingfile
    map_df, nstation = ogh.mappingfileToDF(mappingfile)

    # loop though each LAT/LONG_ +/-0.06250 centroid into gridded cells
    geom=[]
    midpt = spatial_resolution/2
    for ind in map_df.index:
        mid = map_df.loc[ind]
        geom.append(box(mid.LONG_- midpt, mid.LAT - midpt, mid.LONG_ + midpt, mid.LAT + midpt, ccw=True))

    # generate the GeoDataFrame
    test = gpd.GeoDataFrame(map_df, crs=mappingfile_crs, geometry=geom)

    # compile gridded cells to extract bounding box
    test['shapeName'] = 1

    # dissolve shape into new shapefile
    newShape = test.dissolve(by='shapeName').reset_index()
    newShape.bounds

    # take the minx and miny, and centroid_x and centroid_y
    minx, miny, maxx, maxy = newShape.bounds.loc[0]
    lon0, lat0 = np.array(newShape.centroid[0])

    # generate the basemap raster
    fig = plt.figure(figsize=(10,10), dpi=500)
    ax1 = plt.subplot2grid((1,1),(0,0))
    m = Basemap(projection='tmerc', resolution='h', ax=ax1, lat_0=lat0, lon_0=lon0,
                llcrnrlon=minx, llcrnrlat=miny, urcrnrlon=maxx, urcrnrlat=maxy)

    # transform each polygon to the utm basemap projection
    for ind in newShape.index:
        eachpol = newShape.loc[ind]
        newShape.loc[ind,'g2'] = shapely.ops.transform(m, eachpol['geometry'])

    # transform each polygon to the utm basemap projection
    newShape['g2'] = newShape.apply(lambda x: shapely.ops.transform(m, x['geometry']), axis=1)
    
    # remove the plot
    plt.gcf().clear()

    # establish the UTM basemap bounding box dimensions
    minx2, miny2, maxx2, maxy2 = newShape['g2'].iloc[0].bounds
    return(minx2, miny2, maxx2, maxy2)


def calculateUTMcells(mappingfile, mappingfile_crs={'init':'epsg:4326'}, spatial_resolution=0.06250):
    # read in the mappingfile
    map_df, nstation = ogh.mappingfileToDF(mappingfile)

    # loop though each LAT/LONG_ +/-0.06250 centroid into gridded cells
    geom=[]
    midpt = spatial_resolution/2
    for ind in map_df.index:
        mid = map_df.loc[ind]
        geom.append(box(mid.LONG_- midpt, mid.LAT - midpt, mid.LONG_ + midpt, mid.LAT + midpt, ccw=True))

    # generate the GeoDataFrame
    test = gpd.GeoDataFrame(map_df, crs=mappingfile_crs, geometry=geom)

    # compile gridded cells to extract bounding box
    test['shapeName'] = 1

    # dissolve shape into new shapefile
    newShape = test.dissolve(by='shapeName').reset_index()

    # take the minx and miny, and centroid_x and centroid_y
    minx, miny, maxx, maxy = newShape.bounds.loc[0]
    lon0, lat0 = np.array(newShape.centroid[0])

    # generate the basemap raster
    fig = plt.figure(figsize=(10,10), dpi=500)
    ax1 = plt.subplot2grid((1,1),(0,0))
    m = Basemap(projection='tmerc', resolution='h', ax=ax1, lat_0=lat0, lon_0=lon0,
                llcrnrlon=minx, llcrnrlat=miny, urcrnrlon=maxx, urcrnrlat=maxy)

    # transform each polygon to the utm basemap projection
    test['geometry'] = test.apply(lambda x: shapely.ops.transform(m, x['geometry']), axis=1)
    test = test.drop('shapeName', axis=1)
    
    # remove the plot
    plt.gcf().clear()

    # return the geodataframe and the spatial transformation from WGS84
    return(test, m)


def rasterDimensions (maxx, maxy, minx=0, miny=0, dy=100, dx=100):
    # construct the range
    x = pd.Series(range(int(minx),int(maxx)+1,1))
    y = pd.Series(range(int(miny),int(maxy)+1,1))
    
    # filter for values that meet the increment or is the last value
    cols = pd.Series(x.index).apply(lambda x1: x[x1] if x1 % dx == 0 or x1==x[0] or x1==x.index[-1] else None)
    rows = pd.Series(y.index).apply(lambda y1: y[y1] if y1 % dy == 0 or y1==y[0] or y1==y.index[-1] else None)
    
    # construct the indices
    row_list = np.array(rows.loc[pd.notnull(rows)])
    col_list = np.array(cols.loc[pd.notnull(cols)])
    
    # construct the raster
    raster = r.RasterModelGrid((len(row_list), len(col_list)), spacing=(dy, dx))
    raster.add_zeros
    return(raster, row_list, col_list)


def mappingfileToRaster(mappingfile, maxx, maxy, minx=0, miny=0, dx=100, dy=100, 
                        spatial_resolution=0.06250, mappingfile_crs={'init':'epsg:4326'}, raster_crs={'init':'epsg:3857'}):
    
    # generate the mappingfile with UTM cells
    UTMmappingfile, m = calculateUTMcells(mappingfile=mappingfile,
                                          mappingfile_crs=mappingfile_crs,
                                          spatial_resolution=spatial_resolution)
    
    # construct the raster
    raster, row_list, col_list = rasterDimensions(maxx, maxy, minx=minx, miny=miny, dy=dy, dx=dx)
    
    # initialize node list
    df_list=[]
    
    # loop through the raster nodes (bottom to top arrays)
    for row_index, nodelist in enumerate(raster.nodes):

        # index bottom to top arrays with ordered Latitude
        lat = row_list[row_index]

        # index left to right with ordered Longitude
        for nodeid, long_ in zip(nodelist, col_list):
            df_list.append([nodeid, 
                            box(long_, lat, long_+dx, lat+dy, ccw=True),
                            box(long_, lat, long_+dx, lat+dy, ccw=True).centroid])
            
    # convert to dataframe
    df = pd.DataFrame.from_records(df_list).rename(columns={0:'nodeid',1:'raster_geom', 2:'raster_centroid'})
    raster_map = gpd.GeoDataFrame(df, geometry='raster_centroid', crs=raster_crs)

    # identify raster nodeid and equivalent mappingfile FID
    raster_df = gpd.sjoin(raster_map, UTMmappingfile, how='left', op='intersects')
    raster_df = raster_df.drop('raster_centroid', axis=1).set_geometry('raster_geom')
    
    # return the raster node to mappingfile FID cross-map, and the rastermodelgrid
    return(raster_df, raster, m)


def temporalSlice(vardf, vardf_dateindex):
    values = vardf.loc[vardf_dateindex, :].reset_index(level=0)
    values = values.rename(columns={'level_0': 'FID', vardf_dateindex: 'value'}).reset_index(drop=True)
    return(values)


def rasterVector(vardf, vardf_dateindex, crossmap, nodata=-9999):
    values = temporalSlice(vardf=vardf, vardf_dateindex=vardf_dateindex)
    vector = crossmap.merge(values, on='FID', how='left').fillna(nodata)['value']
    return(vector)

    
def valueRange(listOfDf):
    all_values = pd.concat(listOfDf, axis=1).as_matrix()
    return(all_values)


def rasterVectorToWGS(value_vector, nodeXmap, UTM_transformer):
    # name the vector column
    t1 = value_vector.reset_index().rename(columns={'index':'nodeid'})

    # reduce the nodeXmap
    t2 = nodeXmap[pd.notnull(nodeXmap.FID)]

    # merge the node vector information with the crossmap
    t3 = pd.merge(t1, t2, how='right', on='nodeid')

    # transform raster_geom into WGS84
    ids=[]
    newpol = []

    for ind, eachpoly in t3.iterrows():
        # reverse polygon centroid mapping to WGS84
        ras_x, ras_y = np.array(eachpoly['raster_geom'].centroid)
        newcent = UTM_transformer(ras_x, ras_y, inverse=True)

        # indexed by nodeid, LAT, LON
        ids.append(tuple([eachpoly['nodeid'],newcent[1], newcent[0]]))

        # reverse polygon mapping to WGS84
        newpol.append(Polygon([UTM_transformer(x, y, inverse=True) 
                               for x, y in eachpoly['raster_geom'].__geo_interface__['coordinates'][0]]))

    # index each raster node by nodeid, LAT, LON
    t4 = t3.set_index(pd.MultiIndex.from_tuples(ids, names=['','','']))
    t4['wgs_raster'] = newpol
    t4 = t4.set_geometry('wgs_raster')

    # assimilate t5 as wide table
    t5 = t4[['value']].T.reset_index(drop=True)
    return(t4, t5)
