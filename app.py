from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, make_response, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Substitua pela sua própria chave secreta

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'instance', 'carousel.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de dados para imagens do carrossel
class CarouselImage(db.Model):
    __tablename__ = 'CarouselImage'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))

# Formulário de upload de imagens
class ImageUploadForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired()])
    description = TextAreaField('Descrição', validators=[DataRequired()])
    photo = FileField('Escolha uma imagem', validators=[DataRequired()])

# Rota para exibir o carrossel no frontend
@app.route('/')
def carousel():
    user_role = session.get('user_role')

    if user_role == 'admin':
        images = db.session.query(CarouselImage).all()
        return render_template('carousel.html', images=images)
    elif user_role == 'public':
        images = db.session.query(CarouselImage).all()
        return render_template('public_carousel.html', images=images)
    else:
        return redirect(url_for('login_form'))

@app.route('/login', methods=['GET', 'POST'])
def login_form():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'senha_admin':
            session['user_role'] = 'admin'
            return redirect(url_for('carousel')) 
        elif username == 'public' and password == 'senha_public':
            session['user_role'] = 'public'
            return redirect(url_for('carousel'))  
        else:
            flash('Credenciais inválidas', 'danger')

    return render_template('login.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

# Rota para fazer o upload de imagens
@app.route('/upload', methods=['POST'])
def upload_image():
    form = ImageUploadForm()
    
    photo = form.photo.data
    filename = secure_filename(photo.filename)
    photo.save('uploads/' + filename)

    new_image = CarouselImage(
        title=form.title.data,
        description=form.description.data,
        image_url='uploads/' + filename
    )
    db.session.add(new_image)
    db.session.commit()
    flash('Imagem enviada com sucesso', 'success')
    return redirect(url_for('carousel'))

@app.route('/logout')
def logout():
    session.pop('user_role', None)
    return redirect(url_for('login_form'))


@app.route('/delete/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    # Verifique se o usuário está autenticado 
    user_role = session.get('user_role')

    if user_role != 'admin':
        return "Acesso negado"

    image = CarouselImage.query.get(image_id)

    if image:
        # Exclua a imagem do banco de dados
        db.session.delete(image)
        db.session.commit()
    # Redirecione de volta para a página do carrossel
    return redirect(url_for('carousel'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
