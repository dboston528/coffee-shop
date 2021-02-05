import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES
@app.route('/drinks')
def get_drinks():
    drink_list = Drink.query.all()
    if drink_list is None:
        abort(404)
    drinks = [drink.short() for drink in drink_list]
    return jsonify({
        "success": True,
        "drinks": drinks
    }), 200


@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def get_drinks_detail(payload):
    try:
        drinks_details = Drink.query.order_by(Drink.id).all()
        drinks = [drink.long() for drink in drinks_details]
        if len(drinks) == 0:
            abort(404)
        return jsonify({"success": True, "drinks": drinks})
    except Exception as e:
        print(e)
        abort(422)

@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def add_drinks(payload):
    body = request.get_json()
    new_title = request.json.get("title")
    new_recipe = request.json.get("recipe")
    try:
        new_drink = Drink(title=new_title, recipe=json.dumps(new_recipe))
        new_drink.insert()
        return jsonify({"success": True, "drinks": new_drink.long()}), 200
    except Exception as e:
        print(e)
        abort(404)

@app.route("/drinks/<int:id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def edit_drinks(jwt, id):
    body = request.get_json()
    title = body.get("title")
    recipe = body.get("recipe")
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink == None:
            abort(404)
        drink.title = title
        drink.recipe = json.dumps(recipe)
        drink.update()
        return jsonify({
            "success": True, 
            "drinks": drink.long()
            }), 200
    except Exception as e:
        print(e)
        abort(422)

@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drinks(jwt, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink == None:
            abort(404)
        drink.delete()
        return jsonify({"success": True, "delete": id}), 200
    except Exception as e:
        print(e)
        abort(422)

## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "The resource you requested was not found."
    }), 404



@app.errorhandler(AuthError)
def handle_auth0_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), 401
