from flask import Flask, request, redirect, url_for
import flask
from hai_server import app

@app.route('/')
def show_uploader():
  return flask.render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    the_file = request.files['image']
    the_file.save("./hai_server/images/" + "hoge.png")
    return ""

