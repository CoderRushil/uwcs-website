from django.contrib.syndication.feeds import Feed
from django.utils.feedgenerator import Atom1Feed
from Compsoc.comms.models import Communication
from Compsoc.events.models import Event

class LatestNews(Feed):
    title = "Latest Compsoc news items"
    link = "/"
    description = "All the updates the University of Warwick Computing Society"

    def items(self):
        return Communication.objects.filter(type='N').order_by('date')[:10]

    def item_link(self,item):
        return "/%i/" % item.id

class LatestAtomNews(LatestNews):
    feed_type = Atom1Feed
    subtitle = LatestNews.description

class NextEvents(Feed):
    title = "Next Compsoc Events"
    link = "/events/calendar/"
    description = "Next 10 events from the University of Warwick Computing Society"

    def items(self):
        return filter(lambda e: e.is_in_future(),Event.objects.order_by('-start'))[:10]

    def item_link(self,event):
        return "/events/details/%i/" % event.id

class NextAtomEvents(NextEvents):
    feed_type = Atom1Feed
    subtitle = NextEvents.description

class LatestMinutes(Feed):
    title = "Compsoc Exec Meeting Minutes"
    link = "/"
    description = "Minutes written by the secretary of the University of Warwick Computing Society"

    def items(self):
        return Communication.objects.filter(type='M').order_by('date')[:10]

    def item_link(self,item):
        return "/%i/" % item.id

class LatestAtomMinutes(LatestMinutes):
    feed_type = Atom1Feed
    subtitle = LatestMinutes.description
