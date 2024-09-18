import sys
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QScrollArea, \
    QTableWidget, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QEventLoop, QTimer


class GameWindow(QWidget):
    window_closed = pyqtSignal()

    def __init__(self, logger, elements, translation):
        super().__init__()
        self.translation = translation
        self.league_games_layout = None
        self.league_games_widget = None
        self.marked_games_layout = None
        self.marked_games_area = None
        self.marked_games_widget = None
        self.sidebar = None
        self.spinner_label = None
        self.league_games_area = None
        self.leagues_data = {}  # To store leagues and games data
        self.marked_games_data = {}  # To store marked games
        self.selected_league = None  # To track selected league
        self.logger = logger

        # Placeholder labels for "No Data" messages
        self.no_marked_games_label = QLabel("No marked games available", self)
        self.no_league_games_label = QLabel("No league games available", self)

        self.init_ui()
        self.elements = elements

    def close_windows(self):
        self.close()

    def closeEvent(self, event):
        # Display a confirmation dialog
        reply = QMessageBox.question(self, self.translation['Exit Confirmation'],
                                     self.translation["Are you sure you want to quit?"],
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Emit the window_closed signal first to trigger stopping of the PlayManager
                self.logger.info("Emitting window_closed signal to stop PlayManager...")
                self.window_closed.emit()
                self.logger.info("Background tasks completed, closing window...")
                event.accept()  # Accept the event, so the window closes
            except Exception as e:
                self.logger.error(f"Failed to stop the program...Error: {str(e)}")
                sys.exit(1)
        else:
            event.ignore()

    def init_ui(self):
        try:
            self.logger.info('Initializing Main game window...')
            self.setWindowTitle("Sport Scrapper - Game Window")
            self.setGeometry(100, 100, 1200, 800)

            # Main layout for the whole window
            main_layout = QVBoxLayout(self)

            # Header section
            header_label = QLabel("Sport Scrapper", self)
            header_label.setStyleSheet("font-size: 32px; font-weight: bold; text-align: center;")
            header_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(header_label)

            # Create a horizontal layout to separate sidebar and main content
            content_layout = QHBoxLayout()

            # Sidebar layout with its own vertical layout
            sidebar_layout = QVBoxLayout()  # New layout for the sidebar section

            # Add leagues label above the sidebar to match the style of other headers
            leagues_label = QLabel(self.translation["Leagues"], self)
            leagues_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            leagues_label.setAlignment(Qt.AlignCenter)  # Align the label to the center

            # Sidebar for the leagues list
            self.sidebar = QTreeWidget()
            self.sidebar.setHeaderLabel("")
            self.sidebar.setStyleSheet("font-size: 12px; font-weight: bold;")
            self.sidebar.itemClicked.connect(self.on_league_selected)

            # Add the label and sidebar to the sidebar layout
            sidebar_layout.addWidget(leagues_label)
            sidebar_layout.addWidget(self.sidebar)

            # Add sidebar layout to the content layout
            content_layout.addLayout(sidebar_layout, 2)  # Sidebar occupies 26% of the screen width

            # Central layout for main content
            central_layout = QVBoxLayout()

            # Scrollable area for marked games
            marked_games_label = QLabel(self.translation["Marked Games"], self)
            marked_games_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            central_layout.addWidget(marked_games_label)

            self.marked_games_area = QScrollArea()
            self.marked_games_area.setWidgetResizable(True)
            self.marked_games_widget = QWidget()
            self.marked_games_layout = QVBoxLayout(self.marked_games_widget)
            self.marked_games_area.setWidget(self.marked_games_widget)

            central_layout.addWidget(self.marked_games_area, 4)  # 30% of remaining space

            # Add "No Data" label for marked games
            self.no_marked_games_label.setStyleSheet("font-size: 18px; color: gray;")
            self.no_marked_games_label.setAlignment(Qt.AlignCenter)
            central_layout.addWidget(self.no_marked_games_label)
            self.no_marked_games_label.hide()

            # Scrollable area for expanded league games
            league_games_label = QLabel(self.translation["League Games"], self)
            league_games_label.setStyleSheet("font-size: 20px; font-weight: bold; text-align: center;")
            central_layout.addWidget(league_games_label)

            self.league_games_area = QScrollArea()
            self.league_games_area.setWidgetResizable(True)
            self.league_games_widget = QWidget()
            self.league_games_layout = QVBoxLayout(self.league_games_widget)
            self.league_games_area.setWidget(self.league_games_widget)

            central_layout.addWidget(self.league_games_area, 7)  # Remaining 70% for league games

            # Add "No Data" label for league games
            self.no_league_games_label.setStyleSheet("font-size: 18px; color: gray;")
            self.no_league_games_label.setAlignment(Qt.AlignCenter)
            central_layout.addWidget(self.no_league_games_label)
            self.no_league_games_label.hide()

            # Add central layout to content layout
            content_layout.addLayout(central_layout, 7)  # Main content occupies 74% of the screen width

            # Add content layout to main layout
            main_layout.addLayout(content_layout)

            self.show()
            self.logger.info('Main game window initialized successfully!')
        except Exception as e:
            self.logger.error(f'Failed to initialize game window UI on init_ui. Error: {str(e)}')
            sys.exit(1)

    @pyqtSlot(dict, dict)
    def update_game_data(self, basketballLeagues, marked_games):
        """Updates both leagues and marked games safely."""
        try:
            self.logger.info("Updating game data in UI thread...")
            self.update_league_games_ui(basketballLeagues, marked_games)
            self.update_marked_games_ui(marked_games)
        except Exception as e:
            self.logger.error(f'Received an error during update_game_data operation. Error: ${str(e)}')

    def update_translation(self, translation_new):
        self.translation = translation_new

    def update_marked_games_ui(self, marked_games):
        """Thread-safe method to update marked games."""
        try:
            self.logger.info("Updating marked games UI in UI thread...")
            self.marked_games_data = marked_games

            # Clear the existing marked games table
            for i in reversed(range(self.marked_games_layout.count())):
                widget_to_remove = self.marked_games_layout.itemAt(i).widget()
                if widget_to_remove is not None:
                    widget_to_remove.setParent(None)

            # Populate marked games as a table only if a league is selected
            if self.selected_league:
                if self.marked_games_data:
                    self.no_marked_games_label.hide()
                    game_table = QTableWidget()

                    # Setting the columns
                    columns = [self.translation['Game'], self.translation['League'],
                               self.translation['Current Score'], self.translation['First Guessed Score'],
                               self.translation['Selected Row Number'],
                               self.translation['Selected Row total Score'],
                               self.translation['Selected Row Under Score'],
                               self.translation['Selected Row Over Score']]
                    game_table.setColumnCount(len(columns))  # Set columns based on keys
                    game_table.setHorizontalHeaderLabels(columns)
                    # Populate the table with the marked games
                    for row_index, (game_key, game_data) in enumerate(self.marked_games_data.items()):
                        if game_data[self.elements['consts']['league_name']] == self.selected_league:
                            game_name = str(game_key)
                            league_name = str(game_data[self.elements['consts']['league_name']])
                            curr_league = self.leagues_data[league_name]
                            curr_game = curr_league[game_key]
                            selected_row = game_data[self.elements['consts']['selected_row']]
                            current_score = str(curr_game[self.elements['consts']['total_score']])
                            first_total = str(curr_game[self.elements['consts']['first_total_score']])
                            selected_row_index = str(selected_row[self.elements['consts']['curr_row_index']])
                            selected_row_total = str(selected_row[self.elements['consts']['total_text_value']])
                            selected_row_under = str(selected_row[self.elements['consts']['under_text_value']])
                            selected_row_over = str(selected_row[self.elements['consts']['over_text_value']])
                            game_table.insertRow(row_index)
                            game_table.setItem(row_index, 0, QTableWidgetItem(game_name))
                            game_table.setItem(row_index, 1, QTableWidgetItem(league_name))
                            game_table.setItem(row_index, 2, QTableWidgetItem(current_score))
                            game_table.setItem(row_index, 3, QTableWidgetItem(first_total))
                            game_table.setItem(row_index, 4, QTableWidgetItem(selected_row_index))
                            game_table.setItem(row_index, 5, QTableWidgetItem(selected_row_total))
                            game_table.setItem(row_index, 6, QTableWidgetItem(selected_row_under))
                            game_table.setItem(row_index, 7, QTableWidgetItem(selected_row_over))

                    self.marked_games_layout.addWidget(game_table)

                else:
                    # Show the "No Data" message
                    self.no_marked_games_label.show()

                # Make sure the layout is set
                self.marked_games_widget.setLayout(self.marked_games_layout)
        except Exception as e:
            self.logger.error(
                f'Failed to update marked games UI for league {self.selected_league} in update_marked_games_ui. Error: {e}')

    def update_league_games_ui(self, leagues, marked_games):
        """Thread-safe method to update league games."""
        try:
            self.leagues_data = leagues

            # Clear the existing league games and sidebar
            self.sidebar.clear()
            for i in reversed(range(self.league_games_layout.count())):
                widget_to_remove = self.league_games_layout.itemAt(i).widget()
                if widget_to_remove is not None:
                    widget_to_remove.setParent(None)

            # Populate leagues in the sidebar
            if leagues:
                self.no_league_games_label.hide()
                for league, games in self.leagues_data.items():
                    league_item = QTreeWidgetItem([league])

                    # Highlight leagues with marked games
                    if any(game_mark_data[self.elements['consts']['league_name']] == league for
                           (game_key, game_mark_data)
                           in marked_games.items()):
                        league_item.setBackground(0, Qt.green)

                    self.sidebar.addTopLevelItem(league_item)

                # Display games for the selected league as a table
                if self.selected_league and self.selected_league in self.leagues_data:
                    games = self.leagues_data[self.selected_league]
                    if games:
                        game_table = QTableWidget()

                        # Set columns based on the first game's data structure (dynamically set columns based on keys)
                        first_game = next(iter(games.values()))  # Get first game's data
                        game_table.setColumnCount(len(first_game.keys()))
                        columns = first_game.keys()
                        translated_columns = [self.translation[column] for column in columns]
                        game_table.setHorizontalHeaderLabels(translated_columns)

                        # Populate rows with game data
                        for row_index, (game_key, game_data) in enumerate(games.items()):
                            game_table.insertRow(row_index)
                            for col_index, (key, value) in enumerate(game_data.items()):
                                game_table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

                        # Handle marked games data by highlighting rows
                        for game_key, game_info in marked_games.items():
                            if game_info[self.elements['consts']['league_name']] == self.selected_league:
                                for row_index, (key, _) in enumerate(games.items()):
                                    if key == game_key:
                                        for col_index in range(game_table.columnCount()):
                                            game_table.item(row_index, col_index).setBackground(
                                                Qt.yellow)  # Highlight row

                        self.league_games_layout.addWidget(game_table)

            else:
                # Show the "No Data" message
                self.no_league_games_label.show()

            # Set the layout
            self.league_games_widget.setLayout(self.league_games_layout)

        except Exception as e:
            self.logger.error(
                f'Failed to update view for selected league {self.selected_league} in update_league_games_ui. Error: {e}')

    def on_league_selected(self, item):
        """Handle league selection and update games display"""
        try:
            self.selected_league = item.text(0)

            if self.selected_league:
                # Mark the selected league with green background, and bold text
                for i in range(self.sidebar.topLevelItemCount()):
                    league_item = self.sidebar.topLevelItem(i)

                    if league_item.text(0) == self.selected_league:
                        # Set the selected league with green background and bold text
                        league_item.setBackground(0, QColor(0, 50, 50))  # Dark green with RGB(0, 100, 0)
                        league_item.setForeground(0, QColor("white"))
                        font = league_item.font(0)
                        font.setBold(True)
                        league_item.setFont(0, font)
                    else:
                        # Reset the other league items to default
                        league_item.setBackground(0, QColor("transparent"))
                        league_item.setForeground(0, QColor("black"))
                        font = league_item.font(0)
                        font.setBold(False)
                        league_item.setFont(0, font)

                # Update the league games and marked games based on the selected league
                self.update_league_games_ui(self.leagues_data, self.marked_games_data)
                self.update_marked_games_ui(self.marked_games_data)
        except Exception as e:
            self.logger.error(
                f'Failed to update view for selected league {self.selected_league} in on_league_selected. Error: {e}')
