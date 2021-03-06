import facebook
import pika
import configparser
import json
import arrow
import pprint
from helper import facebook_helper as fb
from helper import log_helper
from helper import rabbitmq_helper as rabbit
from helper import mongo_helper as mongodb
from pymongo.errors import DuplicateKeyError

logger = log_helper.get_logger('facebook-comments-fetcher')

config = configparser.ConfigParser()
config.read('config/production.ini')

mongo_client = mongodb.get_mongo_client(config['mongodb']['uri'])
comments_collection = mongo_client.guess_what_facebook.comments
reply_comments_collection = mongo_client.guess_what_facebook.reply_comments

queue_channel = rabbit.get_rabbit_channel(
    user=config['rabbitmq']['user'],
    password=config['rabbitmq']['pass'],
    host=config['rabbitmq']['host'],
    port=int(config['rabbitmq']['port']),
)


graph = fb.get_facebook_graph(access_token=config['facebook']['user_token'])

def callback(ch, method, properties, body):
    post = json.loads(body.decode('utf-8'))
    post_id = post['id']
    comments = fb.get_comments(graph, post_id=post_id)
    logger.info("Comments of post_id = {}, length = {}".format(
        post_id,
        len(comments))
    )
    for comment in comments:
        # insert comment to db
        comment_id = comment['id']
        comment_created_time = comment['created_time']
        
        comment['_id'] = comment['id']
        comment['parent_post_id'] = post_id
        if 'parent' in comment:
            comment['parent_comment_id'] = comment['parent']['id']
            try:
                inserted_id = reply_comments_collection.insert_one(comment).inserted_id 
            except DuplicateKeyError:
                pass
            logger.info('[++] Insert reply-comment to DB, comment_id = {}, created_time = {}'.format(
                comment_id, 
                comment_created_time
            ))
        else:
            try:
                inserted_id = comments_collection.insert_one(comment).inserted_id 
            except DuplicateKeyError:
                pass
            logger.info('[+] Insert comment to DB, comment_id = {}, created_time = {}'.format(
                comment_id, 
                comment_created_time
            ))
    ch.basic_ack(delivery_tag = method.delivery_tag)

queue_channel.basic_qos(prefetch_count=1)
queue_channel.basic_consume(
    callback,
    queue="fb:post:get-comments",
    no_ack=False)
queue_channel.start_consuming()
