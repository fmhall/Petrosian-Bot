import os
from typing import Tuple, Union
from praw import Reddit
from praw.models import Submission, Subreddit, Comment
from dotenv import load_dotenv
import pickledb
from typing import Iterator, Callable
import threading
import logging

log_format = "%(asctime)s: %(threadName)s: %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO, datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# I've saved my API token information to a .env file, which gets loaded here
load_dotenv()
CLIENT = os.getenv("CLIENT_ID")
SECRET = os.getenv("CLIENT_SECRET")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

KEYWORDS = ["pipi", "pampers", "tigran", "petrosian"]

# Set the path absolute path of the chess_post database
pickle_path = os.path.dirname(os.path.abspath(__file__)) + "/comments.db"
db = pickledb.load(pickle_path, True)

# Create the reddit object instance using Praw
reddit = Reddit(
    user_agent="petrosian_bot",
    client_id=CLIENT,
    client_secret=SECRET,
    username=USERNAME,
    password=PASSWORD,
)


def restart(handler: Callable):
    """
    Decorator that restarts threads if they fail
    """

    def wrapped_handler(*args, **kwargs):
        logger.info("Starting thread with: %s", args)
        while True:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error("Exception: %s", e)

    return wrapped_handler


@restart
def iterate_comments(subreddit_name: str):
    """
    The main loop of the program, called by the thread handler
    """
    # Instantiate the subreddit instances
    sub: Subreddit = reddit.subreddit(subreddit_name)

    for comment in sub.stream.comments():
        logger.debug(f"Analyzing {comment.body}")
        if should_comment_on_comment(comment):
            write_comment(comment)
            logger.info(f"Added comment to comment {str(comment.body)}")
        else:
            logger.debug("Not commenting")


@restart
def iterate_posts(subreddit_name: str):
    """
    The main loop of the program, called by the thread handler
    """
    # Instantiate the subreddit instances
    sub: Subreddit = reddit.subreddit(subreddit_name)

    for post in sub.stream.submissions():
        logger.debug(f"Analyzing post {post.title}")
        if should_comment_on_post(post):
            write_comment(post)
            logger.info(f"Added comment to post {str(post.title)}")
        else:
            logger.debug("Not commenting")


def should_comment_on_comment(comment: Comment) -> bool:
    lower_case_body = str(comment.body).lower()
    obj_id = str(comment.id)
    has_keywords = False
    for keyword in KEYWORDS:
        if keyword in lower_case_body:
            has_keywords = True
    if not has_keywords:
        return False
    if comment.author == USERNAME:
        if not db.get(obj_id):
            db.set(obj_id, [obj_id])
            db.dump()
        return False
    if not db.get(obj_id):
        db.set(obj_id, [obj_id])
        db.dump()
        return True
    return False


def should_comment_on_post(post: Submission) -> bool:
    body = str(post.selftext).lower()
    title = str(post.title).lower()
    obj_id = str(post.id)
    has_keywords = False
    for keyword in KEYWORDS:
        if keyword in body or keyword in title:
            has_keywords = True
    if not has_keywords:
        return False
    if post.author == USERNAME:
        if not db.get(obj_id):
            db.set(obj_id, [obj_id])
            db.dump()
        return False
    if not db.get(obj_id):
        db.set(obj_id, [obj_id])
        db.dump()
        return True
    return False


def write_comment(obj: Union[Comment, Submission]):
    pasta = """Are you kidding ??? What the **** are you talking about man ? You are a biggest looser i ever seen in my life ! You was doing PIPI in your pampers when i was beating players much more stronger then you! You are not proffesional, because proffesionals knew how to lose and congratulate opponents, you are like a girl crying after i beat you! Be brave, be honest to yourself and stop this trush talkings!!! Everybody know that i am very good blitz player, i can win anyone in the world in single game! And "w"esley "s"o is nobody for me, just a player who are crying every single time when loosing, ( remember what you say about Firouzja ) !!! Stop playing with my name, i deserve to have a good name during whole my chess carrier, I am Officially inviting you to OTB blitz match with the Prize fund! Both of us will invest 5000$ and winner takes it all!
I suggest all other people who's intrested in this situation, just take a look at my results in 2016 and 2017 Blitz World championships, and that should be enough... No need to listen for every crying babe, Tigran Petrosyan is always play Fair ! And if someone will continue Officially talk about me like that, we will meet in Court! God bless with true! True will never die ! Liers will kicked off...\n\n"""

    source_tag = (
        "[^(fmhall)](https://www.reddit.com/user/fmhall) ^| [^(github)]({})\n".format(
            "https://github.com/fmhall/Petrosian-Bot"
        )
    )

    comment_string = pasta + source_tag
    obj.reply(comment_string)


if __name__ == "__main__":
    logger.info("Main    : Creating threads")
    threads = []
    chess_posts_thread = threading.Thread(
        target=iterate_posts, args=("chess",), name="chess_posts"
    )
    ac_posts_thread = threading.Thread(
        target=iterate_posts, args=("anarchychess",), name="ac_posts"
    )
    chess_comments_thread = threading.Thread(
        target=iterate_comments, args=("chess",), name="chess_comments"
    )
    ac_comments_thread = threading.Thread(
        target=iterate_comments, args=("anarchychess",), name="ac_comments"
    )

    threads.append(chess_posts_thread)
    threads.append(ac_posts_thread)
    threads.append(chess_comments_thread)
    threads.append(ac_comments_thread)

    logger.info("Main    : Starting threads")
    for thread in threads:
        thread.start()
