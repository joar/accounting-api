import sys
import logging
import threading

from datetime import datetime

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

from accounting.client import Client

_log = logging.getLogger(__name__)


class Accounting(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title='Accounting Client')

        self.client = Client()

        self.set_border_width(3)

        # Table

        self.table = Gtk.Table(3, 2, True)
        self.add(self.table)

        # Button

        self.btn_load_transactions = Gtk.Button(label='Load transactions')
        self.btn_load_transactions.connect('clicked', self.on_button_clicked)

        self.spinner = Gtk.Spinner()

        # Transaction stuff

        self.transaction_store = Gtk.ListStore(str, str)
        self.transaction_view = Gtk.TreeView(self.transaction_store)

        renderer = Gtk.CellRendererText()
        date_column = Gtk.TreeViewColumn('Date', renderer, text=0)
        payee_column = Gtk.TreeViewColumn('Payee', renderer, text=1)

        self.transaction_view.append_column(date_column)
        self.transaction_view.append_column(payee_column)

        # Layout
        self.table.attach(self.btn_load_transactions, 0, 1, 0, 1)
        self.table.attach(self.spinner, 1, 2, 0, 1)
        self.table.attach(self.transaction_view, 0, 2, 1, 3)

        # Show
        self.show_all()
        self.spinner.hide()


    def on_button_clicked(self, widget):
        def load_transactions():
            transactions = self.client.get_register()
            GLib.idle_add(self.on_transactions_loaded, transactions)

        self.spinner.show()
        self.spinner.start()

        threading.Thread(target=load_transactions).start()

    def on_transactions_loaded(self, transactions):
        self.spinner.stop()
        self.spinner.hide()
        _log.debug('transactions: %s', transactions)

        self.transaction_store.clear()

        for transaction in transactions:
            self.transaction_store.append([
                transaction.date.strftime('%Y-%m-%d'),
                transaction.payee
            ])


def main(argv=None):
    logging.basicConfig(level=logging.DEBUG)

    GObject.threads_init()

    accounting_win = Accounting()
    accounting_win.connect('delete-event', Gtk.main_quit)

    Gtk.main()

if __name__ == '__main__':
    sys.exit(main())
