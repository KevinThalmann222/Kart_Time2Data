from flask import Flask, render_template, request, flash, url_for, redirect, session
import Karttime2Data 

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

USER = 'kevin'
PW = '123'

@app.route("/",  methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        
        user = request.form["user"]
        password = request.form['pw']

        print('-'*50)
        print(f'Login with: {user}')
        print(f'Login with: {password}')
        print('-'*50)

        if password == PW and user == USER:
            session['user'] = user
            return redirect(url_for("getdata"))
        else:
            return render_template("home.html", INFO="falscher Username oder falsches Password")
 
    return render_template("home.html")

@app.route("/getdata",  methods=['GET', 'POST'])
def getdata():
    if "user" in session:
        if request.method == 'POST':

            flash('Deine Ergegbnisse wurden unter "D:\\Bilder" exportiert')
            pic_name = request.files['name_input'].filename
            kart_pic_path = f'D:\\Bilder\\{pic_name}'
            kartzeiten = Karttime2Data.Kartzeiten(kart_pic_path)
            kartzeiten.kart_change_analyse()
            all_laps = kartzeiten.show_laps()
            kartzeiten.export2csv()
            return render_template("index.html", show_kart_laps=all_laps)

        else:
            flash('Wähle ein Bild deiner Rundenzeiten vom Pfad D:\\Bilder')
            return render_template("index.html")
    else:
        return render_template("home.html")

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
