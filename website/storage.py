import os
from storages.backends.s3boto3 import S3Boto3Storage


class SupabaseStorage(S3Boto3Storage):
    def url(self, name):
        bucket = os.getenv('SUPABASE_S3_BUCKET')
        project_url = os.getenv('SUPABASE_URL')
        return f"{project_url}/storage/v1/object/public/{bucket}/{name}"
