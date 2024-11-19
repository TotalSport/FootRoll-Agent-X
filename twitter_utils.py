#------twitter_utils.py----#
import tweepy
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Получение токенов из переменных окружения
api_key = os.getenv("TWITTER_API_KEY")
api_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

# Проверка загрузки ключей
if not api_key or not api_secret or not access_token or not access_token_secret:
    print("Ошибка: Один или несколько ключей API Twitter не загружены")
    exit()

if not bearer_token:
    print("Ошибка: Bearer Token не загружен")
    exit()

# Инициализация клиента Tweepy с использованием OAuth1 для API v1.1
auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)
api_v1 = tweepy.API(auth)  # Клиент для использования API v1.1

# Инициализация клиента Tweepy с использованием Bearer Token для API v2
client_v2 = tweepy.Client(bearer_token=bearer_token,
                          consumer_key=api_key,
                          consumer_secret=api_secret,
                          access_token=access_token,
                          access_token_secret=access_token_secret)


class TwitterBot:

    def __init__(self, api_v1, client_v2):
        self.api_v1 = api_v1
        self.client_v2 = client_v2

    # Функция для публикации твита через API v2
    def post_tweet(self, content):
        try:
            response = self.client_v2.create_tweet(text=content)
            print("Твит опубликован успешно:", response)
            return response
        except tweepy.TweepyException as e:
            print("Ошибка при публикации твита:", e)
            return None

    # Функция для чтения упоминаний через API v1.1
    def read_mentions(self, count: int = 10) -> List[Dict]:
        try:
            mentions = self.api_v1.mentions_timeline(count=count)
            return [{
                'id': mention.id,
                'text': mention.text,
                'user': mention.user.screen_name,
                'created_at': mention.created_at
            } for mention in mentions]
        except tweepy.TweepyException as e:
            print("Ошибка при чтении упоминаний:", e)
            return [{'error': str(e)}]

    # Функция для ответа на твит через API v1.1
    def reply_to_tweet(self, tweet_id: str, content: str) -> str:
        try:
            tweet = self.api_v1.get_status(tweet_id)
            username = tweet.user.screen_name
            reply_content = f"@{username} {content}"

            reply = self.api_v1.update_status(
                status=reply_content,
                in_reply_to_status_id=tweet_id,
                auto_populate_reply_metadata=True)
            return f"Успешный ответ на твит {tweet_id}"
        except tweepy.TweepyException as e:
            print("Ошибка при ответе на твит:", e)
            return f"Ошибка при ответе на твит: {str(e)}"

    # Функция для поиска твитов через API v1.1
    def search_tweets(self, query: str, count: int = 10) -> List[Dict]:
        try:
            tweets = tweepy.Cursor(self.api_v1.search_tweets,
                                   q=query).items(count)
            return [{
                'id': tweet.id,
                'text': tweet.text,
                'user': tweet.user.screen_name,
                'created_at': tweet.created_at
            } for tweet in tweets]
        except tweepy.TweepyException as e:
            print("Ошибка при поиске твитов:", e)
            return [{'error': str(e)}]
