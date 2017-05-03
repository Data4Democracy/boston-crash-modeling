
# coding: utf-8
# Generate canonical dataset for hackathon
# Developed by: bpben
import fiona
import json
import pandas as pd
import os.path
from shapely.geometry import Point, MultiPoint, shape, mapping
from util import read_shp


def read_records(fp, date_col, id_col, agg='week'):
    """ Reads point data, output count by aggregation level
    
    Args: 
        fp (str): Filename to read
        agg (str): datepart for aggregation, e.g. 'week'
        date_col (str): column name with date information
        id_col (str): column name with inter/non-inter id (for grouping)
        
    Returns:
        A pandas GroupBy object
    """

    with open(fp, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df[date_col] = pd.to_datetime(df[date_col])
    print "total number of records in {}:{}".format(fp, len(df))

    # aggregate
    print "aggregating by ", agg
    df[agg] = df[date_col].apply(lambda x: getattr(x, agg))
    df_g = df.groupby([id_col, agg]).size()
    return df_g


def road_make(feats, inters_fp, non_inters_fp, agg='max'):
    """ Makes road feature df, intersections + non-intersections 

    Args:
        feats : 
        inters_fp (str): Filename of intersection segments (GeoJSON)
        non_inters_fp (str): Filename of non-intersection segments (GeoJSON)
        agg : aggregation type (default is max)
        
    Returns:
        
    """
    # Read in inters data (json), turn into df with inter index
    df_index = []
    df_records = []
    print "reading ", inters_fp
    with open(inters_fp, 'r') as f:
        inters = json.load(f)
        # Append each index to dataframe
        for idx, lines in inters.iteritems():
            df_records.extend(lines)
            df_index.extend([idx] * len(lines))
    inters_df = pd.DataFrame(df_records, index=df_index)

    # Read in non_inters data:
    print "reading ", non_inters_fp
    non_inters = read_shp(non_inters_fp)
    non_inters_df = pd.DataFrame([x[1] for x in non_inters])
    non_inters_df.set_index('id', inplace=True)

    # Combine inter + non_inter
    combined = pd.concat([inters_df, non_inters_df])

    # Subset columns
    combined = combined[feats]

    # Aggregating inters data = max of all properties
    aggregated = getattr(combined.groupby(combined.index), agg)
    combined = aggregated()

    return combined


def main():
    """ Creates canonical dataset
    
    Dependencies:
        interim/crash_joined.json
        interim/concern_joined.json
        interim/inters_data.json
        interim/non_inters_segments.shp
        
    Outputs:
        processed/vz_predict_dataset.csv.gz
    """
    INTERIM_FP = os.path.normpath('./data/interim')
    PROCESSED_FP = os.path.normpath('./data/processed')

    crash = read_records(os.path.join(INTERIM_FP, 'crash_joined.json'),
                         'CALENDAR_DATE', 'near_id')
    concern = read_records(os.path.join(INTERIM_FP, 'concern_joined.json'),
                           'REQUESTDATE', 'near_id')

    # join aggregated crash/concerns
    cr_con = pd.concat([crash, concern], axis=1)
    cr_con.columns = ['crash', 'concern']

    # if null for a certain week = 0 (no crash/concern)
    cr_con.reset_index(inplace=True)
    cr_con = cr_con.fillna(0)
    # Make near_id string (for matching to segments)
    cr_con['near_id'] = cr_con['near_id'].astype('str')

    # combined road feature dataset parameters
    inters_fp = os.path.join(INTERIM_FP, 'inters_data.json')
    non_inters_fp = os.path.join(INTERIM_FP, 'non_inters_segments.shp')
    feats = ['AADT', 'SPEEDLIMIT',
             'Struct_Cnd', 'Surface_Tp',
             'F_F_Class']

    # create combined road feature dataset
    combined = road_make(feats, inters_fp, non_inters_fp)
    print "road features being included: ", ', '.join(feats)
    # All features as int
    combined = combined.apply(lambda x: x.astype('int'))

    # 53 weeks for each segment (year = 52.2 weeks)
    all_weeks = pd.MultiIndex.from_product(
        [combined.index, range(1, 54)], names=['segment_id', 'week'])

    # crash/concern for each week, for each segment
    cr_con = cr_con.set_index(['near_id', 'week']).reindex(all_weeks, fill_value=0)
    cr_con.reset_index(inplace=True)

    # join segment features to crash/concern
    cr_con_roads = cr_con.merge(
        combined, left_on='segment_id', right_index=True, how='outer')

    # output canon dataset
    print "exporting canonical dataset to ", PROCESSED_FP
    cr_con_roads.set_index('segment_id').to_csv(
        os.path.join(PROCESSED_FP, 'vz_predict_dataset.csv.gz'), compression='gzip')


if __name__ == '__main__':
    # load_dotenv(find_dotenv())
    main()
