# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

import time
from datetime import datetime, timedelta
import random
from tinytag import TinyTag

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.skills.audioservice import AudioService
from mycroft.configuration import Configuration
from mycroft.configuration.config import SYSTEM_CONFIG, USER_CONFIG

from os.path import join, isfile, abspath, dirname, splitext
from os import path, listdir

from mycroft.util.log import getLogger
LOGGER = getLogger(__name__)

__author__ = 'aussieW'

class FartingSkill(MycroftSkill):
    def __init__(self):
        super(FartingSkill, self).__init__(name="FartingSkill")
        self.audioservice = None
        self.random_farting = False  # flag to indicate whether random farting mode is active
        self.counter=0  # variable to increment to make the scheduled event unique
        
        # Search the sounds directory for sound files and load into a list.
        valid_codecs = ['.mp3'] #, '.wav']
        self.path_to_sound_files = path.join(abspath(dirname(__file__)), 'sounds')
        self.sound_files = [f for f in listdir(self.path_to_sound_files) if splitext(f)[1] in valid_codecs]
        
        # cater for the picroft platform which behaves a bit differently from the mark1
        self.platform = "unknown"
        config = Configuration.get([SYSTEM_CONFIG, USER_CONFIG], cache=False)
        if "enclosure" in config:
            self.platform = config.get("enclosure").get("platform", "unknown")

    def initialize(self):
        self.register_intent_file('accuse.intent', self.handle_accuse_intent)
        self.register_intent_file('request.intent', self.handle_request_intent)
        self.register_intent_file('random.intent', self.handle_random_intent)

        if AudioService:
            self.audioservice = AudioService(self.emitter)

    def handle_request_intent(self, message):
        # play a randomly selected sound file
        self.fart_and_comment()

    def handle_fart_event(self, message):
        # create a scheduled event to fart at a random interval between 1 minute and half an hour 
        LOGGER.info("Farting skill: Handling fart event")
        if not self.random_farting:
            return
#       self.remove_event('random_fart')  # not currently working - using cancel_schedule_event() instead
        self.cancel_scheduled_event('randon_fart'+str(self.counter))
        self.counter += 1
        self.schedule_event(self.handle_fart_event, datetime.now() + timedelta(seconds=random.randrange(60, 1800)), name='random_fart'+str(self.counter))
        self.fart_and_comment()

    def handle_accuse_intent(self, message):
        # make a comment when accused of farting
        self.speak_dialog('apologise')

    def handle_random_intent(self, message):
        # initiate random farting
        LOGGER.info("Farting skill: Triggering random farting")
        self.speak("got it")
        time.sleep(.5)
        self.speak("don't worry, I'll be very discrete")
        self.random_farting = True
        self.schedule_event(self.handle_fart_event, datetime.now() + timedelta(seconds=random.randrange(30, 60)), name='random_fart'+str(self.counter))

    def fart_and_comment(self):
        # play a randomly selected fart noise and make a comment
        LOGGER.info("Farting skill: Fart and comment")
        tag = TinyTag.get(path.join(self.path_to_sound_files, random.choice(self.sound_files)))
        self.audioservice.play( path.join(self.path_to_sound_files, random.choice(self.sound_files)))
        LOGGER.info("Fart duration " + str(int(tag.duration)))
        delay = 1
        # treat the picroft platform a bit differently
        if self.platform == 'picroft':
            delay = 6
        time.sleep(int(tag.duration) + delay)
        self.speak_dialog('noise')

    @intent_handler(IntentBuilder('halt_farting').require('halt').require('farting'))
    def halt_farting(self, message):
        # stop farting
        LOGGER.info("Farting skill: Stopping")
        # if in random fart mode, cancel the scheduled event
        if self.random_farting:
            LOGGER.info("Farting skill: Stopping random farting event")
            self.speak_dialog('cancel')
            self.audioservice.stop()
            self.random_farting = False
#           self.remove_event('random_fart')  # not currently working - using cancel_schedule_event() instead
            self.cancel_scheduled_event('random_fart'+str(self.counter))

    def stop(self):
        pass

def create_skill():
    return FartingSkill()
