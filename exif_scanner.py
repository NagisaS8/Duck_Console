import exifread

class Scanner:
    def __init__(self) -> None:
        self.path = ""
        self.data = {}
        self.loc_url = ""

    def set_path(self, path):
        self.path = path

    def scan(self):
        data = None
        with open(self.path, "rb") as file:
            data = exifread.process_file(file)
        self.data = data

    def get_result(self):
        return self.data

    def _convert_to_degrees(self, value):
        """Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format."""
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)

        return d + (m / 60.0) + (s / 3600.0)

    def try_get_location(self):
        # Check if the necessary GPS tags are present
        if 'GPS GPSLatitudeRef' in self.data and 'GPS GPSLatitude' in self.data and \
           'GPS GPSLongitudeRef' in self.data and 'GPS GPSLongitude' in self.data:

            # Get latitude and longitude values
            lat_ref = self.data['GPS GPSLatitudeRef'].values
            lat = self._convert_to_degrees(self.data['GPS GPSLatitude'])
            lon_ref = self.data['GPS GPSLongitudeRef'].values
            lon = self._convert_to_degrees(self.data['GPS GPSLongitude'])

            # Adjust sign based on N/S and E/W
            if lat_ref != 'N':
                lat = -lat
            if lon_ref != 'E':
                lon = -lon

            # Generate Google Maps URL
            self.loc_url = f"https://maps.google.com/?q={lat},{lon}"
            return True

        return False
