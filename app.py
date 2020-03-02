#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dkhundley@localhost:5432/fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    website = db.Column(db.String(200))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref = 'venue', lazy = True)

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    website = db.Column(db.String(200))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref = 'artist', lazy = True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


class Show(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable = False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable = False)
    start_time = db.Column(db.DateTime, nullable = False)

    def __repr__(self):
        return f'<Show {self.id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#
@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  # Querying all locations by city-state from the Venues table
  all_locations = Venue.query.order_by(Venue.state, Venue.city).all()

  # Instantiating an emtpy object to append items that will be returned to user
  data = []

  # Looping through areas to append appropriate Venue data
  for location in all_locations:
      # Collecting venues in each city (by each state)
      venues_in_location = Venue.query.filter_by(state = location.state).filter_by(city = location.city).all()
      # Creating an empty array specifically to collect venue information
      venue_data = []
      # Looping through location venues to collect their data
      for venue in venues_in_location:
          venue_data.append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len(list(filter(lambda x: x.start_time > datetime.today(),
                                                  venue.shows)))
          })
      # Appending all necessary data to 'data' object returned to user
      data.append({
        'city': location.city,
        'state': location.state,
        'venues': venue_data
      })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # Bringing in 'search' information from web UI form
  # Special thanks to this Stack Overflow post for help: https://stackoverflow.com/questions/39384923/how-to-use-like-operator-in-sqlalchemy
  search_term = request.form.get('search_term', '')
  search_result = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()

  # Instantiating an empty object to append items that will be returned to user
  data = []

  # Looping through all search results and appending appropriate information
  for result in search_result:
      data.append({
        'id': result.id,
        'name': result.name,
        'num_upcoming_shows': len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all())
      })

  # Establishing the formal response by appending how many results were found with the results themselves
  response = {
    'count': len(search_result),
    'data': data1
  }

  return render_template('pages/search_venues.html', results = response, search_term = request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  # Querying the venue with the provided ID
  venue = Venue.query.get(venue_id)

  # Using the 'Show_Artists' method to collect information about past and upcoming shows
  past_shows = list(filter(lambda x: x.start_time < datetime.today(), venue.shows))
  upcoming_shows = list(filter(lambda x: x.start_time >= datetime.today(), venue.shows))

  past_shows = list(map(lambda x: x.show_artist(), past_shows))
  upcoming_shows = list(map(lambda x: x.show_artist(), upcoming_shows))

  # Turning data returned about the venue into a dictionary, which will be returned back to user on page
  data = venue.to_dict()

  # Appending additional information about shows to the data dictionary
  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue = data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  # Creating our venue with the Venue SQLAlchemy object with info from the UI form
  try:
      venue = Venue()
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.genres = ','.join(request.form.getlist('genres'))
      venue.facebook_link = request.form['facebook_link']
      db.session.add(venue)
      db.session.commit()
  # Rolling back data in case of error
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  # Closing session regardless of error and printing out success / error info
  finally:
      db.session.close()
      if error:
          flash('Error: Venue {} could not be listed.'.format(request.form['name']))
      else:
          flash('Venue {} was successfully listed!'.format(request.form['name']))

  return render_template('pages/home.html')



@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  error = False
  # Attempting to delete venue by provided ID
  try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
  # Rolling back changes in case of error
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  # Closing out session and printing final message
  finally:
      db.session.close()
      if error:
          flash('Error: Venue {} could not be deleted.'.format(venue.name))
      else:
          flash('Venue {} was successfully deleted.'.format(venue.name))

  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = db.session.query(Artist).all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # Getting search term from UI form
  search_term = request.form.get('search_term', '')
  # Returning all results using the search term
  search_result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()

  # Instantiating empty object to hold search result info
  data = []

  # Loopping through all search results to append proper artist information
  for result in search_result:
      data.append({
        'id': result.id,
        'name': result.name,
        'num_upcoming_shows': len(db.session.query(Show).filter(Show.artist_id == result.id).filter(Show.start_time > datetime.now()).all())
      })

  # Formalizing response with search result data object and number of results
  respose = {
    'count': len(search_result),
    'data': data
  }
  return render_template('pages/search_artists.html', results = response, search_term = request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  # Querying the artist based on the artist_id
  artist = db.session.query(Artist).get(artist_id)

  # Querying the artists past shows
  artist_past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()

  # Creating an empty container to append past show information
  past_shows = []

  # Appending previous show infomration from artist_past_shows query
  for show in artist_past_shows:
      past_shows.append({
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'artist_image_link': show.venue.image_link,
        'start_time': show.start_time
      })

  # Querying the artist's upcoming shows
  artist_upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time >= datetime.now()).all()

  # Creating an empty container to append upcoming show information
  upcoming_shows = []

  # Appending upcoming show informaiton from artist_upcoming_shows
  for show in artist_upcoming_shows:
      upcoming_shows.append({
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'artist_image_link': show.venue.image_link,
        'start_time': show.start_time
      })

  # Packaging all data about the artist to return to the user
  data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist = data)





