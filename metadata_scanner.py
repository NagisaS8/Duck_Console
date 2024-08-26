import exifread
import config
import mutagen
import moviepy.editor as mp
import datetime
import os

class ImageScanner:
    def __init__(self) -> None:
        """Initialize instance variables for image path, EXIF data, and location URL."""
        self.path = ""
        self.data = {}
        self.loc_url = ""

    def set_path(self, path: str) -> None:
        """Sets the path of the image file to be scanned."""
        self.path = path

    def scan(self) -> None:
        """Reads the EXIF data from the specified image file."""
        with open(self.path, "rb") as file:
            self.data = exifread.process_file(file)

    def get_result(self) -> dict:
        """Returns the scanned EXIF data."""
        return self.data

    def _convert_to_degrees(self, value) -> float:
        """Converts GPS coordinates from the EXIF format to decimal degrees."""
        d = float(value.values[0].num) / float(value.values[0].den)  # Degrees
        m = float(value.values[1].num) / float(value.values[1].den)  # Minutes
        s = float(value.values[2].num) / float(value.values[2].den)  # Seconds
        return d + (m / 60.0) + (s / 3600.0)

    def try_get_location(self) -> bool:
        """Attempts to extract GPS location data from the scanned EXIF information."""
        if ('GPS GPSLatitudeRef' in self.data and 
            'GPS GPSLatitude' in self.data and
            'GPS GPSLongitudeRef' in self.data and 
            'GPS GPSLongitude' in self.data):

            lat_ref = self.data['GPS GPSLatitudeRef'].values
            lat = self._convert_to_degrees(self.data['GPS GPSLatitude'])
            lon_ref = self.data['GPS GPSLongitudeRef'].values
            lon = self._convert_to_degrees(self.data['GPS GPSLongitude'])

            # Adjust latitude and longitude based on the reference
            if lat_ref != 'N':
                lat = -lat
            if lon_ref != 'E':
                lon = -lon

            self.loc_url = config.GOOGLEMAPS_TEMPLATE_URL + f"{lat},{lon}"
            return True

        return False

    def format_data(self) -> dict:
        """Formats the EXIF data into a more understandable dictionary with specified keys."""
        formatted_data = {}
        if 'Image Make' in self.data:
            formatted_data['Camera Make'] = self.data['Image Make'].values  # Camera manufacturer
        if 'Image Model' in self.data:
            formatted_data['Camera Model'] = self.data['Image Model'].values  # Camera model
        if 'EXIF DateTimeOriginal' in self.data:
            formatted_data['Date Taken'] = self.data['EXIF DateTimeOriginal'].values  # Date photo was taken
        if 'EXIF ExposureTime' in self.data:
            formatted_data['Exposure Time'] = str(self.data['EXIF ExposureTime'].values)  # Exposure duration
        if 'EXIF FNumber' in self.data:
            formatted_data['Aperture'] = f"f/{float(self.data['EXIF FNumber'].values[0].num) / float(self.data['EXIF FNumber'].values[0].den)}"  # Aperture
        if 'EXIF ISOSpeedRatings' in self.data:
            formatted_data['ISO Speed'] = self.data['EXIF ISOSpeedRatings'].values  # ISO sensitivity
        if 'GPS GPSLatitude' in self.data:
            formatted_data['GPS Latitude'] = self._convert_to_degrees(self.data['GPS GPSLatitude'])  # Latitude
        if 'GPS GPSLongitude' in self.data:
            formatted_data['GPS Longitude'] = self._convert_to_degrees(self.data['GPS GPSLongitude'])  # Longitude
        if 'GPS GPSLatitudeRef' in self.data:
            formatted_data['Latitude Reference'] = self.data['GPS GPSLatitudeRef'].values  # N or S
        if 'GPS GPSLongitudeRef' in self.data:
            formatted_data['Longitude Reference'] = self.data['GPS GPSLongitudeRef'].values  # E or W
        return formatted_data


class VideoScanner:
    def __init__(self) -> None:
        """Initialize instance variables for video path and metadata."""
        self.path = ""
        self.metadata = {}

    def set_path(self, path: str) -> None:
        """Sets the path of the video file to be scanned."""
        self.path = path

    def scan(self) -> None:
        """Reads the metadata from the specified video file."""
        video = mp.VideoFileClip(self.path)
        self.metadata = {
            'Duration (seconds)': video.duration,  # Total duration of the video in seconds
            'Width': video.w,  # Width of the video
            'Height': video.h,  # Height of the video
            'FPS': video.fps,  # Frames per second
        }

    def get_result(self) -> dict:
        """Returns the scanned metadata for the video."""
        return self.metadata

    def format_data(self) -> dict:
        """Formats the video metadata into a more understandable dictionary."""
        formatted_data = {
            'Duration': f"{self.metadata['Duration (seconds)']} seconds",  # Duration in seconds
            'Resolution': f"{self.metadata['Width']} x {self.metadata['Height']}",  # Video resolution
            'Frames Per Second': self.metadata['FPS'],  # FPS
        }
        return formatted_data


