# import application packages
import os
from flask import (
    Flask, flash, render_template, redirect,
    request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)
# app configration
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
def home_page():
    hikers = list(mongo.db.users.find())
    trails = list(mongo.db.trails.find())
    return render_template("home.html", hikers=hikers, trails=trails)


# show All places in Hiking places page
@app.route("/all_trails")
def all_trails():
    trails = list(mongo.db.trails.find())
    return render_template("all_trails.html", trails=trails)


# show All places in Hiking places page
@app.route("/all_hikers")
def all_hikers():
    hikers = list(mongo.db.users.find())
    return render_template("hikers.html", hikers=hikers)


# show Hiker profile page
@app.route("/hiker_profile/<hiker_id>", methods=["GET", "POST"])
def hiker_profile(hiker_id):
    hiker = mongo.db.users.find_one({"_id": ObjectId(hiker_id)})
    return render_template("hiker_profile.html", hiker=hiker)


# show Hiker profile page for logedIn user
@app.route("/hiker_page/<name>", methods=["GET", "POST"])
def my_account(name):
    name = mongo.db.users.find_one({"name": session["name"]})["name"]
    hiker = mongo.db.users.find_one({"name": session["name"]})
    return render_template("hiker_profile.html", name=name, hiker=hiker)


# show Place page
@app.route("/trail_page/<trail_id>", methods=["GET", "POST"])
def trail_page(trail_id):
    trail = mongo.db.trails.find_one({"_id": ObjectId(trail_id)})
    return render_template("trail_page.html", trail=trail)


# sign_up Function
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # check if name / email already exists in database
        existing_name = mongo.db.users.find_one(
            {"name": request.form.get("name").lower()})
        existing_email = mongo.db.users.find_one(
            {"email": request.form.get("email")})

        if existing_name:
            flash("Sorry , Name already exists , try again")
            return render_template("thank_you.html")

        elif existing_email:
            flash("Sorry , Email already exists, try again")
            return render_template("thank_you.html")
        # check if password confirmation match
        elif request.form.get("password") != request.form.get("password2"):
            flash("Sorry , The password confirmation does not match, try again")
            return render_template("thank_you.html")

        register = {
            "name": request.form.get("name").lower(),
            "email": request.form.get("email"),
            "password": generate_password_hash(request.form.get("password")),
            # Add default profile data for new user
            "profile_name": request.form.get("name"),
            "profile_img": "https://upload.wikimedia.org/wikipedia/commons/7/7c/Profile_avatar_placeholder_large.png",
            "bio": "",
            "facebook_link": "https://www.facebook.com/",
            "instagram_link": "https://www.instagram.com/",
            "twitter_link": "https://twitter.com/",
            }
        mongo.db.users.insert_one(register)
        # put the new user into 'session' cookie
        session["name"] = request.form.get("name").lower()
        flash("Welcome, {}".format(request.form.get("name")))
        return render_template("thank_you.html")
    return render_template("thank_you.html")


# Login Function
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if email exists in db
        existing_user = mongo.db.users.find_one(
            {"email": request.form.get("login_email")})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("login_password")):
                    session["email"] = request.form.get("login_email")
                    # find a user name to dirct him to his profile
                    session["name"] = mongo.db.users.find_one({"email": session["email"]})["name"]
                    flash("Welcome, {}".format(session["name"]))
                    return render_template("thank_you.html")

            else:
                # invalid password match
                flash("Sorry, Incorrect Username and/or Password , try again")
                return render_template("thank_you.html")

        else:
            # username doesn't exist
            flash("Sorry, Incorrect Username and/or Password , try again")
            return render_template("thank_you.html")

    return render_template("thank_you.html")


@app.route("/logout")
def logout():
    # remove user from session cookie
    session.pop("name")
    flash("You have been logged out")
    return render_template("thank_you.html")


# Edit Profile Function
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    hiker = mongo.db.users.find_one({"name": session["name"]})
    name = session["name"]
    if request.method == "POST":
        profile_name = request.form.get("profile_name")
        bio = request.form.get("hiker_bio")
        facebook_link = request.form.get("facebook_link")
        instagram_link = request.form.get("instagram_link")
        twitter_link = request.form.get("twitter_link")
    # To update only edited values , code insbired from stack overflow answer https://stackoverflow.com/a/24824812/14122351
    # and refrence in mongodb https://docs.mongodb.com/manual/reference/operator/aggregation/cond/
    mongo.db.users.update_many(
        {"name": session["name"]}, [{"$set":{
            "profile_name": {"$cond": [{"$eq": [profile_name, ""]}, hiker["profile_name"], profile_name]},
            "bio": {"$cond": [{"$eq": [bio, ""]}, hiker["bio"], bio]},
            "facebook_link": {"$cond": [{"$eq": [facebook_link, ""]}, hiker["facebook_link"], facebook_link]},
            "instagram_link": {"$cond": [{"$eq": [instagram_link, ""]}, hiker["instagram_link"], instagram_link]},
            "twitter_link": {"$cond": [{"$eq": [twitter_link, ""]}, hiker["twitter_link"], twitter_link]},
        }}], upsert=True)
    return redirect(url_for("my_account", name=name))


# Add a trail to planned trails
@app.route("/planning_trail/<trail_id>", methods=["GET", "POST"])
def planning_trail(trail_id):
    if request.method == "POST":
        trail_id = mongo.db.trails.find_one({"_id": ObjectId(trail_id)})["_id"]
        newtrail = {
            "trail_id": trail_id,
            "trail_status": "planning",
            "plan_post": request.form.get("plan_post")
            }
    mongo.db.users.update({"name": session["name"]}, {"$push": {"Added_trails":
        {"trail_id": newtrail["trail_id"],
        "trail_status": newtrail["trail_status"],
        "plan_post" : newtrail["plan_post"]
        }}})
    flash("Trail Added to your plan")
    trail = mongo.db.trails.find_one({"_id": ObjectId(trail_id)})
    return render_template("trail_page.html", trail=trail)


# Add a trail to completed trails
@app.route("/completed_trail/<trail_id>", methods=["GET", "POST"])
def completed_trail(trail_id):
    if request.method == "POST":
        trail_id = mongo.db.trails.find_one({"_id": ObjectId(trail_id)})["_id"]
        newtrail = {
            "trail_id": trail_id,
            "trail_status": "completed",
            "review_header": request.form.get("review_header"),
            "review_rating": request.form.get("review_rating"),
            "review_post": request.form.get("review_post")
            }
    mongo.db.users.update({"name": session["name"]}, {"$push": {"Added_trails":
        {"trail_id": newtrail["trail_id"],
        "trail_status": newtrail["trail_status"],
        "review_header" : newtrail["review_header"],
        "review_rating" : newtrail["review_rating"],
        "review_post" : newtrail["review_post"]
        }}})
    flash("Trail Marked as Completed")
    trail = mongo.db.trails.find_one({"_id": ObjectId(trail_id)})
    return render_template("trail_page.html", trail=trail)


# make sure to debug= False before submit
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
