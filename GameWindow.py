from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QScrollArea
from PyQt5.QtCore import Qt


class GameWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.dots = None
        self.timer = None
        self.spinner_movie = None
        self.league_games_layout = None
        self.league_games_widget = None
        self.marked_games_layout = None
        self.marked_games_area = None
        self.marked_games_widget = None
        self.spinner_label = None
        self.league_games_area = None
        self.sidebar = None
        self.loading_label = None
        self.leagues_data = {}  # To store leagues and games data
        self.marked_games_data = []  # To store marked games
        self.init_ui()

    def init_ui(self):
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

        # Sidebar for the leagues list
        self.sidebar = QTreeWidget()
        self.sidebar.setHeaderLabel("Leagues")
        content_layout.addWidget(self.sidebar, 2)  # Sidebar occupies 20% of the screen width

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

        content_layout.addLayout(central_layout, 8)  # Main content occupies 80% of the screen width
        main_layout.addLayout(content_layout)

        # Add loading text-based spinner
        self.spinner_label = QLabel(self)
        self.spinner_label.setText("Loading")
        self.spinner_label.setAlignment(Qt.AlignCenter)
        self.spinner_label.setStyleSheet("font-size: 24px; color: white;")
        self.spinner_label.setFixedSize(100, 50)  # Adjust the size
        main_layout.addWidget(self.spinner_label, alignment=Qt.AlignCenter)

        self.show()

    def update_game_data(self, basketballLeagues, marked_games):
        print("Need to be implemented update_game_data")

    def update_marked_games_ui(self, marked_games):
        """Thread-safe method to update marked games."""
        self.marked_games_data = marked_games

        # Clear the existing marked games
        for i in reversed(range(self.marked_games_layout.count())):
            widget_to_remove = self.marked_games_layout.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)

        # Populate with updated marked games
        for game in self.marked_games_data:
            game_label = QLabel(f"{game['team1']} vs {game['team2']} - Total: {game['total']}")
            game_label.setStyleSheet("font-size: 16px;")
            self.marked_games_layout.addWidget(game_label)

    def update_league_games_ui(self, leagues):
        """Thread-safe method to update league games."""
        self.leagues_data = leagues

        # Clear the existing league games
        self.sidebar.clear()

        # Populate leagues and games
        for league, games in self.leagues_data.items():
            league_item = QTreeWidgetItem([league])
            self.sidebar.addTopLevelItem(league_item)
            for game in games:
                game_item = QTreeWidgetItem([f"{game['team1']} vs {game['team2']}"])
                league_item.addChild(game_item)
