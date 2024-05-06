from instagrapi import Client
import random
import requests
import os
from instagrapi.exceptions import LoginRequired
import logging
import email
import imaplib
import re
from instagrapi.mixins.challenge import ChallengeChoice
import base64
from requests.exceptions import ProxyError
from urllib3.exceptions import HTTPError

from instagrapi import Client
from instagrapi.exceptions import (
    ClientConnectionError,
    ClientForbiddenError,
    ClientLoginRequired,
    ClientThrottledError,
    GenericRequestError,
    PleaseWaitFewMinutes,
    RateLimitError,
    SentryBlock,
)


logger = logging.getLogger()


def challenge():
    usePasswordChange = False
    try:
            
            client.challenge_code_handler = challenge_code_handler
            if usePasswordChange:
                client.change_password_handler = change_password_handler
                usePasswordChange=False
    except Exception as e:
        logger.log("Issue in challenge!")



# Define your Gmail API scopes

def get_code_from_email(username):
    mail = imaplib.IMAP4_SSL("mail.inbox.lv")
    mail.login(CHALLENGE_EMAIL, CHALLENGE_PASSWORD)
    mail.select("inbox")
    result, data = mail.search(None, "(UNSEEN)")
    assert result == "OK", "Error1 during get_code_from_email: %s" % result
    ids = data.pop().split()
    for num in reversed(ids):
        mail.store(num, "+FLAGS", "\\Seen")  # mark as read
        result, data = mail.fetch(num, "(RFC822)")
        assert result == "OK", "Error2 during get_code_from_email: %s" % result
        msg = email.message_from_string(data[0][1].decode())
        payloads = msg.get_payload()
        if not isinstance(payloads, list):
            payloads = [msg]
        code = None
        for payload in payloads:
            payload = payload.get_payload()
            if isinstance(payload, bytes):
                try:
                    body = base64.b64decode(payload).decode('utf-8')
                except UnicodeDecodeError:
                    # Handle decoding error
                    body = "Unable to decode payload"
            else:
                body = payload
            if "<div" not in body:
                continue
            match = re.search(">([^>]*?({u})[^<]*?)<".format(u=username), body)
            if not match:
                continue
            print("Match from email:", match.group(1))
            match = re.search(r">(\d{6})<", body)
            if not match:
                print('Skip this email, "code" not found')
                continue
            code = match.group(1)
            if code:
                return code
    return False

def get_code_from_sms(username):
    while True:
        code = input(f"Enter code (6 digits) for {username}: ").strip()
        
        if code and code.isdigit():
            return code
    return None


def challenge_code_handler(username, choice):
    if choice == ChallengeChoice.SMS:
        return get_code_from_sms(username)
    elif choice == ChallengeChoice.EMAIL:
        ecode = get_code_from_email(username)
        print("CODE: ", ecode)
        return ecode
    usePasswordChange=True
    return False


def change_password_handler(username):
    # Simple way to generate a random string
    chars = list("abcdefghijklmnopqrstuvwxyz1234567890!&£@#")
    
    password = "".join(random.sample(chars, 10))
    with open("credentials.txt", "r") as f:
        data=f.readlines()

    data[1]=password+"\n"

    with open("credentials.txt", "w", encoding='utf-8') as f:
        data=f.writelines(data)
    return password

def sendMessage(follower_id, targetUsername):
    with open("messageToSend.txt", "r") as f:
        data=f.readlines()


    try:
        msg = client.direct_send(text = data, user_ids=[follower_id])
        if msg:
            print(f"Messaged {follower_id}") 
    except Exception as e:
         challenge()
         logger.info("Could not direct message: %s" % e)

def likeStory(follower_id):
    try:
        user_story= client.user_stories(follower_id)
    #check if user has active story
        if user_story:
            print(f"{follower_id}'s liked: ", client.story_like(follower_id))
    except Exception as e:
         #challenge()
         print("Could not like the story: %s" % e) 

def followUser(follower_id):
    try:
        is_following = client.user_following(follower_id)
        print(f"{follower_id} followed: ", client.user_follow(user_id=follower_id))
    except Exception as e:
         challenge()
         #("Could not follow the user: %s" % e)

def likePost(follower_id):
    mediaList=client.user_medias(user_id = follower_id, amount=10)
    try:
        if mediaList:
            randomMedia= random.choice(mediaList)
            media_id = randomMedia.id
            print(f"{follower_id}'s media liked: ", client.media_like(media_id = media_id ))
    except Exception as e:
         challenge()
         print("Could not like the post: %s" % e)

