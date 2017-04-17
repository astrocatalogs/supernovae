
import tweepy

# Consumer keys and access tokens, used for OAuth
with open('consumer.key', 'r') as f:
    consumer_key = f.read().strip()
with open('consumer.secret', 'r') as f:
    consumer_secret = f.read().strip()
with open('access.key', 'r') as f:
    access_token = f.read().strip()
with open('access.secret', 'r') as f:
    access_token_secret = f.read().strip()

# OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Creation of the actual interface, using authentication
api = tweepy.API(auth)

# Sample method, used to update a status
api.update_status(status='First post!')
