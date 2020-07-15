from flask import Flask
from flask_mysqldb import MySQL
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, send_file, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from tempfile import NamedTemporaryFile
from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator
import os
from InvoiceGenerator.pdf import SimpleInvoice
from datetime import date, timedelta
import random
#from flask_login import *

# Coneeccion mysql
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Morfologia123'
app.config['MYSQL_DB'] = 'tintoreria'
mysql = MySQL(app)

# SESSION
app.secret_key = 'mysecretkey11'
ti = ""
adminkey = 'specialkey'
# Componentes para interactuar con la base de datos

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    if request.method == 'POST':
        session.pop('username', None)
        return redirect(url_for('login'))

    return render_template('index2.html')


@app.route('/adminprofile', methods=['GET', 'POST'])
def adminprofile():
    if request.method == 'POST':
        session.pop('username', None)
        return redirect(url_for('index2'))
    return render_template('adminprofile.html')


@app.route('/verclientes', methods=['GET', 'POST'])
def verclientes():
    if request.method == 'POST':
        session.pop('username', None)
        return redirect(url_for('index2'))
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM cliente')
    cliente = cur.fetchall()
    
    return render_template('verclientes.html', cliente = cliente )


@app.route('/adminsignup', methods=['GET', 'POST'])
def adminsignup():
    error = ""
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        username = request.form["username"]
        special_key = request.form["specialkey"]
        nombre =request.form["nombre"]
        cedula = request.form["cedula"]
        cargo =request.form["cargo"]
        
        users = cur.execute('SELECT username FROM administrador WHERE username = "'+ username + '"')
        if users >= 1:
            error = '¡Nombre de usuario no disponible!'
            return render_template('adminsignup.html', error = error)

        if special_key == adminkey:
            password = request.form["password"]
            #MySQL request
            cur.execute('INSERT INTO administrador (nombre_completo, cedula, cargo, username, password) VALUES (%s, %s, %s, %s, %s)', (nombre, cedula, cargo, username, password))
            mysql.connection.commit()
            flash('¡Usuario agregado exitosamente!')
            return render_template('adminsignup.html', error = error)
        error ='Hubo un error insertando los datos'
    return render_template('adminsignup.html', error = error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM empleado WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            if account['state'] == 1:
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                return redirect(url_for('index2'))

            else:
                flash('Usuario bloqueado')
                return render_template('login.html')

        flash('Error al introducir los datos')
    return render_template('login.html')


@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():

    if request.method == 'POST':
        session.pop('user_id', None)
        username = request.form['username']
        password = request.form['password']
        special_key = request.form['special_key']
        # Check if account exists using MySQL
        if special_key == adminkey:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'SELECT * FROM administrador WHERE username = %s AND password = %s', (username, password))
            # Fetch one record and return result
            account = cursor.fetchone()
            # If account exists in accounts table in out database
            if account:
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                return redirect(url_for('adminprofile'))
            else:
                flash('Error al introducir los datos')
        else:
            flash('Error al introducir los datos')
        return redirect(url_for('adminlogin'))
    return render_template('adminlogin.html')


@app.route('/index2', methods=['GET', 'POST'])
def index2():

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos')
    productos = cur.fetchall()
    cur.execute('SELECT producto, precio, cantidad FROM items WHERE state = 1')
    items = cur.fetchall()

    iva = 0
    totaliva = 0
    cont = 0

    for x in items:
            cont = cont + ( float(x[1]) * float(x[2]) )
            iva = cont * 0.12
            totaliva = iva + cont

    return render_template('index2.html', productos = productos, items = items, iva = iva, totaliva = totaliva, neto = cont )


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = ""
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        username = request.form["username"]
        users = cur.execute('SELECT username FROM empleado WHERE username = "'+ username + '"')
        if users >= 1:
            error = '¡Nombre de usuario no disponible!'
        else:
            password = request.form["password"]
            fullname = request.form["fullname"]
            cedula = request.form["cedula"]
            phone = request.form["phone"]
            address = request.form["address"]
            dateofbirth = request.form["dateofbirth"]
            #MySQL request
            cur.execute("""INSERT INTO empleado (nombre_completo, direccion, telefono, cedula, username, fechadenacimiento, password, state) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)""", (fullname, address, phone, cedula, username, dateofbirth, password))
            mysql.connection.commit()
            flash('¡Usuario agregado exitosamente!')
    return render_template('signup.html', error = error)

