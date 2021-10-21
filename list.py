from google_auth_oauthlib.flow import InstalledAppFlow

def get_session():

    # Create the flow using the client secrets file from the Google API
    # Console.
    flow = InstalledAppFlow.from_client_secrets_file(
        '/Users/guidowb/.secrets/guidowb.json',
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

def process_albums():
    result = session.get('https://photoslibrary.googleapis.com/v1/albums').json()
    albums = result['albums']
    for album in albums:
        process_album(album)
    nextpagetoken = result.get('nextPageToken', '')
    while nextpagetoken != '':
        result = session.get('https://photoslibrary.googleapis.com/v1/albums?pageToken={}'.format(nextpagetoken)).json()
        albums = result['albums']
        for album in albums:
            process_album(album)
        nextpagetoken = result.get('nextPageToken', '')

albums={}

def process_album(album):
    global albums
    id = album['id']
    title = album['title']
    count = int(album.get('mediaItemsCount', '0'))
    print('Found album {} title {} with {} items'.format(id, title, count))
    entry = albums.get(title, { 'title': title, 'count': 0, 'ids': [], 'empties': [] })
    entry['count'] = entry['count'] + count
    entry['ids'].append(id)
    if count == 0:
        entry['empties'].append(id)
    albums[title] = entry

def list_albums():
    global albums
    print('\n---\n')
    print('Found {} unique album titles'.format(len(albums)))
    for title in albums:
        album = albums[title]
        print('- {} occurred {} times ({} empty) with {} total items'.format(title, len(album['ids']), len(album['empties']), album['count']))

if __name__ == '__main__':
    session = get_session()
    process_albums()
    list_albums()
