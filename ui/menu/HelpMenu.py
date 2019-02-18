import wx


def make_menu_bar(self):
    """
    A menu bar is composed of menus, which are composed of menu items.
    This method builds a set of menus and binds handlers to be called
    when the menu item is selected.
    """

    # Make a file menu with Hello and Exit items
    file_menu = wx.Menu()
    # The "\t..." syntax defines an accelerator key that also triggers
    # the same event
    hello_item = file_menu.Append(wx.ID_ANY, "&Hello...\tCtrl-H",
                                  "Help string shown in status bar for this menu item")
    file_menu.AppendSeparator()
    # When using a stock ID we don't need to specify the menu item's
    # label
    exit_item = file_menu.Append(wx.ID_EXIT)

    # Now a help menu for the about item
    help_menu = wx.Menu()
    about_item = help_menu.Append(wx.ID_ABOUT)

    # Make the menu bar and add the two menus to it. The '&' defines
    # that the next letter is the "mnemonic" for the menu item. On the
    # platforms that support it those letters are underlined and can be
    # triggered from the keyboard.
    menu_bar = wx.MenuBar()
    menu_bar.Append(file_menu, "&File")
    menu_bar.Append(help_menu, "&Help")

    # Give the menu bar to the frame
    self.SetMenuBar(menu_bar)

    # Finally, associate a handler function with the EVT_MENU event for
    # each of the menu items. That means that when that menu item is
    # activated then the associated handler function will be called.
    self.Bind(wx.EVT_MENU, self.on_hello, hello_item)
    self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
    self.Bind(wx.EVT_MENU, self.on_about, about_item)
