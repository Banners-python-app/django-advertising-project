from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
import vercel_blob
from whitenoise.storage import CompressedManifestStaticFilesStorage

@deconstructible
class VercelBlobStorage(Storage):
    def _save(self, name, content):
        # 1. Read the binary data from the uploaded file
        file_data = content.read()
        
        # 2. Upload to Vercel Blob
        # 'addRandomSuffix' prevents overwriting if two files have the same name
        response = vercel_blob.put(name, file_data, options={'addRandomSuffix': 'true'})
        
        # 3. Vercel returns a full absolute URL for the image.
        # We return this URL so Django saves it directly into the database!
        return response['url']

    def url(self, name):
        # Because we saved the absolute Vercel URL in the DB in _save(), 
        # we can just return the name exactly as it is.
        return name

    def exists(self, name):
        # Vercel handles naming collisions automatically with the random suffix,
        # so we tell Django to just pass the file through without checking.
        return False
    
class RelaxedWhiteNoiseStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False   # returns unhashed path instead of crashing