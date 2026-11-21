import os
import secrets
import string

from flask import Flask, redirect, render_template, request, session, url_for
from pymongo import MongoClient


mongo_client = MongoClient(os.getenv("MONGO_URI", "rahasia"))
database = mongo_client.contoh
admin_collection = database.admin
user_collection = database.users

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "rahasia")


def get_account_id():
    return session.get("akun")


def is_current_account(account_id):
    return account_id is not None and account_id == get_account_id()


@app.route("/", methods=["GET", "POST"])
def login():
    account_id = get_account_id()
    if account_id:
        endpoint = "admin" if "admin" in account_id else "user"
        return redirect(url_for(endpoint, id=account_id))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("sandi", "")

        admin = None
        if "admin" in email:
            admin = admin_collection.find_one({"email": email, "sandi": password})

        if admin is not None:
            session["akun"] = admin["_id"]
            return redirect(url_for("admin", id=admin["_id"]))

        user = user_collection.find_one({"email": email, "sandi": password})
        if user is not None:
            session["akun"] = user["_id"]
            return redirect(url_for("user", id=user["_id"]))

        return render_template(
            "login.html",
            pesan="Email atau kata sandi Anda salah.",
        )

    return render_template("login.html")


@app.route("/admin/<id>", methods=["GET", "POST"])
def admin(id):
    if not is_current_account(id):
        return redirect(url_for("login"))

    if request.method == "POST":
        user_collection.insert_one(
            {
                "_id": "".join(
                    secrets.choice(string.ascii_uppercase + string.digits)
                    for _ in range(8)
                ),
                "email": request.form.get("email", "").strip(),
                "sandi": request.form.get("sandi", ""),
                "username": request.form.get("usernm", "").strip(),
                "alamat": request.form.get("alamat", "").strip(),
            }
        )
        return redirect(url_for("admin", id=id))

    users_data = list(user_collection.find())
    return render_template("laman_admin.html", id=id, data=users_data)


@app.route("/user/<id>")
def user(id):
    if not is_current_account(id):
        return redirect(url_for("login"))

    data = user_collection.find_one({"_id": id})
    if data is None:
        session.pop("akun", None)
        return redirect(url_for("login"))

    return render_template("laman_user.html", data=data)


@app.route("/user/edit/<id>", methods=["GET", "POST"])
def user_edit_data(id):
    if not is_current_account(id):
        return redirect(url_for("login"))

    data = user_collection.find_one({"_id": id})
    if data is None:
        session.pop("akun", None)
        return redirect(url_for("login"))

    if request.method == "POST":
        user_collection.update_one(
            {"_id": id},
            {
                "$set": {
                    "email": request.form.get("email", "").strip(),
                    "sandi": request.form.get("sandi", ""),
                    "username": request.form.get("usernm", "").strip(),
                    "alamat": request.form.get("alamat", "").strip(),
                }
            },
        )
        return redirect(url_for("user", id=id))

    return render_template("edit_data_user.html", data=data)


@app.route("/user/hapus/<id>")
def user_hapus_akun(id):
    if not is_current_account(id):
        return redirect(url_for("login"))

    user_collection.delete_one({"_id": id})
    session.pop("akun", None)
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("akun", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
