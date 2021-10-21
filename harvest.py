from google_auth_oauthlib.flow import InstalledAppFlow
import sqlite3

db = sqlite3.connect('google-photos.db')

def get_session():

    # Create the flow using the client secrets file from the Google API
    # Console.
    flow = InstalledAppFlow.from_client_secrets_file(
        '~/.secrets/guidowb.json',
        scopes=['https://www.googleapis.com/auth/photoslibrary.readonly'],
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')

    # Tell the user to go to the authorization URL.
    auth_url, _ = flow.authorization_url(prompt='consent')

    print('Please go to this URL: {}'.format(auth_url))

    # The user will get an authorization code. This code is used to get the
    # access token.
    code = input('Enter the authorization code: ')
    flow.fetch_token(code=code)

    # You can use flow.credentials, or you can just get a requests session
    # using flow.authorized_session.
    session = flow.authorized_session()

    return session

def process_paged_results(url, itemKey, callback, context = None):
    response = session.get(url)
    if response.status_code != 200:
        print(response.headers)
        print(response.text)
        return
    result = response.json()
    items = result.get(itemKey, [])
    for item in items:
        callback(item, context)
    nextpagetoken = result.get('nextPageToken', '')
    while nextpagetoken != '':
        pageUrl = url
        if "?" in url:
            pageUrl = url + "&pageToken={}".format(nextpagetoken)
        else:
            pageUrl = url + "?pageToken={}".format(nextpagetoken)
        response = session.get(pageUrl)
        if response.status_code != 200:
            print(response.headers)
            print(response.text)
            return
        result = response.json()
        items = result.get(itemKey, [])
        for item in items:
            callback(item, context)
        nextpagetoken = result.get('nextPageToken', '')

def process_albums():
    process_paged_results('https://photoslibrary.googleapis.com/v1/albums', 'albums', process_album)

def process_album(album, context):
    id = album['id']
    title = album['title']
    count = int(album.get('mediaItemsCount', '0'))
    print('Found album {} title {} with {} items'.format(id, title, count))
    sql = 'INSERT OR IGNORE INTO ALBUM (id, title, count) values(?, ?, ?)'
    data = [(id, title, count)]
    db.executemany(sql, data)
    db.commit()
    process_album_content(album)

def process_album_content(album):
    albumId = album['id']
    process_paged_results('https://photoslibrary.googleapis.com/v1/mediaItems?albumId={}'.format(albumId), 'mediaItems', process_album_member, album)

def process_album_member(media, album):
    albumId = album['id']
    albumTitle = album['title']
    mediaId = media['id']
    print('Found member {}'.format(mediaId))
    sql = 'INSERT OR IGNORE INTO MEDIA_ALBUM_ID (media, album) values(?, ?)'
    data = [(mediaId, albumId)]
    db.executemany(sql, data)
    sql = 'INSERT OR IGNORE INTO MEDIA_ALBUM_TITLE (media, album) values(?, ?)'
    data = [(mediaId, albumTitle)]
    db.executemany(sql, data)
    db.commit()

def process_library_content():
    process_paged_results('https://photoslibrary.googleapis.com/v1/mediaItems', 'mediaItems', process_media_item)

def process_media_item(item, context):
    id = item['id']
    description = item.get('description', '---')
    print('Found item {} description {}'.format(id, description))
    sql = 'INSERT OR IGNORE INTO MEDIA (id, description) values(?, ?)'
    data = [(id, description)]
    db.executemany(sql, data)
    db.commit()

def insert_media():
    sql = 'INSERT OR IGNORE INTO MEDIA (id, description) values(?, ?)'
    data = [('fake1', 'fake1'), ('fake2', 'fake2')]
    db.executemany(sql, data)
    db.commit()

def delete_fake_media():
    sql = 'DELETE FROM MEDIA WHERE id LIKE ?'
    data = [('fake%',)]
    db.executemany(sql, data)
    db.commit()

def count_media():
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM MEDIA")
    rows = cur.fetchall()
    for row in rows:
        print(row)    
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM MEDIA_ALBUM_ID")
    rows = cur.fetchall()
    for row in rows:
        print(row)    
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM MEDIA_ALBUM_TITLE")
    rows = cur.fetchall()
    for row in rows:
        print(row)    

def create_db():
    with db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS MEDIA (
                id TEXT NOT NULL PRIMARY KEY,
                description TEXT
            );
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS ALBUM (
                id TEXT NOT NULL PRIMARY KEY,
                title TEXT,
                count INTEGER
            );
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS MEDIA_ALBUM_ID (
                media TEXT,
                album TEXT,
                PRIMARY KEY(media, album)
            );
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS MEDIA_ALBUM_TITLE (
                media TEXT,
                album TEXT,
                PRIMARY KEY(media, album)
            );
        """)

if __name__ == '__main__':
    # create_db()
    session = get_session()
    process_library_content()
    # process_albums()
    # insert_media()
    # delete_fake_media()
    count_media()