class AudioScanner:
    def __init__(self) -> None:
        """Initialize instance variables for audio path and metadata."""
        self.path = ""
        self.metadata = {}

    def set_path(self, path: str) -> None:
        """Sets the path of the audio file to be scanned."""
        self.path = path

    def scan(self) -> None:
        """Reads the metadata from the specified audio file."""
        audio = mutagen.File(self.path)  # Read audio file
        self.metadata = {
            'Duration (seconds)': audio.info.length,  # Duration of the audio in seconds
            'Bitrate': audio.info.bitrate,  # Bitrate of the audio
            'Sample Rate': audio.info.sample_rate,  # Sample rate of the audio
            'Channels': audio.info.channels,  # Number of audio channels
        }

    def get_result(self) -> dict:
        """Returns the scanned metadata for the audio."""
        return self.metadata

    def format_data(self) -> dict:
        """Formats the audio metadata into a more understandable dictionary."""
        formatted_data = {
            'Duration': f"{self.metadata['Duration (seconds)']} seconds",  # Duration in seconds
            'Bitrate': f"{self.metadata['Bitrate'] / 1000} kbps",  # Bitrate in kbps
            'Sample Rate': f"{self.metadata['Sample Rate']} Hz",  # Sample rate in Hz
            'Channels': self.metadata['Channels'],  # Number of channels
        }
        return formatted_data

class OtherScanner:
    def __init__(self) -> None:
        """Initialize instance variables for file path and metadata."""
        self.path = ""
        self.metadata = {}

    def set_path(self, path: str) -> None:
        """Sets the path of the file to be scanned."""
        self.path = path

    def scan(self) -> None:
        """Reads the metadata from the specified file."""
        if not os.path.isfile(self.path):
            raise FileNotFoundError(f"The file at {self.path} does not exist.")

        # Get file modification time
        mod_time = os.path.getmtime(self.path)
        self.metadata = {
            'Last Modified': datetime.datetime.fromtimestamp(mod_time),  # Last modified date
            'File Size (bytes)': os.path.getsize(self.path),  # File size
            'Operating System': self._try_identify_os(),  # Operating system #XXX: not what i wanted
            'File Path': self.path  # Full path of the file
        }

    def _try_identify_os(self):
        for wextension in config.WINDOWS_RELATED_EXTENSIONS:
            if self.path.endswith(wextension):
                return "WINDOWS"
        
        for wextension in config.LINUX_RELATED_EXTENSIONS:
            if self.path.endswith(wextension):
                return "LINUX"
        
        return "UNKNOWN"

    def get_result(self) -> dict:
        """Returns the scanned metadata for the file."""
        return self.metadata

    def format_data(self) -> dict:
        """Formats the file metadata into a more understandable dictionary."""
        formatted_data = {
            'Last Modified': self.metadata['Last Modified'].strftime("%Y-%m-%d %H:%M:%S"),  # Formatted last modified date
            'File Size': f"{self.metadata['File Size (bytes)']} bytes",  # File size in bytes
            'Operating System': self.metadata['Operating System'],  # OS
            'File Path': self.metadata['File Path'],  # Full path of the file
        }
        return formatted_data

#Example of usage
# For Image
image_scanner = ImageScanner()
image_scanner.set_path(r"path\to\image")
image_scanner.scan()
formatted_image_data = image_scanner.format_data()
print(formatted_image_data)

# For Video
video_scanner = VideoScanner()
video_scanner.set_path(r"path\to\video")
video_scanner.scan()
formatted_video_data = video_scanner.format_data()
print(formatted_video_data)

# For Audio
audio_scanner = AudioScanner()
audio_scanner.set_path(r"path\to\audio")
audio_scanner.scan()
formatted_audio_data = audio_scanner.format_data()
print(formatted_audio_data)


# For Other files
other_scanner = OtherScanner()
other_scanner.set_path(r"path\to\other\file")  # Change to your file path
try:
    other_scanner.scan()
    formatted_other_data = other_scanner.format_data()
    print("Other File Data:", formatted_other_data)
except FileNotFoundError as e:
    print(e)