#!/usr/bin/env python
# coding=utf-8

# tested on debian 8.5, you need python-pip to install the following modules:
# pyyaml, bs4, slackclient, translate

import random
import sys
import time

import requests
import yaml
from bs4 import BeautifulSoup, FeatureNotFound
from slackclient import SlackClient
from translate import Translator

# load config
try:
    from settings import *
except ImportError:
    print "Could not find settings.py or there was an error loading it."
    sys.exit(1)


# load yaml file w/ SA dictionary
def yaml_loader(filepath):
    with open(filepath, "r") as file_descriptor:
        data = yaml.load(file_descriptor)
    return data


def __send_response(text, icon_url='ru', emoji='null'):
    if "emoji" in icon_url:
      sc.api_call('chat.postMessage',
                  username=BOT_NAME,
                  icon_emoji=emoji,
                  as_user='false',
                  channel=evt["channel"],
                  text=text)
    else:
      sc.api_call('chat.postMessage',
                  username=BOT_NAME,
                  icon_url=icon_url,
                  as_user='false',
                  channel=evt["channel"],
                  text=text)


# Magic 8 Ball function
def eight_ball():
    answers = [
        "It is certain.",
        "Outlook good.",
        "You may rely on it.",
        "Ask again later.",
        "Concentrate and ask again.",
        "Reply hazy, try again.",
        "My reply is no.",
        "My sources say no.",
    ]
    __send_response(random.choice(answers), icon_poolball)


# Sysadmin Dictionary function
def __sa_dictionary(message):
    # print("in saDictionary def")
    blob = ""

    if message in yamldata["words"]:
        blob = blob + "*pronunciation:* _/" + yamldata["words"][message][
            "pronunciation"] + "/_\n"

        for lookup in ('definition', 'usage', 'symptoms', 'synonyms'):
            try:
                if isinstance([yamldata["words"][message][lookup]], list):
                    blob = blob + "\n*" + lookup + "*\n\n"
                    for item in yamldata["words"][message][lookup]:
                        i = yamldata["words"][message][lookup][item]
                        n = str(item)
                        if lookup == 'synonyms':
                            ele = yamldata["words"][message][lookup].keys()[-1]
                            # els = list(yamldata["words"][word][lookup].items())
                            # foo,ele,bar = word.split('\'')
                            print(yamldata["words"][message][lookup][ele])
                            if i == yamldata["words"][message][lookup][ele]:
                                blob = blob + "  " + i
                            else:
                                blob = blob + "  " + i + ","
                        else:
                            blob = blob + "  " + n + ". " + i + "\n"
            except KeyError:
                pass
    return blob


# define function
def define(message):
    # print("in define function: "+word)
    if message in yamldata["words"]:
        sa_def = __sa_dictionary(str(message))
        resp = '<@{}> The Sys Admin dictionary defines `{}` as \n>>>{}'.format(
            evt["user"], message, sa_def)
        __send_response(resp, icon_tux)
    else:
        payload = {'term': message}
        r = requests.get(
            "http://www.urbandictionary.com/define.php", params=payload)
        try:
            soup = BeautifulSoup(r.content, "lxml")
        except FeatureNotFound:
            soup = BeautifulSoup(r.content, "html.parser")
        ud_def = soup.find("div", attrs={"class": "meaning"}).text
        resp = '<@{}> Urban Dictionary defines `{}` as ```{}```'.format(
            evt["user"], message, ud_def)
        __send_response(resp, icon_urban_dictionary)


# Universal Translator
def __trans(flag, lang, message):
    try:
        if len(message) > MAX_TRANSLATE_LENGTH:
            resp = "Don't be a dick <@{}>".format(evt["user"])
            __send_response(resp, icon_ru)
        else:
            translator = Translator(to_lang=lang)
            l = translator.translate(message)
            __send_response(l, "emoji", flag)
    except ValueError:
        resp = 'Vhy try to anger {} <@{}>?'.format(BOT_NAME, evt["user"])
        __send_response(resp, icon_ru)


def magyar(message):
    __trans(":flag-hu:", "hu", message)


def russian(message):
    __trans(":flag-ru:", "ru", message)


def unitr(command, message):
    _, lang = command.split(":")
    __trans(":flag-{}:".format(lang), lang, message)


def angry(message=u"Что ебать ты от меня хочешь? Я не понимаю!"):
    __send_response(message,"emoji",":angry:")


def help(message):
    resp = 'In Soviet Russia <@{}> helps <@{}>.'.format(evt["user"], evt["user"])
    __send_response(resp, icon_ru)


def HELP(message):
    resp = 'VHY YOU YELL AT ME <@{}>!'.format(evt["user"])
    __send_response(resp, "emoji", ":crying_cat_face:")


def leave(message):
    resp = 'I bot. leave you <@{}>!'.format(evt["user"])
    __send_response(resp)

# Main program, slack client.
yamldata = yaml_loader("sa.yaml")
sc = SlackClient(token)
try:
    if sc.rtm_connect():
        bot_mention = "<@{}".format(sc.server.login_data["self"]["id"])

        while True:
            for evt in sc.rtm_read():
                if "type" in evt and evt["type"] == "message" and "text" in evt:
                    message = evt["text"].encode('utf8', 'replace').strip()
                    #print(evt)
                    if "channel" in evt and evt["type"] == "message" and evt["channel"].startswith("D"):
                      #here is a hook for dealing with direct messages; upcoming feature
                      if message.startswith("<#C"):
                        channel,message = message.split(None, 1)
                        channel=channel[2:-1]
                        evt["channel"]=channel
                        print(message)
                    if message.startswith(bot_mention):
                        try:
                            # have a botname, command, and message?
                            _, command, message = message.split(None, 2)
                        except ValueError:
                            try:
                                # maybe just a botname and command?
                                _, command = message.split(None, 1)
                            except ValueError:
                                # fuck you. this should never happen....
                                angry(
                                    u"Как вы сюда попали? Пищу в вашем шифрования, если вы не говорите мне!")

                        if command.startswith('__'):
                            angry(
                                u"Это секрет. В Советской России секрет принадлежит вам!")
                        elif command.startswith('tr:'):
                            unitr(command, message)
                        elif command == "8ball":
                            eight_ball()
                        else:
                            try:
                                # http://stackoverflow.com/a/16683842/436190
                                args_dict = {'message': message}
                                globals()[command](**args_dict)
                            except:
                                angry(
                                    u"Вы датировать commandme? В Советской России бот команда, которую вы!")
            time.sleep(.1)
    else:
        if sc.server.login_data is None:
            print "Connection failed. Probably a bad/missing token."
        else:
            print "Connection failed. Server response: {}".format(
                sc.server.login_data["ok"])
except KeyboardInterrupt:
    sys.exit()
