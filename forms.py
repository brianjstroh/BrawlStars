from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField

modes = [('bounty', 'Bounty'),
('brawlBall', 'Brawl Ball'),
('duoShowdown', 'Duo Showdown'),
('gemGrab', 'Gem Grab'),  
('heist', 'Heist'),
('hotZone', 'Hot Zone'),
('knockout', 'Knockout'),
('loneStar', 'Lone Star'),
('seige', 'Seige'),
('soloShowdown', 'Solo Showdown')]
trophy_levels = [('high','High (>=550)'), ('mid','Mid (>=300 & <550)'), ('low','Low (<300)')] 

class UserForm(FlaskForm):
    player_id = StringField('Player ID')
    game_mode = SelectField('Game Mode', choices = modes)
    map = StringField('Map')
    trophies = SelectField('Trophy Level', choices = trophy_levels)
    get_recommendation = SubmitField('Get Recommendation')
    get_all_recommendations = SubmitField('Get All Recommendations')
    get_map_weaknesses = SubmitField('Get Map Weaknesses')
    clear = SubmitField('Clear Input Fields')