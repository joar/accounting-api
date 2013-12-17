import sys
import logging
import threading
import pkg_resources

from functools import wraps
from datetime import datetime

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

from accounting.client import Client

_log = logging.getLogger(__name__)


def indicate_activity(func_or_str):
    description = None

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kw):
            self.activity_description.set_text(description)
            self.activity_indicator.show()
            self.activity_indicator.start()

            return func(self, *args, **kw)

        return wrapper

    if callable(func_or_str):
        description = 'Working'
        return decorator(func_or_str)
    else:
        description = func_or_str
        return decorator


def indicate_activity_done(func):
    @wraps(func)
    def wrapper(self, *args, **kw):
        self.activity_description.set_text('')
        self.activity_indicator.stop()
        self.activity_indicator.hide()

        return func(self, *args, **kw)

    return wrapper


class AccountingApplication:
    def __init__(self):
        #Gtk.Window.__init__(self, title='Accounting Client')

        self.client = Client()

        self.load_ui(pkg_resources.resource_filename(
            'accounting', 'res/client-ui.glade'))

        self.about_dialog.set_transient_for(self.accounting_window)

        self.accounting_window.connect('delete-event', Gtk.main_quit)
        self.accounting_window.set_border_width(0)
        self.accounting_window.set_default_geometry(640, 360)

        self.accounting_window.show_all()
        self.transaction_detail.hide()

    def load_ui(self, path):
        _log.debug('Loading UI...')
        builder = Gtk.Builder()
        builder.add_from_file(path)
        builder.connect_signals(self)

        for element in builder.get_objects():
            try:
                setattr(self, Gtk.Buildable.get_name(element), element)
                _log.debug('Loaded %s', Gtk.Buildable.get_name(element))
            except TypeError as exc:
                _log.error('%s could not be loaded: %s', element, exc)

        _log.debug('UI loaded')

    def on_transaction_view_cursor_changed(self, widget):
        selection = self.transaction_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        xact_store, xact_iter = selection.get_selected()

        xact_id = xact_store.get_value(xact_iter, 0)
        _log.debug('selection: %s', xact_id)

        for transaction in self.transaction_data:
            if transaction.id == xact_id:
                self.transaction_header.set_text(transaction.payee)

                self.posting_store.clear()

                for posting in transaction.postings:
                    self.posting_store.append([
                        posting.account,
                        str(posting.amount.amount),
                        posting.amount.symbol
                    ])

                self.transaction_detail.show()
                break

    def on_show_about_activate(self, widget):
        _log.debug('Showing About')
        self.about_dialog.show_all()

    def on_about_dialog_response(self, widget, response_type):
        _log.debug('Closing About')
        if response_type == Gtk.ResponseType.CANCEL:
            self.about_dialog.hide()
        else:
            _log.error('Unexpected response_type: %d', response_type)

    @indicate_activity('Refreshing Transactions')
    def on_transaction_refresh_activate(self, widget):
        def load_transactions():
            transactions = self.client.get_register()
            GLib.idle_add(self.on_transactions_loaded, transactions)

        threading.Thread(target=load_transactions).start()

    @indicate_activity_done
    def on_transactions_loaded(self, transactions):
        _log.debug('transactions: %s', transactions)

        self.transaction_data = transactions
        self.transaction_store.clear()

        for transaction in transactions:
            self.transaction_store.append([
                transaction.id,
                transaction.date.strftime('%Y-%m-%d'),
                transaction.payee
            ])


def main(argv=None):
    logging.basicConfig(level=logging.DEBUG)

    GObject.threads_init()

    accounting = AccountingApplication()

    Gtk.main()

if __name__ == '__main__':
    sys.exit(main())
