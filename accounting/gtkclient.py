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

        self.set_border_width(0)

        self.set_default_geometry(640, 360)

        # Controls

        self.btn_load_transactions = Gtk.Button(label='Load transactions')
        self.btn_load_transactions.connect('clicked', self.on_button_clicked)

        self.spinner = Gtk.Spinner()

        renderer = Gtk.CellRendererText()

        # Transaction stuff

        self.transaction_data = None
        self.transaction_store = Gtk.ListStore(str, str, str)
        self.transaction_view = Gtk.TreeView(self.transaction_store)

        self.id_column = Gtk.TreeViewColumn('ID', renderer, text=0)
        self.date_column = Gtk.TreeViewColumn('Date', renderer, text=1)
        self.payee_column = Gtk.TreeViewColumn('Payee', renderer, text=2)

        self.transaction_view.append_column(self.date_column)
        self.transaction_view.append_column(self.payee_column)

        self.transaction_view.connect('cursor-changed',
                                      self.on_transaction_selected)

        # Postings

        self.posting_store = Gtk.ListStore(str, str, str)
        self.posting_view = Gtk.TreeView(self.posting_store)

        self.account_column = Gtk.TreeViewColumn('Account', renderer, text=0)
        self.amount_column = Gtk.TreeViewColumn('Amount', renderer, text=1)
        self.symbol_column = Gtk.TreeViewColumn('Symbol', renderer, text=2)

        self.posting_view.append_column(self.account_column)
        self.posting_view.append_column(self.amount_column)
        self.posting_view.append_column(self.symbol_column)

        # The transaction detail view

        self.lbl_payee = Gtk.Label()

        # Layout setting
        self.menu = Gtk.MenuBar.new()

        self.ctrl_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        self.ctrl_box.pack_start(self.btn_load_transactions, False, False, 0)
        self.ctrl_box.pack_start(self.spinner, False, False, 5)

        self.detail_view = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.detail_view.pack_start(self.lbl_payee, False, True, 0)
        self.detail_view.pack_start(self.posting_view, True, True, 0)

        self.vertical = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.vertical.pack_start(self.ctrl_box, False, True, 0)
        self.vertical.pack_start(self.transaction_view, True, True, 0)

        self.paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        self.add(self.paned)

        self.paned.add1(self.vertical)
        self.paned.add2(self.detail_view)

        # Show

        self.show_all()
        self.spinner.hide()
        self.detail_view.hide()

    def on_transaction_selected(self, widget):
        selection = self.transaction_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        xact_store, xact_iter = selection.get_selected()

        xact_id = xact_store.get_value(xact_iter, 0)
        _log.debug('selection: %s', xact_id)

        for transaction in self.transaction_data:
            if transaction.id == xact_id:
                self.lbl_payee.set_text(transaction.payee)

                self.posting_store.clear()

                for posting in transaction.postings:
                    self.posting_store.append([
                        posting.account,
                        str(posting.amount.amount),
                        posting.amount.symbol
                    ])

                self.detail_view.show()
                break

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

    accounting_win = Accounting()
    accounting_win.connect('delete-event', Gtk.main_quit)

    Gtk.main()

if __name__ == '__main__':
    sys.exit(main())