#Show instruments

@app.route('/showinstruments/<string:tipo>/', methods=['GET', 'POST'])
def show(tipo):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM {0} WHERE state = 1' .format(tipo))
    data = cur.fetchall()
    global ti
    ti = tipo
    return render_template('profile.html', electric_guitar = data)


@app.route('/showinstruments2/<string:tipo>/', methods=['GET', 'POST'])
def show2(tipo):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM {0} WHERE state = 1' .format(tipo))
    data = cur.fetchall()
    global ti
    ti = tipo
    return render_template('index2.html', electric_guitar = data)

#Admin
@app.route('/showinstrumentst/<string:tipo>/', methods=['GET', 'POST'])
def show3(tipo):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM {0} ' .format(tipo))
    data = cur.fetchall()
    global ti
    ti = tipo
    return render_template('adminprofile.html', electric_guitar = data)    

#CAR COMPONENTS

@app.route('/addtocar/<name>', methods=['GET', 'POST'])
def addtocar(name):
    
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cantidad = request.form["quantity"]
        cur.execute("SELECT precio FROM productos WHERE producto = " + "'" + name + "'")
        precio = cur.fetchall()
        #insert into car
        cur.execute('''INSERT INTO items (producto, precio, cantidad, state) 
                VALUES(%s, %s, %s, 1 )''', (name, precio, cantidad ) )
        mysql.connection.commit()  
        cur.execute('SELECT producto, precio, cantidad FROM items WHERE state = 1')
        items = cur.fetchall()

        cont = 0
        for x in items:
            cont = cont + (float(x[1]) * float(x[2]))
            iva = cont * 0.12
            totaliva = iva + cont

        

        return render_template('index2.html', items = items, iva = iva, totaliva = totaliva, neto = cont )


@app.route('/delete/<name>', methods=['GET', 'POST'])
def delete(name):

    cur = mysql.connection.cursor()
    cur.execute("UPDATE items SET state = 0 WHERE producto = " + "'" + name + "'" )
    mysql.connection.commit()
    cur.execute('SELECT producto, precio, cantidad FROM items WHERE state = 1')
    items = cur.fetchall()
    return render_template('index2.html', items = items )


@app.route('/delete2/', methods=['GET', 'POST'])
def delete2():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM items")
    cur.execute('SELECT producto, precio, cantidad FROM items WHERE state = 1')
    items = cur.fetchall()
    mysql.connection.commit()
    return render_template('index2.html', items = items )    



@app.route('/checkout', methods=['GET', 'POST'])
def checkout(): 

    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute('SELECT producto, precio, cantidad FROM items WHERE state = 1')
        items = cur.fetchall()
        cur.execute('SELECT nombre_completo FROM cliente')
        nombreu = cur.fetchall()


        cont = 0
        for x in items:
            cont = cont + (float(x[1]) * float(x[2]))
            iva = cont * 0.12
            totaliva = iva + cont

        #date now
        today = date.today()
        # dd/mm/YY
        currentdate = today.strftime("%d/%m/%Y")
        today2 = today + timedelta(days=30)
        duedate = today2.strftime("%d/%m/%Y")
        hash = random.getrandbits(16)


        nombre = request.form["fullname"]
        cedula = request.form["cedula"]
        direccion = request.form["address"]
        telefono = request.form["telefono"]

        flag = False
        for i in nombreu:
            if i[0] == nombre:
                flag = True

        if flag == False:
            cur.execute("""INSERT INTO cliente (nombre_completo, cedula, direccion, telefono)
            VALUES (%s, %s, %s, %s) """, (nombre, cedula, direccion, telefono) ) 
            mysql.connection.commit()

        cur.execute("""INSERT INTO facturas (fecha_expedicion, fecha_vencimiento, monto, hash, nombre_cliente, cedula_cliente, devolution)
        VALUES (%s, %s, %s, %s, %s, %s, 0) """, (currentdate, duedate, totaliva, hash, nombre, cedula) )
        mysql.connection.commit()

        cur.execute("DELETE FROM items" )
        mysql.connection.commit()
    return render_template('invoice.html', total = cont, iva = iva, totaliva = totaliva, currentdate = currentdate, duedate = duedate, hash = hash, nombre = nombre, cedula = cedula, dir = direccion, telefono = telefono, items = items)


