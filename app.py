from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "ecocycle-demo-key"
DB = "ecocycle.db"

def connect_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def create_tables():
    con = connect_db()
    con.execute("""CREATE TABLE IF NOT EXISTS food (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, quantity TEXT NOT NULL,
        location TEXT NOT NULL, expiry TEXT NOT NULL,
        status TEXT DEFAULT 'Available')""")
    con.execute("""CREATE TABLE IF NOT EXISTS compost (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        waste TEXT NOT NULL, quantity REAL NOT NULL,
        added_on TEXT NOT NULL, stage TEXT NOT NULL)""")
    con.commit()
    con.close()

@app.route("/")
def home():
    con = connect_db()
    available = con.execute("SELECT COUNT(*) FROM food WHERE status='Available'").fetchone()[0]
    entries = con.execute("SELECT COUNT(*) FROM compost").fetchone()[0]
    kg = con.execute("SELECT COALESCE(SUM(quantity),0) FROM compost").fetchone()[0]
    recent = con.execute("SELECT * FROM food ORDER BY id DESC LIMIT 5").fetchall()
    con.close()
    return render_template("index.html", available=available, entries=entries, kg=kg, recent=recent)

@app.route("/food")
def food():
    con = connect_db()
    items = con.execute("SELECT * FROM food ORDER BY id DESC").fetchall()
    con.close()
    return render_template("food.html", items=items)

@app.route("/food/add", methods=["GET", "POST"])
def add_food():
    if request.method == "POST":
        values = [request.form.get(x, "").strip() for x in ("name", "quantity", "location", "expiry")]
        if not all(values):
            flash("Please fill in all fields.")
            return redirect(url_for("add_food"))
        con = connect_db()
        con.execute("INSERT INTO food(name,quantity,location,expiry) VALUES(?,?,?,?)", values)
        con.commit()
        con.close()
        flash("Food listing added!")
        return redirect(url_for("food"))
    return render_template("food_add.html", today=date.today().isoformat())

@app.route("/food/collected/<int:item_id>", methods=["POST"])
def collected(item_id):
    con = connect_db()
    con.execute("UPDATE food SET status='Collected' WHERE id=?", (item_id,))
    con.commit()
    con.close()
    flash("Food marked as collected.")
    return redirect(url_for("food"))

@app.route("/compost", methods=["GET", "POST"])
def compost():
    if request.method == "POST":
        waste = request.form.get("waste", "").strip()
        quantity = request.form.get("quantity", "").strip()
        stage = request.form.get("stage", "").strip()
        try:
            amount = float(quantity)
            if amount <= 0: raise ValueError
        except ValueError:
            flash("Enter a quantity greater than zero.")
            return redirect(url_for("compost"))
        if not waste or not stage:
            flash("Please fill in all fields.")
            return redirect(url_for("compost"))
        con = connect_db()
        con.execute("INSERT INTO compost(waste,quantity,added_on,stage) VALUES(?,?,?,?)",
                    (waste, amount, date.today().isoformat(), stage))
        con.commit()
        con.close()
        flash("Compost record saved!")
        return redirect(url_for("compost"))
    con = connect_db()
    items = con.execute("SELECT * FROM compost ORDER BY id DESC").fetchall()
    con.close()
    return render_template("compost.html", items=items)

@app.route("/guide")
def guide():
    return render_template("guide.html")

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