#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # Importing information from the artist edit UI form
  form = ArtistForm()

  # Querying the artist to edit by provided artist_id
  artist = Artist.query.get(artist_id)

  if artist:
      form.name.data = artist.name
      form.genres.data = artist.genres
      form.city.data = artist.city
      form.state.data = artist.state
      form.phone.data = artist.phone
      form.website.data = artist.website
      form.facebook_link.data = artist.facebook_link
      form.seeking_venue.data = artist.seeking_venue
      form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form = form, artist = artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  error = False
  # Querying the artist information with the provided artist_id
  artist = Artist.query.get(artist_id)

  # Attempting to appropriately update artist information
  try:
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form.getlist('genres')
      artist.website = request.form['website']
      artist.facebook_link = request.form['facebook_link']
      artist.image_link = request.form['image_link']
      artist.seeking_venue = True if 'seeking_venue' in request.form else False
      artist.seeking_description = request.form['seeking_description']
      db.session.commit()
  # Handling error scenarios by rolling back info
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  # Closing the session and displaying appropriate message
  finally:
    db.session.close()
    if error:
        flash('An error occurred. Artist {} could not be updated.'.format(artist_id))
    else:
        flash('Artist {} was successfully updated!'.format(artist_id))

  return redirect(url_for('show_artist', artist_id = artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  # Getting existing venue information using venue_id
  venue = Venue.query.get(venue_id)

  # Appropriately updating venue data from form
  if venue:
      form.name.data = venue.name
      form.genres.data = venue.genres
      form.address.data = venue.address
      form.city.data = venue.city
      form.state.data = venue.state
      form.phone.data = venue.phone
      form.website.data = venue.website
      form.facebook_link.data = venue.facebook_link
      form.seeking_talent.data = venue.seeking_talent
      form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form = form, venue = venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False

  #Querying venue information based on venue_id
  venue = Venue.query.get(venue_id)

  # Attempting to update venue information
  try:
      venue.name = request.form['name']
      venue.genres = request.form.getlist('genres')
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.website = request.form['website']
      venue.facebook_link = request.form['facebook_link']
      venue.image_link = request.form['image_link']
      venue.seeking_talent = True if 'seeking_talent' in request.form else False
      venue.seeking_description = request.form['seeking_description']
      db.session.commit()
  # Handling error scenarios by implementing rollback
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  # Closing out session and showing appropriate message
  finally:
      db.session.close()
      if error:
          flash('Error: Venue {} could not be updated.'.format(venue_id))
      else:
          flash('Venue {} was successfully updated.'.format(venue_id))

  return redirect(url_for('show_venue', venue_id = venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False

  # Attempting to create artist entry with form information
  try:
      artist = Artist(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        phone = request.form['phone'],
        genres = request.form.getlist('genres'),
        website = request.form['website'],
        facebook_link = request.form['facebook_link'],
        image_link = request.form['image_link'],
        seeking_venue = True if 'seeking_venue' in request.form else False,
        seeking_description = request.form['seeking_description']
      )

      db.session.add(artist)
      db.session.commit()
  # Handling error scenarios with rollback
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  # CLosing session and showing appropriate message
  finally:
      db.session.close()
      if error:
          flash('Error: Artist {} could not be listed.'.format(request.form['name']))
      else:
          flash('Artist {} was successfully listed!'.format(request.form['name']))

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # Querying all shows
  all_shows = db.session.query(Show).join(Artist).join(Venue).all()

  # Creating an empty container to append show info to
  data = []

  # Looping through all shows to append show information appropriately
  for show in all_shows:
      data.append({
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'artist_id': show.artist_id,
        'artist_name': show.artist.name,
        'start_time': show.start_time
      })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False

  # Attempting to create show
  try:
      show = Show(
        artist_id = request.form['artist_id'],
        venue_id = request.form['venue_id'],
        start_time = request.form['start_time']
      )

      db.session.add(show)
      db.session.commit()
  # Handling error scenarios with rollback
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  # CLosing session and displaying appropriate information
  finally:
    db.session.close()
    if error:
        flash('An error occurred. Show could not be listed.')
    else:
        flash('Show was successfully listed.')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug = True)