#Gestion de empleados
@app.route('/gestionar', methods=['GET', 'POST'])
def gestionar(): 

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM empleado ')
    empleado = cur.fetchall()
    return render_template("gestionar.html", empleado = empleado)


@app.route('/deleteuser/<id>', methods=['GET', 'POST'])
def deleteuser(id):


    cur = mysql.connection.cursor()
    cur.execute('UPDATE empleado SET state = 0 WHERE id = '+ id )
    mysql.connection.commit()
    return redirect(url_for('gestionar'))


@app.route('/recoveruser/<id>', methods=['GET', 'POST'])
def recoveruser(id):

    cur = mysql.connection.cursor()
    #consulting userlog
    cur.execute('UPDATE empleado SET state = 1 WHERE id = ' + id)
    mysql.connection.commit()
    return redirect(url_for('gestionar'))



@app.route('/vistaeditar', methods=['GET', 'POST'])
def vistaeditar():

    return render_template('vistaeditar.html')


@app.route('/edit/<name>', methods=['GET', 'POST'])
def edit(name):

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos WHERE producto = ' + "'" + name + "'" )
    producto = cur.fetchall()
    mysql.connection.commit()
    flash("¡Producto editado exitosamente!")
    return render_template('edit.html', producto = producto, name = name)



@app.route('/update/<name>', methods=['GET', 'POST'])
def update(name):
    if request.method == 'POST':

        precio = request.form['precio']
        hash = request.form['hash']

        cur = mysql.connection.cursor()
        cur.execute('UPDATE productos SET precio = ' + "'" + str(precio) + "'"  + ', hash = ' + "'" + str(hash) + "'"  + ' WHERE producto = ' + "'" + name + "'" )
        mysql.connection.commit()
    return render_template('vistaeditar.html')


@app.route('/facturas', methods=['GET', 'POST'])
def facturas():

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM facturas')
    facturas = cur.fetchall()

    return render_template('facturas.html', f = facturas)



@app.route('/devolution/<hash>', methods=['GET', 'POST'])
def devolution(hash):

    cur = mysql.connection.cursor()
    cur.execute('UPDATE facturas SET devolution = 1 WHERE hash = '+ hash )
    mysql.connection.commit()

    cur.execute('SELECT * FROM facturas')
    facturas = cur.fetchall()

    return render_template('facturas.html', f = facturas )


"""
 if request.method == 'POST':
     ur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos WHERE producto = ' + name)
    producto = cur.fetchall()
    mysql.connection.commit()
    return render_template('vistaeditar.html', producto = producto)
        photo = request.form['photo']
        model = request.form['model']
        brand = request.form['brand']
        price = request.form['price']
        stock = request.form['stock']
        cur = mysql.connection.cursor()

        cur.execute('UPDATE '+ ti + ' SET photo = "'+ photo + '"' + ', model = "' + model + '"' + ', brand = "' + brand + '"' + ', price = "' + str(price) + '"' + ', stock = "' + str(stock) + '"' + ' WHERE id = 1')
        flash('Producto editado satisfactoriamente!!')
        mysql.connection.commit()

"""
if __name__ == '__main__':
    app.run(port=3000, debug=True)








