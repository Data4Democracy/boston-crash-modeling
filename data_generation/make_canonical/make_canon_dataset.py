
# coding: utf-8
# Generate canonical dataset for hackathon
# Developed by: bpben
import json
import pandas as pd
from ..util import read_shp


MAP_FP = 'data/processed/maps'
DATA_FP = 'data/processed'


def read_records(fp, date_col, id_col, agg='week'):
    """ Read point data, output count by aggregation level
    agg : datepart for aggregation
    date_col : column name with date information
    id_col : column name with inter/non-inter id (for grouping)
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
    return(df_g)


def road_make(feats, inters_fp, non_inters_fp, agg='max'):
    """ Makes road feature df, intersections + non-intersections

    agg : aggregation type (default is max)
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
    
    # Aggregating inters data = apply aggregation (default is max)
    aggregated = getattr(combined[feats].groupby(combined.index), agg)

    # return aggregation and adjacency info (orig_id)
    return(aggregated(), combined['orig_id'])

if __name__ == '__main__':

    # read/aggregate crash/concerns
    crash = read_records(DATA_FP + '/crash_joined.json',
                         'CALENDAR_DATE', 'near_id')
    concern = read_records(DATA_FP + '/concern_joined.json',
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
    inters_fp = DATA_FP + '/inters_data.json'
    non_inters_fp = MAP_FP + '/non_inters_segments.shp'

    feats = ['AADT', 'SPEEDLIMIT',
             'Struct_Cnd', 'Surface_Tp',
             'F_F_Class']

    # create combined road feature dataset
    aggregated, adjacent = road_make(feats, inters_fp, non_inters_fp)
    print "road features being included: ", ', '.join(feats)
    # All features as int
    aggregated = aggregated.apply(lambda x: x.astype('int'))

    # 53 weeks for each segment (year = 52.2 weeks)
    all_weeks = pd.MultiIndex.from_product(
        [aggregated.index, range(1, 54)], names=['segment_id', 'week'])

    # crash/concern for each week, for each segment
    cr_con = cr_con.set_index(
        ['near_id', 'week']).reindex(all_weeks, fill_value=0)
    cr_con.reset_index(inplace=True)

    # join segment features to crash/concern
    cr_con_roads = cr_con.merge(
        aggregated, left_on='segment_id', right_index=True, how='outer')

    # output canon dataset
    print "exporting canonical dataset to ", DATA_FP
    cr_con_roads.set_index('segment_id').to_csv(
        DATA_FP + '/vz_predict_dataset.csv.gz', compression='gzip')

    # output adjacency info
    # need to include ATRs
    atrs = pd.read_json(DATA_FP + '/snapped_atrs.json')
    adjacent = adjacent.reset_index()
    adjacent = adjacent.merge(
        atrs[['near_id', 'orig']],
        left_on='index',
        right_on='near_id',
        how='left'
    )
    adjacent.drop(['near_id'], axis=1, inplace=True)
    adjacent.columns = ['segment_id', 'orig_id', 'atr_address']
    adjacent.to_csv(DATA_FP+'/adjacency_info.csv', index=False)
