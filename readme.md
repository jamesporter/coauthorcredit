# Coauthor Credit

## Analyse who is really contributing to shared projects on Dropbox, with per-file leaderboards

Sign in via Google
Authorise Dropbox
Enter a (shared) folder name and open
Choose a file to see the leaderboard (see if you or your co-workers are pulling their weight).
NB Dropbox only gives revisions on free accounts for 30 days, longer for Pro.

## Deployment

You need to customise the application: in app.yaml and to create a dbx_keys.py file as per the template instructions.
You need to get keys from Dropbox/set up a Dropbox App.
Also, there is a url hardcoded in one place for the Dropbox token request (as we had issues getting this dynamically; no doubt an easy fix).

## Improvements

Lots of things could be improved: this was made in a few hours at Dropbox's 2015 London Hackathon.
Most of the frustration of working with this kind of thing is that code must be deployed to get tokens etc (so a way of locally testing it would be a good first step before developing things further)... perhaps with a 'local'/'dev' flag
Some tests would be good
We started with webhooks, although realised this wasn't necessary for our core idea. For realtime updates/actions these might be useful.