"""


@app.route('/car', methods=['GET', 'POST'])
def car():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM car WHERE userid = ' + str(session['id']) + ' AND state = 1')
    data = cur.fetchall()
    cur.execute('SELECT * FROM user_info WHERE id = ' + str(session['id']))
    user = cur.fetchall()
    cont = 0.0
    for x in data:
        cont = cont + (float(x[3]) * float(x[11]))
    iva = cont * 0.12
    totaliva = iva + cont

    cur.execute('SELECT * FROM invoices WHERE iduser = ' + str(session['id']))
    invoices = cur.fetchall()


    return render_template('car.html', car = data, total = cont, iva = iva, totaliva = totaliva, invoices = invoices)

@app.route('/admincar', methods=['GET', 'POST'])
def admincar():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM car Where state = 1')
    data = cur.fetchall()
    cont = 0.0
    for x in data:
        cont = cont + (float(x[3]) * float(x[11]))
    iva = cont * 0.12
    totaliva = iva + cont

    cur.execute('SELECT * FROM invoices WHERE devolution = 1')
    invoices = cur.fetchall()

    return render_template('admincar.html', car = data, total = cont, iva = iva, totaliva = totaliva, invoices = invoices)

@app.route('/admincardelete/<id>', methods=['GET', 'POST'])
def admincardelete(id):
    cur = mysql.connection.cursor()
    #extract product
    #extract the product from products table
    cur.execute('SELECT quantity FROM car WHERE id = ' + str(id))
    stockproduct = cur.fetchall()

    #extract the product from the car
    cur.execute('SELECT stock FROM car WHERE id = ' + str(id))
    stockcar = cur.fetchall()
    #update stock product
    newstock = int(stockproduct[0][0]) + int(stockcar[0][0])

    # extracting product car id
    cur.execute('SELECT idproduct FROM car WHERE id = ' + str(id))
    pid = cur.fetchall()
    idproduct = pid[0][0]

    cur.execute('SELECT model FROM car WHERE id = ' + str(id))
    model = cur.fetchall()

    cur.execute('SELECT userid FROM car WHERE id = ' + str(id))
    userid = cur.fetchall()

    cur.execute('SELECT tabla FROM car WHERE id = ' + str(id))
    tabla = cur.fetchall()

    cur.execute('UPDATE ' + tabla[0][0] + ' SET stock = ' + str(newstock) + ' WHERE id = ' + str(idproduct))
    mysql.connection.commit()

    #¡¡!!!
    cur.execute('UPDATE car SET state = 0 WHERE userid = %s and id = %s', (userid[0][0], id))
    mysql.connection.commit()

    cur.execute('UPDATE car SET stock = ' + str(newstock) +' WHERE userid = %s and id = %s', (str(userid[0][0]), str(id)))
    mysql.connection.commit()

    return redirect(url_for('admincar'))

@app.route('/adminrecovercar/<id>', methods=['GET', 'POST'])
def adminrecovercar(id):

    cur = mysql.connection.cursor()
    #extract product
    #extract the product from products table
    cur.execute('SELECT quantity FROM car WHERE id = ' + str(id))
    stockproduct = cur.fetchall()

    #extract the product from the car
    cur.execute('SELECT stock FROM car WHERE id = ' + str(id))
    stockcar = cur.fetchall()
    #update stock product
    newstock = int(stockcar[0][0]) - int(stockproduct[0][0])

    # extracting product car id
    cur.execute('SELECT idproduct FROM car WHERE id = ' + str(id))
    pid = cur.fetchall()
    idproduct = pid[0][0]

    cur.execute('SELECT model FROM car WHERE id = ' + str(id))
    model = cur.fetchall()

    cur.execute('SELECT userid FROM car WHERE id = ' + str(id))
    userid = cur.fetchall()

    cur.execute('SELECT tabla FROM car WHERE id = ' + str(id))
    tabla = cur.fetchall()

    cur.execute('UPDATE ' + tabla[0][0] + ' SET stock = ' + str(newstock) + ' WHERE id = ' + str(idproduct))
    mysql.connection.commit()

    cur.execute('UPDATE car SET stock = ' + str(newstock) + ' WHERE id = ' + id)
    mysql.connection.commit()
    #¡¡!!!
    cur.execute('UPDATE car SET state = 1 WHERE userid = %s and id = %s', (userid[0][0], id))
    mysql.connection.commit()
    return redirect(url_for('admincar'))


"""











