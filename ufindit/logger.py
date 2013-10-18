from ufindit.models import Event, PlayerTask, Serp

class EventLogger:
    '''
        This class logs different types of events to the database table.
    '''

    def __init__(self, task):
        assert isinstance(task, PlayerTask)
        self.task = task

    @staticmethod
    def query(player_task, query, serpid):
        assert isinstance(player_task, PlayerTask)
        Event(player_task=player_task, event='Q', query=query,
            serp=Serp.objects.get(id=serpid)).save()

    @staticmethod
    def click(player_task, url):
        assert isinstance(player_task, PlayerTask)
        Event(player_task=player_task, event='C', url=url).save()

    @staticmethod
    def emu_log_event(player_task, url):
        assert isinstance(player_task, PlayerTask)
        Event(player_task=player_task, event='EMU', url=url).save()

    @staticmethod
    def emu_save_page(player_task, data):
        assert isinstance(player_task, PlayerTask)
        Event(player_task=player_task, event='EMU_PAGE', extra_data=data).save()


if __name__ == "__main__":
    print "Event logger for uFindIt game"