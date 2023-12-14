# sit2stand.ai 

[Sit2stand.ai](https://sit2stand.ai/) is a web-app for deriving health-related metrics from a mobile phone video. 

## Quick start

The platform is developped in django so it can be deployed as any other django application

1. Install requirements with:
```
pip install -r requirements.txt
```
2. Check settings in `motionlab/settings.py`. In particular, make sure to configure it to run on your database and AWS S3 servers.
3. Migrate the database with (you may need to manually create a folder called "data" to store the local database):
```
python manage.py migrate
```
4. Start the server with:
```
python manage.py runserver
```
5. Visit http://127.0.0.1:8000/ in your browser