"""


#ADMIN ACTIONS
@app.route('/admindelete/<id>')
def admindelete(id):
    cur = mysql.connection.cursor()
    #Delete instrument by logical elimination
    
    cur.execute('SELECT idproduct FROM car WHERE id = ' + str(id))
    pid = cur.fetchall()
        

    cur.execute('UPDATE ' + ti + ' SET state = 0 WHERE id = ' + str(id))
    mysql.connection.commit()

    # Refresh the car
    # Product consult inside car.html
    
    cur.execute('SELECT hash FROM ' + ti + ' WHERE id = ' + str(id))
    hash = cur.fetchall()
    #Update de db with logical elimination
    cur.execute('UPDATE car SET state = 0 WHERE hash = ' + str(hash[0][0]) )
    mysql.connection.commit()

    flash('Elemento eliminado con exito')

    return redirect(url_for('adminprofile'))


@app.route('/adminrecover/<id>')
def adminrecover(id):
    cur = mysql.connection.cursor()
    cur.execute('UPDATE ' + ti + ' SET state = 1 WHERE id = ' + str(id))
    mysql.connection.commit()

    #consulting hash
    cur.execute('SELECT hash FROM ' + ti + ' WHERE id = ' + str(id))
    hash = cur.fetchall()
    #Update de db with logical elimination
    cur.execute('UPDATE car SET state = 1 WHERE hash = ' + str(hash[0][0]) )
    mysql.connection.commit()


    flash('Elemento recuperado con exito con exito')
    return redirect(url_for('adminprofile'))


@app.route('/editproduct/<id>', methods=['GET', 'POST'])
def editproduct(id):
   
    cur = mysql.connection.cursor()
    cur.execute('SELECT photo, model, brand, price, stock FROM ' + ti + ' WHERE id = ' + str(id))
    data = cur.fetchall()

    return render_template('editproduct.html', data = data, id = id)

@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):

    if request.method == 'POST':
        photo = request.form['photo']
        model = request.form['model']
        brand = request.form['brand']
        price = request.form['price']
        stock = request.form['stock']
        cur = mysql.connection.cursor()

        cur.execute('UPDATE '+ ti + ' SET photo = "'+ photo + '"' + ', model = "' + model + '"' + ', brand = "' + brand + '"' + ', price = "' + str(price) + '"' + ', stock = "' + str(stock) + '"' + ' WHERE id = 1')
        flash('Producto editado satisfactoriamente!!')
        mysql.connection.commit()
        return redirect(url_for('adminprofile'))


# Users Operations 
@app.route('/adminusers', methods=['GET', 'POST'])
def adminusers():

    cur = mysql.connection.cursor()
    #consulting userlog
    cur.execute('SELECT * FROM userlog ')
    userlog = cur.fetchall()
    cur.execute('SELECT user_info_firstname, user_info_secondname, email, user_info_phone, user_info_country, user_info_adress, state, id FROM user_info')
    userinfo = cur.fetchall()

    return render_template('adminusers.html', userlog = userlog, userinfo = userinfo)


@app.route('/deleteuser/<id>', methods=['GET', 'POST'])
def deleteuser(id):

    print('')
    print('')
    print(type(id))
    print('')
    print('')
    cur = mysql.connection.cursor()
    cur.execute('UPDATE userlog SET state = 0 WHERE iduserlog = '+ id )
    mysql.connection.commit()
    cur.execute('UPDATE user_info SET state = 0 WHERE id = ' + id )
    mysql.connection.commit()
    return redirect(url_for('adminusers'))


@app.route('/recoveruser/<id>', methods=['GET', 'POST'])
def recoveruser(id):

    cur = mysql.connection.cursor()
    #consulting userlog
    cur.execute('UPDATE userlog SET state = 1 WHERE iduserlog = ' + id)
    mysql.connection.commit()
    cur.execute('UPDATE user_info SET state = 1 WHERE id = ' + id )
    mysql.connection.commit()
    return redirect(url_for('adminusers'))


@app.route('/profilesearch', methods=['GET', 'POST'])
def profilesearch():

    if request.method == "POST":

        search = request.form["search"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM instruments WHERE model LIKE '%" + search + "%'" + " OR brand LIKE '%" + search + "%'" )
        data = cur.fetchall()
        return render_template('profile.html', electric_guitar = data)

@app.route('/profilesearch2', methods=['GET', 'POST'])
def profilesearch2():
    if request.method == "POST":

        search = request.form["search"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM instruments WHERE model LIKE '%" + search + "%'" + " OR brand LIKE '%" + search + "%'" )
        data = cur.fetchall()
        return render_template('adminprofile.html', electric_guitar = data)

@app.route('/carsearch', methods=['GET', 'POST'])
def carsearch():
    if request.method == "POST":

        search = request.form["search"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM car WHERE model LIKE '%" + search + "%'" + " OR brand LIKE '%" + search + "%'" + " OR state LIKE '%" + search + "%'" + " OR userid LIKE '%" + search + "%'" )
        data = cur.fetchall()
        return render_template('admincar.html', car = data)

@app.route('/usersearch', methods=['GET', 'POST'])
def usersearch():
    if request.method == "POST":

        search = request.form["search"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_info_firstname, user_info_secondname, email, user_info_phone, user_info_country, user_info_adress, state, id  FROM user_info WHERE user_info_firstname LIKE '%" + search + "%'" + " OR user_info_secondname LIKE '%" + search + "%'" + " OR user_info_country LIKE '%" + search + "%'" + " OR user_info_country LIKE '%" + search + "%'" )
        data = cur.fetchall()
        return render_template('adminusers.html', userinfo = data)

@app.route('/devolution/<id>', methods=['GET', 'POST'])
def devolution(id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE invoices SET devolution = 1 WHERE id = " + id )
    mysql.connection.commit()
    return redirect(url_for("car"))


@app.route('/aprov/<id>', methods=['GET', 'POST'])
def aprov(id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE invoices SET devolution = 1, state = 0 WHERE id = " + id )
    mysql.connection.commit()
    return redirect(url_for("inv"))


@app.route('/inv', methods=['GET', 'POST'])
def inv():
    cur = mysql.connection.cursor()

    cur.execute('SELECT * FROM invoices WHERE devolution = 0')
    inv = cur.fetchall()

    cur.execute('SELECT * FROM invoices WHERE devolution = 1')
    invoices = cur.fetchall()

    return render_template('inv.html', invoices = invoices, inv = inv)


@app.route('/invsearch', methods=['GET', 'POST'])
def invsearch():
    if request.method == "POST":
        search = request.form["search"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM invoices WHERE hash LIKE '%" + search + "%'" + " OR fistname LIKE '%" + search + "%'" + " OR lastname LIKE '%" + search + "%'" + " OR expedate LIKE '%" + search + "%'"+ " OR duedate LIKE '%" + search + "%'" )
        data = cur.fetchall()

        cur.execute('SELECT * FROM invoices WHERE devolution = 1')
        invoices = cur.fetchall()
        return render_template('inv.html', inv = data, invoices = invoices)


@app.route('/add', methods=['GET', 'POST'])
def add():
#Final del programa



"""
