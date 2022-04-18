## GPSmyCity to GPX converter
# Last update: 2022-04-12


# Erase all declared global variables
globals().clear()

# Import packages
import os
import re
from urllib.request import urlopen

import gpxpy
import numpy as np
import pandas as pd
from werkzeug.utils import secure_filename

# Set working directory to user's 'Downloads' folder
os.chdir(os.path.join(os.path.expanduser('~'), r'Downloads'))



###########
# Functions
###########

def gpsmycity_importer(url):

    page_source = urlopen(url).read().decode('utf-8')
    page_source = page_source.split('\n')

    # tour_name
    tour_name = [s for s in page_source if s.startswith('<TITLE>') and s.endswith('</TITLE>\r')][0]
    tour_name = re.sub(r'^<TITLE>', r'', tour_name)
    tour_name = re.sub(r'</TITLE>\r$', r'', tour_name)

    # tour_map
    tour_map = [s for s in page_source if s.startswith('jarr')][0]
    tour_map = re.sub(r'^jarr = ', r'', tour_map)
    tour_map = re.sub(r';\r$', r'', tour_map)

    # Create a dataframe from tour_map
    df_tour_map = pd.read_json(tour_map, dtype='unicode', convert_dates=False, orient ='index')
    df_tour_map = df_tour_map.transpose()
    df_tour_map['pins'] = df_tour_map['pins'].replace(r'^None$', np.NaN, regex=True)

    # Split df_tour_map in df_segments and df_waypoints dataframes
    df_segments = df_tour_map.filter(['path'])
    df_waypoints = df_tour_map[~df_tour_map['pins'].isnull()].filter(['pins'])

    # Delete objects
    del page_source, tour_map, df_tour_map


    ## df_segments

    # Split columns
    df_segments['path'] = df_segments['path'].str.strip('[\']')
    df_segments[['latitude', 'longitude']] = df_segments['path'].str.split('\', \'', expand=True)
    df_segments = df_segments.drop(columns=['path'])

    # Change dtypes
    df_segments['latitude'] = pd.to_numeric(df_segments['latitude'])
    df_segments['longitude'] = pd.to_numeric(df_segments['longitude'])


    ## df_waypoints

    # Split columns
    df_waypoints['pins'] = df_waypoints['pins'].str.strip('[\']')
    df_waypoints[['latitude', 'longitude', 'name', 'number', 'id']] = df_waypoints['pins'].str.split('\', "|\', \'|", \'', expand=True)
    df_waypoints = df_waypoints.drop(columns=['pins', 'number', 'id'])

    # Change dtypes
    df_waypoints['latitude'] = pd.to_numeric(df_waypoints['latitude'])
    df_waypoints['longitude'] = pd.to_numeric(df_waypoints['longitude'])


    ## Create .gpx file
    gpx = gpxpy.gpx.GPX()
    gpx.creator = 'GPSmyCity'
    gpx.description = tour_name

    # Create first track in .gpx
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in .gpx track
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Write segments to .gpx
    for row in df_segments.index:
       gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=df_segments.loc[row, 'latitude'], longitude=df_segments.loc[row, 'longitude']))

    # Write waypoints to .gpx
    for row in df_waypoints.index:
       gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(name=df_waypoints.loc[row, 'name'], latitude=df_waypoints.loc[row, 'latitude'], longitude=df_waypoints.loc[row, 'longitude']))

    # Save .gpx file
    with open('{}.gpx'.format(secure_filename(tour_name)), 'w') as f:
        f.write(gpx.to_xml())



####################
# gpsmycity_importer
####################

# List of tours to be imported
url_list = ['https://www.gpsmycity.com/tours/munich-introduction-walking-tour-6446.html',
'https://www.gpsmycity.com/tours/edinburgh-introduction-walking-tour-6397.html']

for index in url_list:
    gpsmycity_importer(index)
