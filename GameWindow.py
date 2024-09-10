import sys

from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QScrollArea
from PyQt5.QtCore import Qt


class GameWindow(QWidget):
    def __init__(self, logger):
        super().__init__()

        self.league_games_layout = None
        self.league_games_widget = None
        self.marked_games_layout = None
        self.marked_games_area = None
        self.marked_games_widget = None
        self.sidebar = None
        self.spinner_label = None
        self.league_games_area = None
        self.leagues_data = {}  # To store leagues and games data
        self.marked_games_data = []  # To store marked games
        self.selected_league = None  # To track selected league
        self.logger = logger
        self.init_ui()

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

            # Sidebar for the leagues list with 30% more space
            self.sidebar = QTreeWidget()
            self.sidebar.setHeaderLabel("Leagues")
            self.sidebar.setStyleSheet("text-align: right;")  # RTL text direction
            self.sidebar.itemClicked.connect(self.on_league_selected)
            content_layout.addWidget(self.sidebar, 3)  # Sidebar occupies 26% of the screen width

            # Central layout for main content
            central_layout = QVBoxLayout()

            # Scrollable area for marked games
            marked_games_label = QLabel("Marked Games", self)
            marked_games_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            central_layout.addWidget(marked_games_label)

            self.marked_games_area = QScrollArea()
            self.marked_games_area.setWidgetResizable(True)
            self.marked_games_widget = QWidget()
            self.marked_games_layout = QVBoxLayout(self.marked_games_widget)
            self.marked_games_area.setWidget(self.marked_games_widget)

            central_layout.addWidget(self.marked_games_area, 3)  # 30% of remaining space

            # Scrollable area for expanded league games
            league_games_label = QLabel("League Games", self)
            league_games_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            central_layout.addWidget(league_games_label)

            self.league_games_area = QScrollArea()
            self.league_games_area.setWidgetResizable(True)
            self.league_games_widget = QWidget()
            self.league_games_layout = QVBoxLayout(self.league_games_widget)
            self.league_games_area.setWidget(self.league_games_widget)

            central_layout.addWidget(self.league_games_area, 7)  # Remaining 70% for league games

            content_layout.addLayout(central_layout, 7)  # Main content occupies 74% of the screen width
            main_layout.addLayout(content_layout)

            self.show()
            self.logger.info('Main game window initialized successfully!')
        except Exception as e:
            self.logger.error(f'Failed to ini game window ui on init_ui. Error : ${str(e)}')
            sys.exit(1)

    def update_game_data(self, basketballLeagues, marked_games):
        """Updates both leagues and marked games"""
        self.update_league_games_ui(basketballLeagues, marked_games)
        self.update_marked_games_ui(marked_games)

    def update_marked_games_ui(self, marked_games):
        """Thread-safe method to update marked games."""
        self.marked_games_data = marked_games

        # Clear the existing marked games
        for i in reversed(range(self.marked_games_layout.count())):
            widget_to_remove = self.marked_games_layout.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)

        # Populate marked games only if a league is selected
        if self.selected_league:
            for game in self.marked_games_data:
                if game['league'] == self.selected_league:
                    game_label = QLabel(f"{game['team1']} vs {game['team2']} - Total: {game['total']}")
                    game_label.setStyleSheet("font-size: 16px; background-color: green; color: white;")
                    self.marked_games_layout.addWidget(game_label)

    def update_league_games_ui(self, leagues, marked_games):
        """Thread-safe method to update league games."""
        self.leagues_data = leagues

        # Clear the existing league games and sidebar
        self.sidebar.clear()
        for i in reversed(range(self.league_games_layout.count())):
            widget_to_remove = self.league_games_layout.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)

        # Populate leagues in the sidebar
        for league, games in self.leagues_data.items():
            league_item = QTreeWidgetItem([league])

            # Highlight leagues with marked games
            if any(game['league'] == league for game in marked_games):
                league_item.setBackground(0, Qt.green)

            self.sidebar.addTopLevelItem(league_item)

        # Update league games for selected league
        if self.selected_league:
            if self.selected_league in self.leagues_data:
                for game in self.leagues_data[self.selected_league]:
                    game_text = f"{game['team1']} vs {game['team2']} - Quarter: {game['quarter']} - Score: {game['team1_score']} - {game['team2_score']}"
                    game_label = QLabel(game_text)

                    # Highlight games also marked in marked_games
                    if any(g['team1'] == game['team1'] and g['team2'] == game['team2'] for g in marked_games):
                        game_label.setStyleSheet("font-size: 16px; background-color: green; color: white;")
                    else:
                        game_label.setStyleSheet("font-size: 16px;")

                    self.league_games_layout.addWidget(game_label)

    def on_league_selected(self, item, column):
        """Handle league selection and update games display"""
        self.selected_league = item.text(0)

        # Mark the selected league with a black border (simulated with background and text color),
        # green background, and bold text
        for i in range(self.sidebar.topLevelItemCount()):
            league_item = self.sidebar.topLevelItem(i)

            if league_item.text(0) == self.selected_league:
                # Set the selected league with green background and bold text
                league_item.setBackground(0, QColor("green"))
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
