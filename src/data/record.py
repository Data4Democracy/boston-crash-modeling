import util
import pyproj
from shapely.geometry import Point
from dateutil.parser import parse


class Record(object):
    "A record contains a dict of properties and a point in 4326 projection"

    def __init__(self, properties):
        self.point = self._get_reproject_point(properties['location'])
        self.properties = properties

    @property
    def schema(self):
        return util.make_schema('Point', self.properties)

    def _get_near_id(self):
        if 'near_id' in self.properties:
            return self.properties['near_id']
        return None

    def _set_near_id(self, near_id):
        self.properties['near_id'] = near_id
    
    near_id = property(_get_near_id, _set_near_id)

    def _get_reproject_point(self, location):
        """
        Turn a 4326 projection into 3857
        """
        lon, lat = pyproj.transform(
            pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:3857'),
            location['longitude'], location['latitude']
        )
        return Point(float(lon), float(lat))


class Crash(Record):
    def __init__(self, properties):
        Record.__init__(self, properties)

        # Leaving this out pending standarizing schema
        # to always include summary
        self.properties['summary'] = ''
        # Need to deal with other optional fields as well
        self.properties['vehicles'] = ''
        self.properties['address'] = ''

    @property
    def timestamp(self):
        return parse(self.properties['dateOccurred'])


class Concern(Record):
    def __init__(self, properties):
        Record.__init__(self, properties)

        # Leaving these out pending ascii encoding on transformation side
        self.properties['category'] = ''
        self.properties['summary'] = ''

    @property
    def timestamp(self):
        return parse(self.properties['dateCreated'])