def botActivities():
        print("STARTING BOT ACTIVITIES")
#Get existing ids
        num_lines_to_read = 5
        list_of_ids = []
        #likeStory_variable= 1
        #sendMessage_variable = 2
        #likePost_variable = 3
        with open("follower_ids.txt","r") as f:
            for _ in range(num_lines_to_read):
                line = f.readline().strip()
                if not line:
                    break  # Break if the end of the file is reached
                list_of_ids.append(line)
        for follower_id in list_of_ids:
    #print("Follower ID:", follower_id)
    #followUser(follower_id)
            
            choice = random.randint(1,2)
            if choice==1:
                likePost(follower_id)
            elif choice==2:
                followUser(follower_id)
            sendMessage(follower_id,target_username)
            likeStory(follower_id)
            print("BOT ACTIVITIES IN PROGRESS")
        
        with open("follower_ids.txt", 'r') as f:
        # Read all lines into a list
            lines = f.readlines()
            
        with open("follower_ids.txt", 'w') as f:
        # Write the remaining lines back to the file
            for line in lines:
                if line.strip() not in list_of_ids:
                    f.write(line)      

def startBot():
    for x in range(0,20):
        end_cursor_id = ""
        try:
            print(f"Getting followers from: {target_username}")
        # Define the account_id, curr, and all values
            account_id = client.user_id_from_username(target_username)
            # Open the file in read mode
            with open('follower_ids.txt', 'r') as file:
                lines = file.readlines()
            if len(lines) == 0:
                with open('endFollower.txt', 'r') as file:
                    lines_end_follower = file.readlines()
                if len(lines_end_follower)==0:
                    end_cursor_id=None
                else:
                    end_cursor_id=lines_end_follower[0]
                print("STARTING TO COLLECT FOLLOWERS")
                followers=client.user_followers_gql_chunk(user_id = account_id, max_amount=5, end_cursor=end_cursor_id)
                print(followers)
                followers_list=followers[0]
                followers_ids=[follower.pk for follower in followers_list]
                print (followers_ids)
                with open('endFollower.txt','w') as file:
                    file.write(followers[1])
                print(f"Last followers id: {followers_ids[-1]}")
                with open('follower_ids.txt', 'w') as file:
                    for follower in followers_ids:
                        file.write(follower+"\n")
                botActivities()
            else:
                botActivities()
        except Exception as e:
            print("ERROR IN COLLECTING CLIENTS")
            challenge()
                #follower_id= f.readline().strip()

def next_proxy():
    return random.choice(
        [
            "http://username:password@147.123123.123:412345",
            "http://username:password@147.123123.123:412346",
            "http://username:password@147.123123.123:412347",
        ]
    )


if __name__=="__main__":
    with open("challengeEmail.txt","r") as f:
        CHALLENGE_EMAIL, CHALLENGE_PASSWORD = f.read().splitlines()
    
    if True:
        with open("credentials.txt","r") as f:
            username, password, target_username= f.read().splitlines()
        with open("challengeEmail.txt","r") as f:
            CHALLENGE_EMAIL, CHALLENGE_PASSWORD = f.read().splitlines()

        client = Client() #proxy=next_proxy()
        try:
                 
                 client.login(username, password)
                 client.delay_range = [5,120]
                 startBot()
    #     except (ProxyError, HTTPError, GenericRequestError, ClientConnectionError):
    # # Network level
    #         client.set_proxy(next_proxy())
    #     except (SentryBlock, RateLimitError, ClientThrottledError):
    # # Instagram limit level
    #         client.set_proxy(next_proxy())
    #     except (ClientLoginRequired, PleaseWaitFewMinutes, ClientForbiddenError):
    #         # Logical level
    #         client.set_proxy(next_proxy()) 
        except Exception as e:
                #challenge()
                print("ERROR LOGGING IN")
                #client.login(username, password)
               # client.delay_range = [5,120]
               # startBot()
        # Ensure to logout after bot activitiesclient.logout()
        client.logout()
            
        






    



# for follower_id in follower_ids:
#     #print("Follower ID:", follower_id)
#     #followUser(follower_id)

#     likeStory(follower_id)
#     sendMessage(follower_id,target_username)
#     likePost(follower_id)

