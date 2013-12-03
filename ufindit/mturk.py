from boto.mturk.connection import *
from boto.mturk.question import ExternalQuestion
from boto.mturk.qualification import Requirement, LocaleRequirement, PercentAssignmentsApprovedRequirement, Qualifications

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404


from ufindit.models import Game, Player

import settings

@staff_member_required
def publish_game_view(request, game_id, sandbox):
    """
        This view is called when we need to publish a game in Amazon MTurk
    """
    assert request.method == "GET"
    mturk = MTurkProxy(sandbox)
    mturk.submit_game(request, get_object_or_404(Game, id=game_id))
    return HttpResponseRedirect(reverse('index'))


class MTurkProxy:
    """
        This class helps to post games to Amazon MTurk
    """

    def __init__(self, sandbox):
        if sandbox == '0':
            mturk_host = settings.MTURK_REST_ENDPOINT
        else:
            mturk_host = settings.MTURK_REST_SANDBOX_ENDPOINT
        self.mturk_connection = MTurkConnection(
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            host=mturk_host)

        quals = Qualifications()
        if settings.MTURK_APPROVED_PERCENT_REQUIREMENT > 0:            
            quals.add(
                PercentAssignmentsApprovedRequirement("GreaterThanOrEqualTo",
                    settings.MTURK_APPROVED_PERCENT_REQUIREMENT))
        if settings.MTURK_USONLY_REQUIREMENT:
            quals.add( LocaleRequirement("EqualTo", "US"))
        if settings.MTURK_MASTERS_REQUIREMENT:
            quals.add(Requirement('2ARFPLSP75KLA8M8DH1HTEQVJT3SY6' if sandbox!='0' \
                else '2F1QJWKUDD8XADTFD2Q0G6UTO95ALH', "Exists"))
        self.paramdict = dict(
            hit_type=None,
            lifetime=datetime.timedelta(hours=settings.MTURK_HIT_LIFETIME_HOURS),
            max_assignments=settings.MTURK_MAX_ASSIGNMENTS,
            title = settings.MTURK_GAME_TITLE,
            description = settings.MTURK_GAME_DESCRIPTION,
            keywords = 'search',
            reward = settings.MTURK_HIT_REWARD,
            duration = datetime.timedelta(hours=settings.MTURK_HIT_DURATION),
            approval_delay = datetime.timedelta(hours=settings.MTURK_APPROVAL_DELAY),
            questions = None,
            qualifications = quals
        )

    def submit_game(self, request, game):
        self.paramdict['question'] = ExternalQuestion(
           request.build_absolute_uri(reverse('game', 
               kwargs={'game_id':game.id})), settings.MTURK_FRAME_HEIGHT)
        hit = self.mturk_connection.create_hit( **self.paramdict )[0]
        game.hitId = hit.HITId
        game.save()


class MTurkUser:
    """ Manages users that came to the game from MTurk """

    @staticmethod
    def get_mturk_user(workerId):
        try:
            player = Player.objects.get(mturk_worker_id=workerId)
        except Player.DoesNotExist:
            user = User.objects.create_user(workerId, workerId+'@mturk.com',
                workerId)
            user.save()
            player = Player(user=user, mturk_worker_id=workerId)
            player.save()
        user = authenticate(username=workerId+'@mturk.com', password=workerId)
        return user


if __name__ == "__main__":
    print 'This module contains routines to work with MTurk'
