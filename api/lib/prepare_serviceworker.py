from loguru import logger
from lib.app_config import get_app_config
from pathlib import Path



@logger.catch
def prepare_serviceworker():
    file = Path("www/firebase-messaging-sw.js")
    if file.is_file():

        # Safely read the input filename using 'with'
        with open(file) as f:
            s = f.read()

        # Safely write the changed content, if found in the file
        with open(file, 'w') as f:
            
            s = s.replace("INSERT_API_KEY_HERE", get_app_config().apiKey)
            s = s.replace("INSERT_AUTH_DOMAIN_HERE", get_app_config().authDomain)
            s = s.replace("INSERT_PROJECT_ID_HERE", get_app_config().projectId)
            s = s.replace("INSERT_STORAGE_BUCKET_HERE", get_app_config().storageBucket)
            s = s.replace("INSERT_MESSAGING_SENDER_ID_HERE", get_app_config().messagingSenderId)
            s = s.replace("INSERT_MEASUREMENT_ID_HERE", get_app_config().measurementId)
            s = s.replace("INSERT_APP_ID_HERE", get_app_config().appId)
            f.write(s)
    else:
        logger.error("./www/public/firebase-messaging-sw.js - File not found")
