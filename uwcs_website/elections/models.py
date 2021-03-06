from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Election(models.Model):
    date = models.DateTimeField(help_text="This is when the elections will take place")
    close_date = models.DateTimeField(help_text="This is the closing date for proxy votes")

    def __unicode__(self):
        return "Elections for %s" % self.date.year

class Position(models.Model):
    election = models.ForeignKey(Election)
    title = models.CharField(max_length=30)

    def __unicode__(self):
        return "%s for %s" % (self.title, self.election.date.year)

#class AbstractCandidate(models.Model):
    #class Meta:
        #abstract = True

#class RealCandidate(AbstractCandidate):
    #user = models.ForeignKey(User)
    #manifesto = models.TextField(blank=True)

#class FakeCandidate(AbstractCandidate):
    #name = models.CharField(max_length=30)

class Candidate(models.Model):
    position = models.ForeignKey(Position)
    user = models.ForeignKey(User)
    manifesto = models.TextField(blank=True)

    def __unicode__(self):
        return self.user.__unicode__()

class Vote(models.Model):
    candidate = models.ForeignKey(Candidate)
    preference = models.IntegerField()
    voter = models.ForeignKey(User)
