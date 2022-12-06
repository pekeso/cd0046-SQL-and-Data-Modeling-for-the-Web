#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
from datetime import datetime as dt

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  venues = Venue.query.all()
  shows = Show.query.all()

  num_upcoming_shows = 0
  map = {}
  for venue in venues:
    shows_found = Show.query.filter_by(venue_id=venue.id)
    
    num_upcoming_shows = (shows_found.filter(Show.start_time > dt.now())).count()
    city = venue.city
    state = venue.state
    venue_dict = {
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': num_upcoming_shows
    }
    key = city + ',' + state
    if key not in map: 
      map[key] = [venue_dict]
    else:
      map[key].append(venue_dict)

  for key, values in map.items():
    result = key.split(',')
    city = result[0]
    state = result[1]
    venue_data = {
      'city': city,
      'state': state,
      'venues': values
    }
    data.append(venue_data)
    

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  data = []
  search_term = request.form['search_term']
  venues = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()

  for venue in venues:
    shows_found = Show.query.filter_by(venue_id=venue.id)
    num_upcoming_shows = (shows_found.filter(Show.start_time > dt.now())).count()
    venue_dict = {
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': num_upcoming_shows
    }
    data.append(venue_dict)

  response={
    "count": len(data),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  
  past_shows_query = Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<dt.now()).all()
  upcoming_shows_query = Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>dt.now()).all()
  past_shows = []
  upcoming_shows = []
  for past_show in past_shows_query:
    artist = Artist.query.get(past_show.artist_id)
    past_shows.append({
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': str(past_show.start_time)
    })
  
  for upcoming_show in upcoming_shows_query:
    artist = Artist.query.get(upcoming_show.artist_id)
    upcoming_shows.append({
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': str(upcoming_show.start_time)
    })

  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres,
    'address': venue.address,
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data, form=VenueForm())

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()

  # Form validation
  if not form.validate_on_submit():
    flash('Please check your inputs!')
    return render_template('forms/new_venue.html', form=form) 

  name = request.form['name'] 
  city = request.form['city']
  state = request.form['state']
  address = request.form['address']
  phone = request.form['phone']
  genres = request.form.getlist('genres')
  facebook_link = request.form['facebook_link']
  image_link = request.form['image_link']
  website_link = request.form['website_link']
  seeking_talent = request.form.get('seeking_talent', False, type=bool)
  seeking_description = request.form['seeking_description']
  # TODO: insert form data as a new Venue record in the db, instead

  try:
    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres,
                facebook_link=facebook_link, image_link=image_link, website_link=website_link,
                seeking_talent=seeking_talent, seeking_description=seeking_description)
    if len(genres) > 4:
      flash('Please select up to 4 genres')
      return redirect(url_for('create_venue_form'))
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + name + ' was successfully listed!')
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + name + ' could not be listed.')
    db.session.rollback()
    abort(422)
  finally:
    db.session.close()

  # TODO: modify data to be the data object returned from db insertion

  
  
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html', form=form)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    abort(404)
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  form = ArtistForm()
  artists = Artist.query.all()
  for artist in artists:
    artist_dict = {
      'id': artist.id,
      'name': artist.name
    }
    data.append(artist_dict)

  return render_template('pages/artists.html', artists=data, form=form)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  data = []
  search_term = request.form['search_term']
  artists = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()

  for artist in artists:
    shows_found = Show.query.filter_by(artist_id=artist.id)
    num_upcoming_shows = (shows_found.filter(Show.start_time > dt.now())).count()
    artist_dict = {
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': num_upcoming_shows
    }
    data.append(artist_dict)

  response={
    "count": len(data),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  data = []
  artist = Artist.query.get(artist_id)

  past_shows_query = Show.query.join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<dt.now()).all()
  upcoming_shows_query = Show.query.join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>dt.now()).all()
  past_shows = []
  upcoming_shows = []
  for past_show in past_shows_query:
    venue = Venue.query.get(past_show.venue_id)
    past_shows.append({
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': str(past_show.start_time)
    })
  
  for upcoming_show in upcoming_shows_query:
    venue = Venue.query.get(upcoming_show.venue_id)
    upcoming_shows.append({
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': str(upcoming_show.start_time)
    })

  data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website_link,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
 
  artist = Artist.query.get(artist_id)
  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone  
  form.website_link.data = artist.website_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link

  artist = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,  
    'website': artist.website_link,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm()

  if not form.validate_on_submit():
    flash('Please check your inputs!')
    return render_template('forms/new_artist.html', form=form)

  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.address = request.form['address']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website_link = request.form['website_link']
    artist.seeking_talent = request.form.get('seeking_talent', False, type=bool)
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()

    flash('Artist ' + artist.name + ' was successfully edited!')
  except:
    db.session.rollback()
    flash('Artist ' + artist.name + ' could not be edited!')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
 
  venue = Venue.query.get(venue_id)
  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone  
  form.website_link.data = venue.website_link
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link

  venue = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres,
    'address': venue.address,
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,  
    'website': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()

  # Form validation
  if not form.validate_on_submit():
    flash('Please check your inputs!')
    return render_template('forms/new_venue.html', form=form)

  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.website_link = request.form['website_link']
    venue.seeking_talent = request.form.get('seeking_talent', False, type=bool)
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()

    flash('Venue ' + venue.name + ' was successfully edited!')
  except:
    db.session.rollback()
    flash('Venue ' + venue.name + ' could not be edited!')
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

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
  form = ArtistForm()

  if not form.validate_on_submit():
    flash('Please check your inputs!')
    return render_template('forms/new_artist.html', form=form)
  
  name = request.form['name'] 
  city = request.form['city']
  state = request.form['state']
  phone = request.form['phone']
  genres = request.form.getlist('genres')
  facebook_link = request.form['facebook_link']
  image_link = request.form['image_link']
  website_link = request.form['website_link']
  seeking_venue = request.form.get('seeking_venue', False, type=bool)
  seeking_description = request.form['seeking_description']
  try:
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres,
                facebook_link=facebook_link, image_link=image_link, website_link=website_link,
                seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + name + ' was successfully listed!')
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + name + ' could not be listed.')
    db.session.rollback()
    abort(500)
  finally:
    db.session.close()
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  shows = Show.query.all()

  for show in shows:
    # Get the first venue object
    venue = Venue.query.filter_by(id=show.venue_id).first()
    artist = Artist.query.filter_by(id=show.artist_id).first()

    # Make show dictionnary 
    show_dict = {
      'venue_id': show.venue_id,
      'venue_name': venue.name,
      'artist_id': show.artist_id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': str(show.start_time)
    }
    data.append(show_dict)

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
  form = ShowForm()

  artist_id = request.form['artist_id']
  venue_id = request.form['venue_id']
  start_time = request.form['start_time']

  try:
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
