"""
top-like command for monitoring Sentry events.

Heavily inspired by the celery cursesmon:

https://github.com/celery/celery/blob/master/celery/events/cursesmon.py
"""

import curses
import sentry
import threading

from itertools import count
from optparse import make_option
from time import sleep

from django.core.management.base import BaseCommand

BORDER_SPACING = 4
LEFT_BORDER_OFFSET = 3
COUNT_LENGTH = 10
PROJECT_LENGTH = 62


def abbr(S, max, ellipsis='...'):
    if S is None:
        return '???'
    if len(S) > max:
        return ellipsis and (S[:max - len(ellipsis)] + ellipsis) or S[:max]
    return S


class CursesMonitor(object):  # pragma: no cover
    keymap = {}
    win = None
    screen_width = None
    screen_delay = 10
    selected_task = None
    selected_position = 0
    selected_str = 'Selected: '
    foreground = curses.COLOR_WHITE
    background = curses.COLOR_BLACK
    online_str = 'Events: '
    help_title = 'Keys: '
    help = ('^c: quit')
    greet = ' Sentry %s ' % sentry.VERSION
    info_str = 'Info: '

    keyalias = {
        # curses.KEY_DOWN: 'J',
        # curses.KEY_UP: 'K',
        # curses.KEY_ENTER: 'I'
    }

    def __init__(self, results, keymap=None):
        self.keymap = keymap or self.keymap
        self.results = results
        default_keymap = {
            # 'J': self.move_selection_down,
            # 'K': self.move_selection_up,
            # 'C': self.revoke_selection,
            # 'T': self.selection_traceback,
            # 'R': self.selection_result,
            # 'I': self.selection_info,
            # 'L': self.selection_rate_limit
        }
        self.keymap = dict(default_keymap, **self.keymap)

    def format_row(self, project, num_events):
        mx = self.display_width

        project = abbr(project, PROJECT_LENGTH).ljust(PROJECT_LENGTH)
        num_events = abbr(str(num_events), COUNT_LENGTH).ljust(COUNT_LENGTH)

        row = '%s %s ' % (project, num_events)
        if self.screen_width is None:
            self.screen_width = len(row[:mx])
        return row[:mx]

    @property
    def screen_width(self):
        _, mx = self.win.getmaxyx()
        return mx

    @property
    def screen_height(self):
        my, _ = self.win.getmaxyx()
        return my

    @property
    def display_width(self):
        _, mx = self.win.getmaxyx()
        return mx - BORDER_SPACING

    @property
    def display_height(self):
        my, _ = self.win.getmaxyx()
        return my - 7

    @property
    def limit(self):
        return self.display_height

    def handle_keypress(self):
        try:
            key = self.win.getkey().upper()
        except:
            return
        key = self.keyalias.get(key) or key
        handler = self.keymap.get(key)
        if handler is not None:
            handler()

    def alert(self, callback, title=None):
        self.win.erase()
        my, mx = self.win.getmaxyx()
        y = blank_line = count(2).next
        if title:
            self.win.addstr(y(), 3, title, curses.A_BOLD | curses.A_UNDERLINE)
            blank_line()
        callback(my, mx, y())
        self.win.addstr(my - 1, 0, 'Press any key to continue...',
                        curses.A_BOLD)
        self.win.refresh()
        while 1:
            try:
                return self.win.getkey().upper()
            except:
                pass

    def readline(self, x, y):
        buffer = str()
        curses.echo()
        try:
            i = 0
            while 1:
                ch = self.win.getch(x, y + i)
                if ch != -1:
                    if ch in (10, curses.KEY_ENTER):            # enter
                        break
                    if ch in (27, ):
                        buffer = str()
                        break
                    buffer += chr(ch)
                    i += 1
        finally:
            curses.noecho()
        return buffer

    def display_result_row(self, lineno, project, num_events):
        attr = curses.A_NORMAL

        name = '%s / %s' % (project.team.slug, project.slug)

        line = self.format_row(name, num_events)
        self.win.addstr(lineno, LEFT_BORDER_OFFSET, line, attr)

    def draw(self):
        win = self.win
        self.handle_keypress()
        x = LEFT_BORDER_OFFSET
        y = blank_line = count(1).next
        my, mx = win.getmaxyx()
        win.erase()
        win.bkgd(' ', curses.color_pair(1))
        win.border()
        win.addstr(0, x - 1, self.greet, curses.A_DIM | curses.color_pair(2))
        blank_line()
        win.addstr(y(), x, self.format_row('PROJECT', '# EVENTS'),
                   curses.A_BOLD | curses.A_UNDERLINE)
        results = self.results
        if results:
            for row, (project, num_events) in enumerate(results):
                if row > self.display_height:
                    break

                lineno = y()
                self.display_result_row(lineno, project, num_events)

        # -- Footer
        blank_line()
        win.hline(my - 3, x, curses.ACS_HLINE, self.screen_width - 4)

        # # Info
        # win.addstr(my - 3, x, self.info_str, curses.A_BOLD)
        # win.addstr(
        #     my - 3, x + len(self.info_str),
        #     'events:%s tasks:%s workers:%s/%s' % (
        #         self.state.event_count, self.state.task_count,
        #         len([w for w in self.state.workers.values()
        #              if w.alive]),
        #         len(self.state.workers)),
        #     curses.A_DIM,
        # )

        # Help
        self.safe_add_str(my - 2, x, self.help_title, curses.A_BOLD)
        self.safe_add_str(my - 2, x + len(self.help_title), self.help,
                          curses.A_DIM)
        win.refresh()

    def safe_add_str(self, y, x, string, *args, **kwargs):
        if x + len(string) > self.screen_width:
            string = string[:self.screen_width - x]
        self.win.addstr(y, x, string, *args, **kwargs)

    def init_screen(self):
        self.win = curses.initscr()
        self.win.nodelay(True)
        self.win.keypad(True)
        curses.start_color()
        curses.init_pair(1, self.foreground, self.background)
        # greeting
        curses.init_pair(2, curses.COLOR_CYAN, self.background)

        curses.cbreak()

    def resetscreen(self):
        curses.nocbreak()
        self.win.keypad(False)
        curses.echo()
        curses.endwin()

    def nap(self):
        curses.napms(self.screen_delay)


class DisplayThread(threading.Thread):  # pragma: no cover

    def __init__(self, display):
        self.display = display
        self.shutdown = False
        threading.Thread.__init__(self)

    def run(self):
        while not self.shutdown:
            self.display.draw()
            self.display.nap()


class Command(BaseCommand):
    help = 'Reports the most active projects ala `top`.'

    option_list = BaseCommand.option_list + (
        make_option('--minutes', default='15', type=int, help='Number of minutes to check.'),
        make_option('--tick', default='5', type=int, help='Number of seconds in between updates.'),
    )

    def handle(self, **options):
        from sentry.plugins import plugins

        plugin = plugins.get('top')

        display = CursesMonitor([])
        display.init_screen()

        refresher = DisplayThread(display)
        refresher.start()
        try:
            while True:
                # TODO: should probably lock this
                display.results = plugin.top_projects()
                sleep(options['tick'])
        except (KeyboardInterrupt, SystemExit):
            refresher.shutdown = True
            refresher.join()
            display.resetscreen()
