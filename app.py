from flask import Flask,  jsonify, make_response 
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from models import db, User, AudioBook, Vote
from sqlalchemy import func
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
api = Api(app)


# To ensure that the tables are created before the first request.
@app.before_first_request
def create_tables():
    db.create_all()
    seed_audiobooks()

def seed_audiobooks():
    if AudioBook.query.count() == 0: 
        audiobooks = [
            {
                "title": "The Help",
                "author": "Kathryn Stockett",
                "cover_image": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1622355533i/4667024.jpg"
            },
            {
                "title": "Harry Potter and the Sorcerer's Stone",
                "author": "J.K. Rowling",
                "cover_image": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1474154022i/3.jpg"
            },
            {
                "title": "Harry Potter and the Prisoner of Azkaban",
                "author": "J.K. Rowling",
                "cover_image": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1630547330i/5.jpg"
            },
            {
                "title": "Bossypants",
                "author": "Tina Feyn mjvcx",
                "cover_image": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1481509554i/9418327.jpg"
            },
            {
                "title": "Ready Player One",
                "author": "Ernest Cline",
                "cover_image": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1500930947i/9969571.jpg"
            },
            {
                "title": "Harry Potter and the Chamber of Secrets",
                "author": "J.K. Rowling",
                "cover_image": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1474169725i/15881.jpg"
            },
            {
                "title": "The Book Thief",
                "author": "Markus Zusak",
                "cover_image": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1522157426i/19063.jpg"
            },
            {
                "title": "Harry Potter and the Deathly Hallows",
                "author": "J.K. Rowling",
                "cover_image": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1663805647i/136251.jpg"
            },
            {
                "title": "Water for Elephants",
                "author": "Sara Gruen",
                "cover_image": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1722456144i/43641.jpg"
            }
        ]
        
        for book in audiobooks:
            new_audiobook = AudioBook(
                title=book['title'],
                author=book['author'],
                cover_image=book['cover_image']
            )
            db.session.add(new_audiobook)
        db.session.commit()
        print("Audiobooks seeded successfully!")

user_resource_fields = {
	'id': fields.Integer,
	'username': fields.String
}

class UserResource(Resource):
    def get(self):
        users = User.query.all()
        return jsonify([{"id": user.id, "username": user.username} for user in users])

    def post(self):
        user_post_args = reqparse.RequestParser()
        user_post_args.add_argument("username", type=str, help="Username is required!", required=True)
        data = user_post_args.parse_args()

        result = User.query.filter_by(username=data['username']).first()
        if result: return {"success": "true", "user": {"id":result.id, "username": result.username}}

        new_user = User(username=data['username'])
        db.session.add(new_user)
        db.session.commit()
        return new_user, 201

audiobook_resource_fields = {
	'id': fields.Integer,
	'title': fields.String,
    'author': fields.String,
    'cover_image': fields.String,
    'vote_count': fields.Integer,
}

class AudioBookResource(Resource):
    def get(self):
        audiobook_post_args = reqparse.RequestParser()
        audiobook_post_args.add_argument("user_id", type=str, help="User ID is required!", required=True)
        data = audiobook_post_args.parse_args()

        audiobooks = db.session.query(
            AudioBook,
            func.count(Vote.id).label('vote_count')
        ).outerjoin(Vote, Vote.audiobook_id == AudioBook.id).group_by(AudioBook.id).all()
      
        user_voted_ids = set()
        if data["user_id"]:
            user_votes = db.session.query(Vote.audiobook_id).filter_by(user_id=data["user_id"]).all()
            user_voted_ids = {vote.audiobook_id for vote in user_votes}

        results = []
        for audiobook, vote_count in audiobooks:
            results.append({
                "id": audiobook.id,
                "title": audiobook.title,
                "author": audiobook.author,
                "cover_image": audiobook.cover_image,
                "vote_count": vote_count,
                "user_voted": audiobook.id in user_voted_ids
            })

        return make_response(jsonify(results), 200)

    @marshal_with(audiobook_resource_fields)
    def post(self):
        audiobook_post_args = reqparse.RequestParser()
        audiobook_post_args.add_argument("title", type=str, help="Title is required!", required=True)
        audiobook_post_args.add_argument("author", type=str, help="Author is required!", required=True)
        audiobook_post_args.add_argument("cover_image", type=str, help="Cover image is required!", required=True)
        data = audiobook_post_args.parse_args()
        new_audiobook = AudioBook(
            title=data['title'],
            author=data['author'],
            cover_image=data.get('cover_image')
        )
        db.session.add(new_audiobook)
        db.session.commit()
        return new_audiobook, 201

votes_resource_fields = {
	'id': fields.Integer,
	'user_id': fields.Integer,
    'audiobook_id': fields.Integer
}

class VoteResource(Resource):
    def post(self):
        votes_post_args = reqparse.RequestParser()
        votes_post_args.add_argument("user_id", type=str, help="User is required!", required=True)
        votes_post_args.add_argument("audiobook_id", type=str, help="Audiobook is required!", required=True)
        data = votes_post_args.parse_args()
        user_id = data['user_id']
        audiobook_id = data['audiobook_id']
        if not User.query.get(user_id):
            return {"message": "User not found"}, 404
        if not AudioBook.query.get(audiobook_id):
            return {"message": "Audiobook not found"}, 404
        
        vote = Vote.query.filter_by(user_id=user_id, audiobook_id=audiobook_id).first()
        if vote:
            return {"message": "User has already voted for this audiobook"}, 400

        new_vote = Vote(user_id=user_id, audiobook_id=audiobook_id)
        db.session.add(new_vote)
        db.session.commit()
        return {"message": "Vote cast successfully"}, 201

api.add_resource(UserResource, '/users')
api.add_resource(AudioBookResource, '/audiobooks')
api.add_resource(VoteResource, '/votes')

if __name__ == '__main__':
    app.run(debug=True)