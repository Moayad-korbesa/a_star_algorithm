# imports
from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import heapq

# App Setup
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False

db = SQLAlchemy(app)


# Node Class for A* nodes
class Node:
    def __init__(self, path, g, h):
        self.path = path
        self.g = g
        self.h = h
        self.f = g + h

    def __lt__(self, other):
        return self.f < other.f


def a_star_algorithm(distance_matrix, start_city):
    def heuristic(path):
        # Estimate the remaining cost to visit all unvisited cities and return to the start
        unvisited = set(range(len(distance_matrix))) - set(path)
        if not unvisited:
            return distance_matrix[path[-1]][start_city]
        return min(distance_matrix[path[-1]][city] for city in unvisited)

    # Priority queue for open nodes
    open_list = []
    heapq.heappush(open_list, Node([start_city], 0, heuristic([start_city])))

    while open_list:
        # Expand the node with the lowest total cost (f)
        current_node = heapq.heappop(open_list)

        # If all cities are visited and returned to the start city, we're done
        if (
            len(current_node.path) == len(distance_matrix)
            and current_node.path[0] == start_city
        ):
            new_path = current_node.path + [start_city]
            new_g = (
                current_node.g
                + distance_matrix[current_node.path[len(current_node.path) - 1]][
                    start_city
                ]
            )
            current_node.path = new_path
            current_node.g = new_g
            return current_node.path, current_node.g

        # Expand to neighboring cities
        last_city = current_node.path[-1]
        for neighbor in range(len(distance_matrix)):
            if neighbor not in current_node.path or (
                len(current_node.path) == len(distance_matrix)
                and neighbor == start_city
            ):
                new_path = current_node.path + [neighbor]
                new_g = current_node.g + distance_matrix[last_city][neighbor]
                new_h = heuristic(new_path)
                heapq.heappush(open_list, Node(new_path, new_g, new_h))


# Cities Data Base
class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, default=0)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Task {self.id}"


with app.app_context():
    db.create_all()


@app.route("/", methods=["POST", "GET"])
def index():
    # Add City
    if request.method == "POST":
        current_city = request.form["city"]
        new_city = City(name=current_city)
        try:
            db.session.add(new_city)
            db.session.commit()
            return redirect("/")
        except Exception as e:
            print(f"ERROR:{e}")
            return f"ERROR:{e}"
    else:
        # display Cities
        cities = City.query.order_by(City.id).all()
        return render_template("index.html", cities=cities)


# Delete city
@app.route("/delete/<int:id>")
def delete(id: int):
    delete_city = City.query.get_or_404(id)
    try:
        db.session.delete(delete_city)
        db.session.commit()
        return redirect("/")
    except Exception as e:
        return f"ERROR:{e}"


@app.route("/distanceMatrix", methods=["POST", "GET"])
def distance_matrix_input():
    distanceMatrix = []
    current_matrix = []
    # inputting distance matrix from the user
    if request.method == "POST":
        cities = City.query.order_by(City.id).all()
        startCity = int(request.form["startCity"]) - 1
        try:
            for city in cities:
                for i in range(len(cities)):
                    current_matrix_value = int(request.form[city.name + str(i)])
                    current_matrix.append(current_matrix_value)
                distanceMatrix.append(current_matrix)
                current_matrix = []

            shortestPath, cost = a_star_algorithm(distanceMatrix, startCity)
            return render_template(
                "result.html",
                cities=cities,
                shortestPath=shortestPath,
                cost=cost,
            )
        except Exception as e:
            return f"ERROR:{e}"

    else:
        cities = City.query.order_by(City.id).all()
        return render_template("distance.html", cities=cities)


if __name__ == "__main__":

    app.run(debug=True)
