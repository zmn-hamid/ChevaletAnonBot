# Chevalet Anon Bot (Original)

The most awesome telegram bot to send messages to other users anonymously written in Python.

## A Word About How and Why I Made this project

I started this project in August 2024. This projected was always on my mind since I learned
python (tho a much smaller version). But I finally started working on it when one of the most
popular anonymous bots in the community turned out to be spying on people. I published the bot
with the help of my friend [Atur](https://github.com/aturzone) (props to
him for providing the server all these years. I was only the programmer). He also had a big
art channel at the time which was a good starting point for people to trust us.

I was naive. Don't get me wrong, I was very much capable of creating a bot of this
scale and complexity. At the time being, no gen AI was powerful enough to help me
with the `python-telegram-bot` package. I had to code almost everything by myself.
I managed it because I had been making (almost unpublished) telegram bots for about 2 years.

But I grew up with this project as my life went on.
I didn't know many things, most of which were about maintenance. I learnt things as basic
as "what's `__init__.py` used for", or as top level as "what does
docker do". You can see this clearly in the git history.

That's why I'm not at all happy with the current state of this project. Though
one can say it's enough for a project this size, It's not something I'd advertise as my
most profound repo. Before making this project public, I was thinking of restructuring the
whole project, but due to how big the project is and how many changes is needed, I prefer not
to touch it anymore. I will make a template python telegram project in the future which
will most precisely show my skillset and what a professional, scalable and understandable PTB project can
look like.

Currently the project is offline because it has been migrated to a Golang version by
Atur and is maintained by him. I will not continue this project anymore.

## Features

The bot is only in Persian language.

**Unique features**

- multiple links per user - customizable - usable for people with multiple audiences
- sending message by replying to the recieved message (no need for manually pressing the "reply" button)
- sending message by replying to a channel post - The post will be sent to the replied admin if they provided
the url in the syntax mentioned. otherwise it's just a blank reply (reply is preserved)
- quote reply to a part of a text (quote is perserved)
- gallery messages
- disabling the message preview forcefully
- default tag for audios - This feature was useful back then when Telegram didn't show the message sender
(when forwarding) for audios, so I added this feature and enabled it by default so every audio
is appended a "\[Unknown\]" tag when received.
- unblock features - Unblock everyone you've blocked, or get unblocked by the user who accidentally
blocked you or whatever (by sending a unblock url, which the user can click and unblock/re-block you)
- two layer obfuscation - Each user is assigned a chevaltid and that chevaletid is encoded using a custom
encoder each time so absolutely no private info is leaked.

**Usual features**

- enable/disable "seen" button (button to tell the other party they have been seen)
- enable/disable undo message feature
- custom message tags - applied to the end of the received messages

## How to setup

1. install `docker` and `docker compose`
2. clone the repository
3. run `make up`. if faced some errors you might want to run it again
4. here you can restore a backup. when bot is up, use `make restore` to restore
a specific backup file (backup file path pattern: `backups/backup_*.sql.gz`).  
Tip: you can send a backup file to your server using `scp` command on windows.
5. run `make backup-setup-auto` to add the hourly backup cron job
6. if needed to update the bot: `make update`

### Known issues

- health checker for bot is not working properly

### additional info

- git history might be a bit odd since the conventions has changed a bit. but generally you
can follow these conventions:
    - `feat` for features. anything new and of value
    - `fix` for fixing bugs only
    - `maint` for any maintenance stuff. including refactoring code, updating requirements
        or basically anything