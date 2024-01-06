# from constants import http_status_codes
# import datetime
# import uuid
# import os
#
#
# def upload_file(file, container_client):
#     try:
#         if file.filename == '':
#             return {
#                 "responseMessage": "No selected file",
#                 "responseCode": http_status_codes.HTTP_400_BAD_REQUEST
#             }
#
#         # Generate a unique filename using timestamp and/or uuid
#         timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#         unique_id = str(uuid.uuid4())
#         original_filename, file_extension = os.path.splitext(file.filename)
#         unique_filename = f"{original_filename}_{timestamp}_{unique_id}{file_extension}"
#
#         blob_client = container_client.get_blob_client(unique_filename)
#         blob_client.upload_blob(file)
#         return {
#             'original_name': original_filename,
#             'filename': unique_filename,
#             'responseCode': http_status_codes.HTTP_200_OK,
#             'responseMessage': 'File uploaded successfully'
#         }
#     except Exception as err:
#         return {
#             "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
#             "responseMessage": "Something Went Wrong!!",
#             "error": str(err)
#         }